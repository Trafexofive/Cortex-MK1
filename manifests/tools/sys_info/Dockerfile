FROM python:3.11-slim

WORKDIR /tool

# Copy tool files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scripts/ ./scripts/

# Make script executable
RUN chmod +x ./scripts/sys_info.py

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python3 ./scripts/sys_info.py '{"operation": "health_check"}' || exit 1

# Default entrypoint
ENTRYPOINT ["python3", "./scripts/sys_info.py"]
