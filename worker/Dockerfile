FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY ./worker/requirements.txt ./worker/requirements.txt
RUN pip install --no-cache-dir -r ./worker/requirements.txt

# Copy worker code
COPY ./worker/ ./worker/

# Copy shared models from backend
COPY ./backend/app/models/ ./backend/app/models/
COPY ./backend/app/config.py ./backend/app/config.py

# Run RQ worker
ENV PYTHONPATH=/app
CMD ["rq", "worker", "-u", "redis://redis:6379/0", "analysis"]

