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
from functools import wraps
import random

def retry_on_failure(max_attempts=3, initial_delay=1, max_delay=60, exponential_base=2):
    """
    Retry decorator
    max_attempts: Maximum number of retry attempts
    initial_delay: Initial delay time (seconds)
    max_delay: Maximum delay time (seconds)
    exponential_base: Base for exponential backoff
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            delay = initial_delay
            
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    if attempt == max_attempts:
                        print(f"Maximum retry attempts ({max_attempts}) reached, operation failed")
                        raise e
                    
                    # Calculate delay for next retry (exponential backoff + random jitter)
                    delay = min(delay * exponential_base + random.uniform(0, 1), max_delay)
                    print(f"Operation failed (attempt {attempt}/{max_attempts}): {str(e)}")
                    print(f"Retrying in {delay:.2f} seconds...")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

class EmailForwarder:
    def __init__(self, 
                 source_imap_server, source_imap_port, source_email, source_password,
                 dest_imap_server, dest_imap_port, dest_email, dest_password):
        # Source IMAP server settings
        self.imap_server = source_imap_server
        self.imap_port = source_imap_port
        self.imap_email = source_email
        self.imap_password = source_password
        
        # Destination IMAP server settings
        self.smtp_server = dest_imap_server  # Keep the variable name, but it's actually an IMAP server
        self.smtp_port = dest_imap_port      # It's actually an IMAP port
        self.smtp_email = dest_email
        self.smtp_password = dest_password
        
        self.forward_to_email = dest_email   # This variable can be removed, as it's no longer needed
        self.imap = None
        self.running = False
        self.ssl_context = ssl.create_default_context()

    @retry_on_failure(max_attempts=3)
    def connect_source_imap(self):
        """Connect to source IMAP server"""
        self.imap = imaplib.IMAP4_SSL(self.imap_server, self.imap_port, ssl_context=self.ssl_context)
        self.imap.login(self.imap_email, self.imap_password)
        return True

    @retry_on_failure(max_attempts=3)
    def connect_dest_imap(self):
        """Connect to destination IMAP server"""
        dest_imap = imaplib.IMAP4_SSL(self.smtp_server, self.smtp_port, ssl_context=self.ssl_context)
        dest_imap.login(self.smtp_email, self.smtp_password)
        return dest_imap

    @retry_on_failure(max_attempts=3)
    def forward_email(self, email_id):
        """Copy email via IMAP (with retry mechanism)"""
        try:
            # Get original email data
            _, msg_data = self.imap.fetch(email_id, '(RFC822)')
            if not msg_data[0]:
                print(f"Unable to fetch email {email_id}")
                return False
            
            email_body = msg_data[0][1]
            
            # Connect to destination IMAP server
            with self.connect_dest_imap() as dest_imap:
                # Select inbox
                dest_imap.select('INBOX')
                
                # Add email to destination mailbox
                dest_imap.append('INBOX', None, imaplib.Time2Internaldate(time.time()), email_body)
                
                original_email = email.message_from_bytes(email_body)
                print(f"Successfully copied email from {original_email['From']}")
                return True
                
        except Exception as e:
            print(f"Error copying email: {e}")
            import traceback
            print(f"Detailed error: {traceback.format_exc()}")
            raise  # Re-raise the exception to trigger the retry mechanism

    def start(self):
        """Start email forwarding service"""
        self.running = True
        try:
            while self.running:
                try:
                    # Ensure IMAP connection is active
                    try:
                        self.imap.noop()
                    except:
                        print("IMAP connection lost, attempting to reconnect...")
                        self.connect_source_imap()
                    
                    # Select inbox
                    self.imap.select('INBOX')
                    
                    # Search for unread emails
                    _, messages = self.imap.search(None, 'UNSEEN')
                    
                    for email_id in messages[0].split():
                        if self.forward_email(email_id):
                            # Mark as read
                            self.imap.store(email_id, '+FLAGS', '\\Seen')
                    
                    time.sleep(60)  # Check every minute
                    
                except Exception as e:
                    print(f"Error processing emails: {e}")
                    time.sleep(60)  # Wait for one minute after an error occurs
                    
        finally:
            if self.imap:
                self.imap.logout()

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

# Example usage
if __name__ == "__main__":
    # Source server configuration (spmode)
    SOURCE_IMAP_SERVER = "imap.spmode.ne.jp"
    SOURCE_IMAP_PORT = 993
    SOURCE_EMAIL = "fengjueming@gmail.com"
    SOURCE_PASSWORD = "ZXX_Dy@?k%"
    
    # Destination server configuration (Gmail)
    DEST_IMAP_SERVER = "imap.gmail.com"
    DEST_IMAP_PORT = 993
    DEST_EMAIL = "fengjueming@gmail.com"
    DEST_PASSWORD = "kujzlbksmaynlknz"  # Gmail requires using an app-specific password
    
    forwarder = EmailForwarder(
        SOURCE_IMAP_SERVER, SOURCE_IMAP_PORT, SOURCE_EMAIL, SOURCE_PASSWORD,
        DEST_IMAP_SERVER, DEST_IMAP_PORT, DEST_EMAIL, DEST_PASSWORD
    )
    
    try:
        forwarder.connect_source_imap()  # Initial connection (with retry)
        forwarder.start()
    except KeyboardInterrupt:
        print("Stopping service...")
        forwarder.running = False
    except Exception as e:
        print(f"Service error: {e}")