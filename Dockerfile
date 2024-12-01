FROM python:3.9-slim

WORKDIR /app

COPY mail.py .

CMD ["python", "mail.py"] 