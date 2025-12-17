# Backend Dockerfile (Python Flask API)
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir flask flask-cors gunicorn

# Copy application code
COPY . .

# Expose API port
EXPOSE 8080

# Run with gunicorn (production WSGI server)
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--threads", "4", "api_server:app"]
