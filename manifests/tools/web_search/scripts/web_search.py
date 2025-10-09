#!/usr/bin/env python3
"""
Web Search Tool - DuckDuckGo search integration
"""

import sys
import json
import requests
from typing import Dict, List
from urllib.parse import quote_plus


def search_duckduckgo(query: str, max_results: int = 5) -> Dict:
    """Search DuckDuckGo and return results."""
    try:
        # DuckDuckGo Instant Answer API
        url = f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json&no_html=1&skip_disambig=1"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        results = []
        
        # Abstract (direct answer)
        if data.get("Abstract"):
            results.append({
                "type": "answer",
                "title": data.get("Heading", "Answer"),
                "snippet": data.get("Abstract"),
                "url": data.get("AbstractURL", ""),
                "source": data.get("AbstractSource", "DuckDuckGo")
            })
        
        # Related Topics
        for topic in data.get("RelatedTopics", [])[:max_results]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append({
                    "type": "related",
                    "title": topic.get("Text", "").split(" - ")[0],
                    "snippet": topic.get("Text", ""),
                    "url": topic.get("FirstURL", ""),
                    "source": "DuckDuckGo"
                })
        
        # If we got no results, try a simple web search
        if not results:
            # Use DuckDuckGo HTML search as fallback
            html_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            results.append({
                "type": "info",
                "title": "Search Results",
                "snippet": f"Visit DuckDuckGo for results: {query}",
                "url": html_url,
                "source": "DuckDuckGo"
            })
        
        return {
            "status": "success",
            "query": query,
            "results": results[:max_results],
            "count": len(results[:max_results])
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "query": query
        }


def main():
    """Main entry point."""
    try:
        # Read input from stdin or first argument
        if len(sys.argv) > 1:
            input_data = json.loads(sys.argv[1])
        else:
            input_data = json.load(sys.stdin)
        
        query = input_data.get("query")
        if not query:
            print(json.dumps({"status": "error", "error": "Missing 'query' parameter"}))
            sys.exit(1)
        
        max_results = input_data.get("max_results", 5)
        
        result = search_duckduckgo(query, max_results)
        print(json.dumps(result, indent=2))
        
        sys.exit(0 if result["status"] == "success" else 1)
        
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
