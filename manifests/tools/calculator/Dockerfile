FROM python:3.11-slim

WORKDIR /tool

# Copy tool files
COPY requirements.txt .
COPY scripts/ ./scripts/

# Make script executable
RUN chmod +x ./scripts/calculator.py

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python3 ./scripts/calculator.py '{"expression": "1+1"}' || exit 1

# Default entrypoint
ENTRYPOINT ["python3", "./scripts/calculator.py"]
