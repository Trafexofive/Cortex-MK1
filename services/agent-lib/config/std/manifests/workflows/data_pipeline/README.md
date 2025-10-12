# Text Processing Pipeline Workflow

Simple workflow that analyzes text and stores the results.

## Steps

1. **analyze_text**: Uses `text_analyzer` tool to analyze input text
2. **store_results**: Stores analysis results in `kv_store` relic

## Usage

```yaml
trigger:
  input_text: "This is a wonderful day! I love it."
```

## Expected Flow

1. Text is analyzed for word count, sentiment, etc.
2. Results are stored in KV store with timestamped key
3. Workflow returns analysis key and metrics

## Outputs

- `analysis_key`: Key where results were stored
- `word_count`: Number of words
- `sentiment`: Detected sentiment (positive/negative/neutral)

## Error Handling

- If analysis fails, workflow aborts
- Storage has 3 retry attempts with exponential backoff
- All steps are logged and traced
