#!/usr/bin/env python3
"""
Web Scraper Tool
Fetches web page content with headers and status handling
"""

import json
import sys
import urllib.request
import urllib.error
from typing import Dict, Any

def fetch_url(url: str, timeout: int = 30, user_agent: str = None) -> Dict[str, Any]:
    """
    Fetch web page content
    For production, use requests library or scrapy
    """
    if not user_agent:
        user_agent = "Mozilla/5.0 (WebResearcher/1.0)"
    
    headers = {
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=timeout) as response:
            content = response.read().decode('utf-8', errors='ignore')
            status_code = response.getcode()
            response_headers = dict(response.headers)
            
            return {
                "success": True,
                "url": url,
                "status_code": status_code,
                "content": content,
                "content_length": len(content),
                "headers": response_headers
            }
    
    except urllib.error.HTTPError as e:
        return {
            "success": False,
            "url": url,
            "status_code": e.code,
            "error": f"HTTP Error: {e.code} - {e.reason}",
            "content": None
        }
    
    except urllib.error.URLError as e:
        return {
            "success": False,
            "url": url,
            "error": f"URL Error: {str(e.reason)}",
            "content": None
        }
    
    except Exception as e:
        return {
            "success": False,
            "url": url,
            "error": str(e),
            "content": None
        }

def health_check() -> Dict[str, Any]:
    """Health check for the tool"""
    return {
        "status": "healthy",
        "version": "1.0",
        "capabilities": ["fetch_url", "custom_headers"],
        "library": "urllib (built-in)"
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
    if 'url' not in params:
        print(json.dumps({
            "error_type": "MissingParameter",
            "error_message": "Required parameter 'url' not provided"
        }), file=sys.stderr)
        sys.exit(1)
    
    # Extract parameters
    url = params['url']
    timeout = params.get('timeout', 30)
    user_agent = params.get('user_agent', None)
    
    # Fetch URL
    result = fetch_url(url, timeout, user_agent)
    
    print(json.dumps(result))
    sys.exit(0 if result.get('success') else 1)

if __name__ == "__main__":
    main()
