FROM python:3.11-slim

# Debug label to force cache invalidation
LABEL debug="extract_raw_words_fix_v1"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy worker code
COPY worker/ .

# Copy shared models from backend
COPY backend/app/models/ ./app/models/
COPY backend/app/config.py ./app/config.py

# Copy GCS credentials
COPY gcs-service-account.json ./gcs-service-account.json

# Run RQ worker
ENV PYTHONPATH=/app
CMD ["rq", "worker", "-u", "redis://redis:6379/0", "main", "--with-scheduler"]

