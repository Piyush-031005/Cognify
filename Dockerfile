# Dockerfile for Cognify v3.0 Production Deployment
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose server port
EXPOSE 10000

# Set environment defaults
ENV PORT=10000
ENV COGNIFY_BYPASS_AUTH=false

# Start server
CMD ["python", "app.py"]
