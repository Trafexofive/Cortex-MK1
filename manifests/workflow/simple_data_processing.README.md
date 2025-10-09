# Simple Data Processing Workflow

**Basic data processing workflow with sentiment analysis**

## Overview

A simple workflow that processes text data by analyzing sentiment and storing results. Demonstrates basic workflow concepts with actual tool implementations.

## Trigger

**Type:** Manual  
**Event:** `data.process`

### Parameters

- `text_data` (string, required) - Text data to process
- `user_id` (string, required) - User identifier

## Steps

1. **analyze_text** - Analyze sentiment using sentiment_analyzer tool
2. **store_results** - Store analysis results in kv_store

## Outputs

- `analysis_id` - Key where analysis was stored
- `sentiment` - Detected sentiment (positive/negative/neutral)
- `confidence` - Confidence score (0.0-1.0)

## Dependencies

### Tools
- `sentiment_analyzer` - Sentiment analysis tool

### Relics
- `kv_store` - Key-value storage

## Usage

This workflow is designed to be triggered manually or via API:

```json
{
  "text_data": "I love this amazing product!",
  "user_id": "user_123"
}
```

Expected output:
```json
{
  "analysis_id": "analysis:user_123:1234567890",
  "sentiment": "positive",
  "confidence": 0.95
}
```

## Configuration

- **Timeout:** 120 seconds
- **Retry Policy:** Linear backoff, max 2 attempts
- **Error Handling:** Abort on step failure
- **Observability:** INFO level logging, tracing enabled

## Manifest

- **Path:** `workflow/simple_data_processing.workflow.yml`
- **Version:** 1.0
- **State:** stable
- **Author:** PRAETORIAN_CHIMERA
