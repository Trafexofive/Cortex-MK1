# Calendar Tool

**Simple date and time tool for journaler agent**

## Overview

Provides current date and time information for the journaler agent. Used for timestamping journal entries and date-based operations.

## Operations

- `get_current_date` - Returns current date
- `get_current_time` - Returns current time

## Usage

```bash
# Get current date
python3 scripts/calendar.py '{"operation": "get_current_date"}'

# Get current time
python3 scripts/calendar.py '{"operation": "get_current_time"}'
```

## Output

Returns JSON with the requested date/time information.

## Implementation

Simple Python script using built-in datetime module. No external dependencies required.

## Manifest

- **Path:** `agents/journaler/tools/calendar/tool.yml`
- **Version:** 1.0
- **State:** stable
- **Local to:** journaler agent
