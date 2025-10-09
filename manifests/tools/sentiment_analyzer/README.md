# Sentiment Analyzer Tool

**ML-powered sentiment analysis tool**

## Overview

Analyzes text sentiment and returns sentiment label (positive/negative/neutral) with confidence scores.

**Current Implementation**: Simple keyword-based approach  
**Production Ready**: Integrate with transformers library for ML-powered analysis

## Operations

The tool accepts a JSON input with:
- `text` (required): Text to analyze
- `model` (optional): Model to use ('default', 'multilingual', 'financial')
- `language` (optional): Text language code
- `return_scores` (optional): Return all class scores

## Usage

```bash
# Basic sentiment analysis
python3 scripts/sentiment_analyzer.py '{"text": "I love this product!"}'

# With all scores
python3 scripts/sentiment_analyzer.py '{
  "text": "The product is okay",
  "return_scores": true
}'

# Health check
python3 scripts/sentiment_analyzer.py --health-check
```

## Output

```json
{
  "sentiment": "positive",
  "confidence": 0.95,
  "language": "en",
  "processing_time_ms": 2.5,
  "scores": {
    "positive": 0.85,
    "negative": 0.10,
    "neutral": 0.05
  }
}
```

## Production Deployment

For production use with ML models:

1. Uncomment transformers dependencies in requirements.txt
2. Install: `pip install -r requirements.txt`
3. Update script to use transformers models
4. Pre-download models in build phase

## Manifest

- **Path:** `tools/sentiment_analyzer/tool.yml`
- **Version:** 1.0
- **State:** stable
- **Resource Requirements:**
  - Memory: 512M (ML model), 128M (keyword-based)
  - CPU: 0.5
  - Timeout: 30s

## Example Integration

```yaml
# In an agent manifest
import:
  tools:
    - "path/to/tools/sentiment_analyzer/tool.yml"
```

## Error Handling

The tool returns proper error responses:
- `InvalidInput`: JSON parsing error
- `MissingParameter`: Required parameter missing
- `ValidationError`: Input validation failed
- `ProcessingError`: Processing failed
