# Journal Entry Pipeline Workflow

**Complete pipeline for processing and storing journal entries**

## Overview

A workflow that processes journal entries by analyzing sentiment, gathering metadata, and storing in the journal KV store. Demonstrates sequential execution with error handling and actual implementations.

## Trigger

**Type:** Manual  
**Event:** `journal.new_entry`

### Parameters

- `entry_text` (string, required) - Journal entry text (10-10000 chars)
  - Validation: min_length: 10, max_length: 10000
- `user_id` (string, required) - User identifier
  - Validation: pattern: `^user_[a-z0-9]+$`
- `tags` (array, optional) - Entry tags

## Steps

1. **analyze_sentiment** - Analyze entry sentiment with scores
2. **get_system_info** - Get OS information for metadata
3. **build_entry** - Compile enriched entry data
4. **store_entry** - Store in journal_kv_store

## Outputs

- `entry_id` - Unique identifier for stored entry
- `sentiment` - Overall sentiment (optional)
- `timestamp` - Entry timestamp

## Dependencies

### Tools
- `sentiment_analyzer` - Sentiment analysis
- `sys_info` - System information

### Relics
- `journal_kv_store` - Journal storage (from journaler agent)

## Usage

Trigger the workflow with a journal entry:

```json
{
  "entry_text": "Today was an amazing day! I accomplished so much and felt great.",
  "user_id": "user_john",
  "tags": ["personal", "achievement"]
}
```

Expected output:
```json
{
  "entry_id": "entry:1234567890:user_john",
  "sentiment": "positive",
  "timestamp": "1234567890"
}
```

Stored entry includes:
- Original text
- User ID and tags
- Sentiment analysis results
- System information
- Workflow metadata
- Timestamp

## Configuration

- **Timeout:** 300 seconds (5 minutes)
- **Retry Policy:** Exponential backoff, max 3 attempts
- **Error Handling:** Continue on step failure
- **Observability:** INFO level logging, tracing enabled

## Error Handling

- Sentiment analysis failure: Continue (entry stored without sentiment)
- System info failure: Continue (entry stored without system metadata)
- Storage failure: Abort (critical operation)

## Manifest

- **Path:** `workflow/journal_entry_pipeline.workflow.yml`
- **Version:** 1.0
- **State:** stable
- **Author:** PRAETORIAN_CHIMERA
