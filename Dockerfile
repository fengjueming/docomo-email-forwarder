FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y ca-certificates openssl && \
    rm -rf /var/lib/apt/lists/*

COPY mail.py .

# Add these environment variables to enable legacy SSL behavior
ENV PYTHONWARNINGS="ignore:ssl-warnings"
ENV OPENSSL_CONF=/etc/ssl/openssl.cnf
ENV OPENSSL_ENABLE_UNSAFE_RENEGOTIATION=1

# Create custom OpenSSL configuration
RUN echo ' \n\
openssl_conf = default_conf \n\
\n\
[default_conf] \n\
ssl_conf = ssl_sect \n\
\n\
[ssl_sect] \n\
system_default = system_default_sect \n\
\n\
[system_default_sect] \n\
Options = UnsafeLegacyRenegotiation' > /etc/ssl/openssl.cnf

CMD ["python", "mail.py"] 