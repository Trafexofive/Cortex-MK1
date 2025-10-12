#!/bin/bash

# Test direct Gemini API call
curl -s "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${GEMINI_API_KEY}" \
  -H 'Content-Type: application/json' \
  -d '{
    "contents": [{
      "parts":[{"text": "Say hello in one word"}]
    }],
    "generationConfig": {
      "temperature": 0.3,
      "maxOutputTokens": 100
    }
  }' | jq -r '.candidates[0].content.parts[0].text' 2>/dev/null || echo "API call failed"
