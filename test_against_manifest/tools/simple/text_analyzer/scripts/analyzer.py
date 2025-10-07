#!/usr/bin/env python3
"""
Text Analyzer Tool
"""
import json
import sys
import re


def count_words(text):
    """Count words in text"""
    return len(text.split())


def count_chars(text):
    """Count characters in text"""
    return len(text)


def count_sentences(text):
    """Count sentences in text"""
    sentences = re.split(r'[.!?]+', text)
    return len([s for s in sentences if s.strip()])


def detect_sentiment(text):
    """Basic sentiment detection"""
    positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'love', 'best']
    negative_words = ['bad', 'terrible', 'awful', 'worst', 'hate', 'poor', 'horrible']
    
    text_lower = text.lower()
    pos_count = sum(1 for word in positive_words if word in text_lower)
    neg_count = sum(1 for word in negative_words if word in text_lower)
    
    if pos_count > neg_count:
        return "positive"
    elif neg_count > pos_count:
        return "negative"
    else:
        return "neutral"


def analyze_text(text):
    """Comprehensive text analysis"""
    return {
        "word_count": count_words(text),
        "char_count": count_chars(text),
        "sentence_count": count_sentences(text),
        "sentiment": detect_sentiment(text),
        "avg_word_length": count_chars(text) / max(count_words(text), 1)
    }


def health_check():
    """Health check"""
    return {"status": "ok", "tool": "text_analyzer"}


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "No parameters provided"}))
        sys.exit(1)
    
    try:
        params = json.loads(sys.argv[1])
        operation = params.get("operation")
        
        if operation == "health_check":
            result = health_check()
            print(json.dumps({"success": True, **result}))
            return
        
        text = params.get("text", "")
        if not text:
            print(json.dumps({"success": False, "error": "Text parameter is required"}))
            sys.exit(1)
        
        if operation == "analyze":
            result = analyze_text(text)
        elif operation == "count_words":
            result = {"word_count": count_words(text)}
        elif operation == "detect_sentiment":
            result = {"sentiment": detect_sentiment(text)}
        else:
            print(json.dumps({"success": False, "error": f"Unknown operation: {operation}"}))
            sys.exit(1)
        
        print(json.dumps({"success": True, **result}))
    
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
