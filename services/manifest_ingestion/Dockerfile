FROM python:3.11-slim

LABEL maintainer="PRAETORIAN_CHIMERA"
LABEL description="Cortex-Prime Manifest Ingestion Service"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash cortex
RUN chown -R cortex:cortex /app
USER cortex

# Health check
HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8082/health || exit 1

# Expose port
EXPOSE 8082

# Default environment variables
ENV HOST=0.0.0.0
ENV PORT=8082
ENV LOG_LEVEL=info

# Start the service
CMD ["python", "main.py"]