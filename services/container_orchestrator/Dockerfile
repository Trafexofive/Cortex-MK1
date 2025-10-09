FROM python:3.11-slim

WORKDIR /app

# Install Docker CLI (needed for docker SDK)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8086

# Run service
CMD ["python", "main.py"]
