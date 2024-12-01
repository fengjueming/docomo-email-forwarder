import imaplib
import email
import smtplib
import time
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import threading
import os

class EmailForwarder:
    def __init__(self, 
                 source_imap_server, source_imap_port, source_email, source_password,
                 dest_imap_server, dest_imap_port, dest_email, dest_password):
        # Source server IMAP settings
        self.imap_server = source_imap_server
        self.imap_port = source_imap_port
        self.imap_email = source_email
        self.imap_password = source_password
        
        # Destination server IMAP settings
        self.smtp_server = dest_imap_server  # Keep variable name but actually IMAP server
        self.smtp_port = dest_imap_port      # Actually IMAP port
        self.smtp_email = dest_email
        self.smtp_password = dest_password
        
        self.forward_to_email = dest_email   # Can be removed as no longer needed
        self.imap = None
        self.running = False
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.options &= ~ssl.OP_NO_RENEGOTIATION
        self.ssl_context.options &= ~ssl.OP_NO_TLSv1
        self.ssl_context.options &= ~ssl.OP_NO_TLSv1_1

    def connect_imap(self):
        """Establish IMAP connection"""
        try:
            if self.imap:
                try:
                    self.imap.close()
                    self.imap.logout()
                except:
                    pass
            
            self.imap = imaplib.IMAP4_SSL(self.imap_server, self.imap_port, ssl_context=self.ssl_context)
            self.imap.login(self.imap_email, self.imap_password)  # Use IMAP authentication information
            self.imap.select('INBOX')
            print("Successfully connected to IMAP server")
        except Exception as e:
            print(f"Error connecting to IMAP server: {e}")
            raise

    def forward_email(self, email_id):
        """Copy email via IMAP"""
        try:
            # Get original email data
            _, msg_data = self.imap.fetch(email_id, '(RFC822)')
            if not msg_data[0]:
                print(f"Could not fetch email {email_id}")
                return False
            
            email_body = msg_data[0][1]
            
            # Connect to the destination IMAP server
            with imaplib.IMAP4_SSL(self.smtp_server, self.imap_port, ssl_context=self.ssl_context) as dest_imap:
                # Use the destination account to log in
                dest_imap.login(self.smtp_email, self.smtp_password)
                
                # Select the inbox
                dest_imap.select('INBOX')
                
                # Add the email to the destination mailbox
                dest_imap.append('INBOX', None, imaplib.Time2Internaldate(time.time()), email_body)
                
                original_email = email.message_from_bytes(email_body)
                print(f"Successfully copied email from {original_email['From']}")
                return True
                
        except Exception as e:
            print(f"Error copying email: {e}")
            import traceback
            print(f"Detailed error: {traceback.format_exc()}")
            return False

    def process_existing_emails(self):
        """Process existing unread emails"""
        try:
            # Search for all unread emails
            typ, msgs = self.imap.search(None, 'UNSEEN')
            if typ != 'OK':
                print("Search for unread emails failed")
                return
            
            # Get all unread email IDs
            email_ids = msgs[0].split()
            if not email_ids:
                print("No unread emails")
                return
            
            print(f"Found {len(email_ids)} unread emails")
            
            # Process each email
            for email_id in email_ids:
                try:
                    # Try forwarding the email
                    self.forward_email(email_id)
                    
                    # If forwarding is successful, mark the email as deleted
                    self.imap.store(email_id, '+FLAGS', '\\Deleted')
                    print(f"Email {email_id} marked as deleted")
                    
                except Exception as e:
                    print(f"Error processing email {email_id}: {e}")
                    continue  # Skip this email and continue processing the next one
            
            # Perform the actual deletion operation
            self.imap.expunge()
            print("Deleted all successfully forwarded emails")
            
        except Exception as e:
            print(f"Error processing existing emails: {e}")

    def idle_loop(self):
        """IMAP IDLE loop"""
        while self.running:
            try:
                # Send IDLE command
                tag = self.imap._new_tag().decode('ascii')
                self.imap.send(f"{tag} IDLE\r\n".encode('ascii'))
                
                # Wait for the server to be ready for response
                response = self.imap.readline().decode('ascii')
                if not response.startswith('+ '):
                    print(f"IDLE command failed: {response}")
                    time.sleep(5)  # Add delay and retry
                    continue
                
                print("Enter IDLE mode, waiting for new emails...")
                
                while self.running:
                    try:
                        self.imap.socket().settimeout(60 * 29)
                        line = self.imap.readline().decode('ascii')
                        
                        if not line:  # Connection closed
                            raise ConnectionError("Connection closed")
                            
                        if 'EXISTS' in line or 'RECENT' in line:
                            # Properly handle DONE command
                            try:
                                self.imap.send(b'DONE\r\n')
                                # Wait for all responses
                                while True:
                                    resp = self.imap.readline().decode('ascii')
                                    if resp.startswith(tag):
                                        break
                                
                                # Process new emails received
                                self.process_existing_emails()
                                
                            except Exception as e:
                                print(f"Error handling DONE command: {e}")
                                raise
                                
                            break  # Exit inner loop and re-enter IDLE mode
                            
                    except (imaplib.IMAP4.abort, TimeoutError, ConnectionError) as e:
                        print(f"Connection interrupted: {e}")
                        self.connect_imap()  # Reconnect
                        break
                        
            except Exception as e:
                print(f"Main loop error: {e}")
                time.sleep(5)
                try:
                    self.connect_imap()
                except:
                    continue

    def start(self):
        """Start email forwarding service"""
        try:
            self.connect_imap()
            self.running = True
            
            # First, process existing unread emails
            self.process_existing_emails()
            
            # Then start IDLE loop to wait for new emails
            print("Email forwarding service started...")
            self.idle_loop()
            
        except Exception as e:
            print(f"Service startup error: {e}")
            self.running = False
            raise

    def stop(self):
        """Stop service"""
        self.running = False
        if self.imap:
            try:
                self.imap.close()
                self.imap.logout()
            except:
                pass
        print("Email forwarding service stopped")

# Usage example
if __name__ == "__main__":
    # Source server config (spmode)
    SOURCE_IMAP_SERVER = os.getenv('SOURCE_IMAP_SERVER', 'imap.spmode.ne.jp')
    SOURCE_IMAP_PORT = int(os.getenv('SOURCE_IMAP_PORT', 993))
    SOURCE_EMAIL = os.getenv('SOURCE_EMAIL')
    SOURCE_PASSWORD = os.getenv('SOURCE_PASSWORD')
    
    # Destination server config (Gmail)
    DEST_IMAP_SERVER = os.getenv('DEST_IMAP_SERVER', 'imap.gmail.com')
    DEST_IMAP_PORT = int(os.getenv('DEST_IMAP_PORT', 993))
    DEST_EMAIL = os.getenv('DEST_EMAIL')
    DEST_PASSWORD = os.getenv('DEST_PASSWORD')  # Gmail requires app-specific password
    
    # Validate required environment variables
    required_vars = [
        'SOURCE_EMAIL', 'SOURCE_PASSWORD',
        'DEST_EMAIL', 'DEST_PASSWORD'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        exit(1)
    
    forwarder = EmailForwarder(
        SOURCE_IMAP_SERVER, SOURCE_IMAP_PORT, SOURCE_EMAIL, SOURCE_PASSWORD,
        DEST_IMAP_SERVER, DEST_IMAP_PORT, DEST_EMAIL, DEST_PASSWORD
    )
    
    try:
        forwarder.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping service...")
        forwarder.stop()