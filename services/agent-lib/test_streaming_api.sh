#!/bin/bash

# Test Gemini streaming API
timeout 10 curl -N "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:streamGenerateContent?alt=sse&key=${GEMINI_API_KEY}" \
  -H 'Content-Type: application/json' \
  -d '{
    "contents": [{
      "parts":[{"text": "Say hello in one word"}]
    }],
    "generationConfig": {
      "temperature": 0.3,
      "maxOutputTokens": 100
    }
  }'
