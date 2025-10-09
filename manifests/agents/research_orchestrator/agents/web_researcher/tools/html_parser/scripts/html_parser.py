#!/usr/bin/env python3
"""
HTML Parser Tool
Extracts structured data from HTML content
"""

import json
import sys
import re
from typing import Dict, Any, List

def extract_text(html: str) -> str:
    """
    Extract plain text from HTML
    For production, use BeautifulSoup or lxml
    """
    # Remove script and style tags
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', html)
    
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text

def extract_links(html: str) -> List[Dict[str, str]]:
    """
    Extract links from HTML
    For production, use BeautifulSoup
    """
    links = []
    
    # Simple regex to find links (not perfect, use BeautifulSoup for production)
    pattern = r'<a\s+(?:[^>]*?\s+)?href="([^"]*)"[^>]*>(.*?)</a>'
    matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
    
    for href, text in matches:
        links.append({
            "url": href,
            "text": extract_text(text)
        })
    
    return links

def extract_headings(html: str) -> Dict[str, List[str]]:
    """
    Extract headings from HTML
    """
    headings = {
        "h1": [],
        "h2": [],
        "h3": [],
        "h4": [],
        "h5": [],
        "h6": []
    }
    
    for level in range(1, 7):
        tag = f"h{level}"
        pattern = f'<{tag}[^>]*>(.*?)</{tag}>'
        matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
        headings[tag] = [extract_text(m) for m in matches]
    
    return headings

def parse_html(html: str, extract_type: str = "all") -> Dict[str, Any]:
    """
    Parse HTML and extract requested information
    """
    result = {
        "success": True
    }
    
    if extract_type in ["all", "text"]:
        result["text"] = extract_text(html)
    
    if extract_type in ["all", "links"]:
        result["links"] = extract_links(html)
    
    if extract_type in ["all", "headings"]:
        result["headings"] = extract_headings(html)
    
    if extract_type == "all":
        result["stats"] = {
            "total_links": len(result.get("links", [])),
            "text_length": len(result.get("text", "")),
            "total_headings": sum(len(v) for v in result.get("headings", {}).values())
        }
    
    return result

def health_check() -> Dict[str, Any]:
    """Health check for the tool"""
    return {
        "status": "healthy",
        "version": "1.0",
        "capabilities": ["text_extraction", "link_extraction", "heading_extraction"],
        "library": "regex (built-in)"
    }

def main():
    """Main entry point"""
    if len(sys.argv) > 1:
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
        try:
            params = json.loads(sys.stdin.read())
        except json.JSONDecodeError as e:
            print(json.dumps({
                "error_type": "InvalidInput",
                "error_message": f"Invalid JSON input: {str(e)}"
            }), file=sys.stderr)
            sys.exit(1)
    
    # Validate required parameters
    if 'html' not in params:
        print(json.dumps({
            "error_type": "MissingParameter",
            "error_message": "Required parameter 'html' not provided"
        }), file=sys.stderr)
        sys.exit(1)
    
    # Extract parameters
    html = params['html']
    extract_type = params.get('extract_type', 'all')
    
    # Parse HTML
    try:
        result = parse_html(html, extract_type)
        print(json.dumps(result))
        sys.exit(0)
    except Exception as e:
        print(json.dumps({
            "error_type": "ParsingError",
            "error_message": str(e)
        }), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
