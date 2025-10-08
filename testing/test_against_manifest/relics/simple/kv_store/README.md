# KV Store Relic

Simple persistent key-value storage service using FastAPI and SQLite.

## Features

- RESTful API
- SQLite persistence
- Docker deployment
- Health check endpoint

## API Endpoints

- `POST /set` - Store key-value pair
- `GET /get/{key}` - Retrieve value
- `DELETE /delete/{key}` - Delete key
- `GET /list` - List all keys
- `GET /health` - Health check

## Deployment

```bash
docker-compose up -d
```

## Testing

```bash
# Health check
curl http://localhost:8004/health

# Set value
curl -X POST http://localhost:8004/set \
  -H "Content-Type: application/json" \
  -d '{"key": "test", "value": {"data": "hello"}}'

# Get value
curl http://localhost:8004/get/test

# Delete value
curl -X DELETE http://localhost:8004/delete/test
```
