#!/usr/bin/env python3
"""
Sentiment Analysis Tool
Analyzes text sentiment using simple rule-based approach
For production use, integrate with transformers library
"""

import json
import sys
import time
from typing import Dict, Any

def analyze_sentiment(text: str, return_scores: bool = False) -> Dict[str, Any]:
    """
    Analyze sentiment of text using simple keyword-based approach
    
    For production, replace with actual ML model (transformers)
    """
    start_time = time.time()
    
    # Simple keyword-based sentiment (replace with actual ML model)
    positive_words = [
        'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
        'love', 'best', 'awesome', 'perfect', 'beautiful', 'brilliant'
    ]
    negative_words = [
        'bad', 'terrible', 'awful', 'horrible', 'worst', 'hate',
        'poor', 'disappointing', 'useless', 'pathetic'
    ]
    
    text_lower = text.lower()
    words = text_lower.split()
    
    positive_count = sum(1 for word in words if any(pw in word for pw in positive_words))
    negative_count = sum(1 for word in words if any(nw in word for nw in negative_words))
    
    # Determine sentiment
    if positive_count > negative_count:
        sentiment = "positive"
        confidence = min(0.95, 0.5 + (positive_count / len(words)) * 2)
    elif negative_count > positive_count:
        sentiment = "negative"
        confidence = min(0.95, 0.5 + (negative_count / len(words)) * 2)
    else:
        sentiment = "neutral"
        confidence = 0.6
    
    processing_time = (time.time() - start_time) * 1000
    
    result = {
        "sentiment": sentiment,
        "confidence": round(confidence, 2),
        "language": "en",  # Auto-detected (simplified)
        "processing_time_ms": round(processing_time, 2)
    }
    
    if return_scores:
        total = positive_count + negative_count + 1
        result["scores"] = {
            "positive": round(positive_count / total, 2),
            "negative": round(negative_count / total, 2),
            "neutral": round(1 / total, 2)
        }
    
    return result

def health_check() -> Dict[str, Any]:
    """Health check for the tool"""
    return {
        "status": "healthy",
        "version": "1.0",
        "model": "simple-keyword-based",
        "ready": True
    }

def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        # Parse command line argument
        if sys.argv[1] == '--health-check':
            result = health_check()
            print(json.dumps(result))
            sys.exit(0)
        
        try:
            params = json.loads(sys.argv[1])
        except json.JSONDecodeError as e:
            print(json.dumps({
                "error_type": "InvalidInput",
                "error_message": f"Invalid JSON input: {str(e)}"
            }), file=sys.stderr)
            sys.exit(1)
    else:
        # Read from stdin
        try:
            params = json.loads(sys.stdin.read())
        except json.JSONDecodeError as e:
            print(json.dumps({
                "error_type": "InvalidInput",
                "error_message": f"Invalid JSON input: {str(e)}"
            }), file=sys.stderr)
            sys.exit(1)
    
    # Validate required parameters
    if 'text' not in params:
        print(json.dumps({
            "error_type": "MissingParameter",
            "error_message": "Required parameter 'text' not provided"
        }), file=sys.stderr)
        sys.exit(1)
    
    # Extract parameters
    text = params['text']
    return_scores = params.get('return_scores', False)
    
    # Validate text length
    if len(text) < 1:
        print(json.dumps({
            "error_type": "ValidationError",
            "error_message": "Text must be at least 1 character"
        }), file=sys.stderr)
        sys.exit(1)
    
    if len(text) > 10000:
        print(json.dumps({
            "error_type": "ValidationError",
            "error_message": "Text exceeds maximum length of 10000 characters"
        }), file=sys.stderr)
        sys.exit(1)
    
    # Analyze sentiment
    try:
        result = analyze_sentiment(text, return_scores)
        print(json.dumps(result))
        sys.exit(0)
    except Exception as e:
        print(json.dumps({
            "error_type": "ProcessingError",
            "error_message": str(e)
        }), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
