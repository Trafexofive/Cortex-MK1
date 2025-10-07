#!/usr/bin/env python3
import json
import sys

def analyze_sentiment(text):
    # A very simple sentiment analysis
    positive_words = ["happy", "good", "great", "wonderful", "awesome", "love"]
    negative_words = ["sad", "bad", "terrible", "horrible", "hate"]

    text_lower = text.lower()
    positive_count = sum(word in text_lower for word in positive_words)
    negative_count = sum(word in text_lower for word in negative_words)

    if positive_count > negative_count:
        sentiment = "positive"
    elif negative_count > positive_count:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    return {"sentiment": sentiment, "positive_score": positive_count, "negative_score": negative_count}

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "No JSON parameters provided."}))
        sys.exit(1)

    try:
        params = json.loads(sys.argv[1])
        operation = params.get("operation")
        text = params.get("text")

        if operation == "analyze_sentiment":
            if not text:
                result = {"success": False, "error": "'text' parameter is required for analyze_sentiment."}
            else:
                result = analyze_sentiment(text)
        else:
            result = {"success": False, "error": f"Unknown operation: {operation}"}
        
        print(json.dumps({"success": True, "result": result}))

    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()
