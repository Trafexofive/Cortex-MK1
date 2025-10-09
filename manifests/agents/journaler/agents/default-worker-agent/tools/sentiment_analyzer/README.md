# Sentiment Analyzer Tool (Worker-Local)

**Simple sentiment analysis for default-worker-agent**

## Overview

Analyzes text sentiment using basic keyword matching. This is a local tool for the default-worker-agent (sub-agent of journaler).

## Operations

- `analyze_sentiment` - Analyzes sentiment of provided text

## Usage

```bash
# Analyze sentiment
python3 scripts/sentiment.py '{
  "operation": "analyze_sentiment",
  "text": "I am very happy today!"
}'
```

## Output

Returns JSON with sentiment analysis result (positive/negative/neutral).

## Implementation

Simple Python script using keyword-based sentiment analysis. No external dependencies required.

For production use, consider integrating with:
- TextBlob
- VADER sentiment
- Transformers-based models

## Manifest

- **Path:** `agents/journaler/agents/default-worker-agent/tools/sentiment_analyzer/tool.yml`
- **Version:** 1.0
- **State:** stable
- **Local to:** default-worker-agent
