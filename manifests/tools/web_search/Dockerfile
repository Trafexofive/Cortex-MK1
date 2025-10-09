FROM python:3.11-slim

WORKDIR /tool

# Copy tool files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scripts/ ./scripts/

# Make script executable
RUN chmod +x ./scripts/web_search.py

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python3 -c "import requests; print('ok')" || exit 1

# Default entrypoint
ENTRYPOINT ["python3", "./scripts/web_search.py"]
