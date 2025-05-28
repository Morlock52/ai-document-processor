FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    python3-opencv \
    libgl1-mesa-glx \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY worker/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy worker code
COPY worker /app/worker
COPY backend /app/backend

# Create necessary directories
RUN mkdir -p /app/uploads

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set working directory for the worker
WORKDIR /app/worker

# Command to run the worker
CMD ["rq", "worker", "--url", "redis://redis:6379/0", "--path", "/app"]
