# StorageUnitMk1

Universal key-value storage system for agent data persistence. Clean, minimal implementation with atomic operations, TTL support, and namespace isolation.

## Features

- **Atomic Operations**: All storage operations are atomic with SQLite ACID guarantees
- **Namespace Isolation**: Organize data across different namespaces for clean separation
- **TTL Support**: Automatic expiration of time-sensitive data
- **Pattern Matching**: List keys with wildcard pattern support
- **Statistics Tracking**: Monitor usage patterns and performance
- **Automatic Cleanup**: Expired entries are cleaned up automatically
- **Backup System**: Create JSON backups of all stored data

## Installation

```bash
# No external dependencies - uses Python stdlib only
chmod +x scripts/storage_unit_mk1.py
```

## Usage Examples

### Store Data
```bash
python3 storage_unit_mk1.py '{"operation": "store", "namespace": "config", "key": "api_url", "value": "https://api.example.com", "ttl": 3600}'
```

### Retrieve Data
```bash
python3 storage_unit_mk1.py '{"operation": "retrieve", "namespace": "config", "key": "api_url"}'
```

### List Keys
```bash
# List all keys in namespace
python3 storage_unit_mk1.py '{"operation": "list", "namespace": "config"}'

# List with pattern
python3 storage_unit_mk1.py '{"operation": "list", "namespace": "config", "pattern": "api_*"}'
```

### Delete Data
```bash
python3 storage_unit_mk1.py '{"operation": "delete", "namespace": "config", "key": "api_url"}'
```

### Get Statistics
```bash
python3 storage_unit_mk1.py '{"operation": "stats"}'
```

### Clear Namespace
```bash
python3 storage_unit_mk1.py '{"operation": "clear", "namespace": "config"}'
```

### Create Backup
```bash
python3 storage_unit_mk1.py '{"operation": "backup"}'
```

## Operations

| Operation | Required Parameters | Optional Parameters | Description |
|-----------|-------------------|-------------------|-------------|
| `store` | `key`, `value` | `ttl`, `namespace` | Store key-value pair |
| `retrieve` | `key` | `namespace` | Get value by key |
| `delete` | `key` | `namespace` | Remove key-value pair |
| `list` | - | `pattern`, `namespace` | List keys in namespace |
| `stats` | - | - | Get storage statistics |
| `clear` | - | `namespace` | Clear all keys in namespace |
| `backup` | - | - | Create JSON backup |

## Configuration

- **Data Directory**: `$AGENT_WORKSPACE/.data/` (default: `./.data/`)
- **Database**: SQLite file at `.data/storage_unit_mk1.db`
- **Default Namespace**: `default`
- **Automatic Cleanup**: Runs on store/retrieve/list operations

## Performance

- **Small footprint**: ~250 lines of clean Python code
- **Fast operations**: SQLite with proper indexing
- **Memory efficient**: No in-memory caching, direct SQLite access
- **Concurrent safe**: SQLite handles concurrent access automatically

## Error Handling

All operations return JSON with `success` field:
```json
{
  "success": true,
  "message": "Operation completed",
  "data": "..."
}
```

Or on error:
```json
{
  "success": false,
  "error": "Error description"
}
```

## Development

The code follows the enterprise patterns from your system prompt but keeps implementation minimal:

- **Clean separation**: Validation, core operations, and utilities are separate
- **Defensive programming**: All inputs validated, edge cases handled
- **Resource management**: Proper SQLite connection handling with context managers
- **Logging**: Statistics tracking for monitoring (silent fail to avoid noise)
- **Schema evolution**: Database schema designed for future extensions

Perfect for building more complex agent systems while maintaining simplicity.
