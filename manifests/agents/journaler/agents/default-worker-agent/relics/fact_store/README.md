# Fact Store Relic

**Simple persistent key-value storage for default-worker-agent**

## Overview

A simple key-value storage service local to the default-worker-agent. Stores facts and metadata using SQLite with persistent storage.

## Features

- **Simple KV Storage**: Store and retrieve JSON facts
- **Persistence**: SQLite-backed persistent storage
- **Timestamps**: Automatic created_at and updated_at tracking
- **Key Listing**: List all stored fact keys
- **Statistics**: Storage usage statistics

## Endpoints

- `GET /health` - Health check
- `GET /system/capabilities` - Service capabilities
- `POST /set` - Store a fact
- `GET /get/{key}` - Retrieve a fact
- `DELETE /delete/{key}` - Delete a fact
- `GET /keys` - List all fact keys
- `GET /stats` - Get storage statistics

## Deployment

```bash
cd manifests/agents/journaler/agents/default-worker-agent/relics/fact_store
docker-compose up -d
```

Service will be available at `http://localhost:8006`

## Usage

### Store a fact
```bash
curl -X POST http://localhost:8006/set \
  -H "Content-Type: application/json" \
  -d '{
    "key": "user:preferences",
    "value": {"theme": "dark", "language": "en"}
  }'
```

### Retrieve a fact
```bash
curl http://localhost:8006/get/user:preferences
```

### List all keys
```bash
curl http://localhost:8006/keys
```

### Get statistics
```bash
curl http://localhost:8006/stats
```

## Integration

Used by default-worker-agent (sub-agent of journaler) to store worker-specific facts and state.

## Storage

- Backend: SQLite
- Database: `/data/fact_store.db`
- Volume: Docker volume `fact_data`
- Tracking: Created and updated timestamps for each fact

## Response Format

All endpoints return JSON responses:

```json
{
  "success": true,
  "key": "user:preferences",
  "value": {"theme": "dark", "language": "en"},
  "message": "Fact stored successfully"
}
```

## Manifest

- **Path:** `agents/journaler/agents/default-worker-agent/relics/fact_store/relic.yml`
- **Version:** 1.0
- **State:** stable
- **Port:** 8006
- **Author:** PRAETORIAN_CHIMERA
