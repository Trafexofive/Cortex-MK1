#!/usr/bin/env python3
"""
Web Search Tool for Chimera Ecosystem
Supports multiple search engines with fallback capabilities
"""

import json
import os
import sys
import time
import hashlib
import sqlite3
from pathlib import Path
from urllib.parse import urlencode, urlparse, quote_plus
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import re
import html

# Configuration
DATA_DIR = Path(os.getenv("AGENT_WORKSPACE", ".")) / ".data"
DB_PATH = DATA_DIR / "web_search.db"
CACHE_DURATION = 3600  # 1 hour cache
MAX_RETRIES = 3
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Search engine configurations
SEARCH_ENGINES = {
    'duckduckgo': {
        'url': 'https://html.duckduckgo.com/html/',
        'params': {'q': '{query}'},
        'parser': 'parse_duckduckgo'
    },
    'searx': {
        'instances': [
            'https://searx.be/',
            'https://search.sapti.me/',
            'https://searx.tiekoetter.com/'
        ],
        'path': 'search',
        'params': {'q': '{query}', 'format': 'json'},
        'parser': 'parse_searx'
    }
}

def ensure_data_dir():
    """Create the data directory if it doesn't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

def init_database():
    """Initialize the database with required tables."""
    ensure_data_dir()
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        
        # Cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_cache (
                query_hash TEXT PRIMARY KEY,
                query TEXT,
                results TEXT,
                timestamp INTEGER,
                engine TEXT
            )
        """)
        
        # Stats table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT,
                engine TEXT,
                timestamp INTEGER,
                success BOOLEAN,
                response_time REAL
            )
        """)
        
        conn.commit()

def get_query_hash(query, engine=""):
    """Generate a hash for cache key."""
    return hashlib.md5(f"{query}:{engine}".encode()).hexdigest()

def get_cached_results(query, engine=""):
    """Retrieve cached search results if they exist and are fresh."""
    query_hash = get_query_hash(query, engine)
    current_time = int(time.time())
    
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT results, timestamp FROM search_cache WHERE query_hash = ?",
            (query_hash,)
        )
        row = cursor.fetchone()
        
        if row and (current_time - row[1]) < CACHE_DURATION:
            return json.loads(row[0])
    
    return None

def cache_results(query, results, engine=""):
    """Cache search results."""
    query_hash = get_query_hash(query, engine)
    current_time = int(time.time())
    
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO search_cache (query_hash, query, results, timestamp, engine) VALUES (?, ?, ?, ?, ?)",
            (query_hash, query, json.dumps(results), current_time, engine)
        )
        conn.commit()

def log_search_stats(query, engine, success, response_time):
    """Log search statistics."""
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO search_stats (query, engine, timestamp, success, response_time) VALUES (?, ?, ?, ?, ?)",
            (query, engine, int(time.time()), success, response_time)
        )
        conn.commit()

def make_request(url, timeout=10, headers=None):
    """Make HTTP request with error handling."""
    if headers is None:
        headers = {'User-Agent': USER_AGENT}
    
    req = Request(url, headers=headers)
    
    for attempt in range(MAX_RETRIES):
        try:
            with urlopen(req, timeout=timeout) as response:
                return response.read().decode('utf-8', errors='ignore')
        except (URLError, HTTPError) as e:
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(1 * (attempt + 1))  # Exponential backoff
    
    return None

def parse_duckduckgo(html_content):
    """Parse DuckDuckGo HTML results with multiple fallback patterns."""
    results = []
    
    # Debug: Save content for inspection
    debug_file = DATA_DIR / "debug_duckduckgo.html"
    try:
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(html_content[:10000])  # First 10k chars
    except:
        pass
    
    # Multiple patterns to handle different DuckDuckGo layouts
    patterns = [
        # Pattern 1: Standard result format
        r'<div[^>]*class="[^"]*result[^"]*"[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?<span[^>]*class="[^"]*snippet[^"]*"[^>]*>(.*?)</span>',
        # Pattern 2: Alternative format
        r'<h2[^>]*class="[^"]*result[^"]*"[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?</h2>.*?<div[^>]*>(.*?)</div>',
        # Pattern 3: Simple link extraction
        r'<a[^>]*href="([^"]+)"[^>]*title="([^"]*)"[^>]*>.*?</a>',
        # Pattern 4: Most basic - any external link
        r'href="(https?://[^"]+)"[^>]*>([^<]+)</a>'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
        if matches:
            for match in matches:
                if len(match) >= 2:
                    url = html.unescape(match[0]).strip()
                    title = html.unescape(re.sub(r'<.*?>', '', match[1])).strip()
                    snippet = html.unescape(re.sub(r'<.*?>', '', match[2] if len(match) > 2 else '')).strip()
                    
                    # Filter out DuckDuckGo internal links and empty results
                    if (url and title and 
                        not url.startswith('http://duckduckgo.com') and 
                        not url.startswith('https://duckduckgo.com') and
                        'duckduckgo' not in url.lower() and
                        len(title) > 3):
                        
                        results.append({
                            'title': title[:200],  # Limit title length
                            'url': url,
                            'snippet': snippet[:300] if snippet else '',
                            'source': 'duckduckgo'
                        })
            
            if results:
                break  # Use first pattern that gives results
    
    return results

def parse_searx(json_content):
    """Parse Searx JSON results."""
    try:
        data = json.loads(json_content)
        results = []
        
        for result in data.get('results', []):
            if result.get('url') and result.get('title'):
                results.append({
                    'title': result.get('title', ''),
                    'url': result.get('url', ''),
                    'snippet': result.get('content', ''),
                    'source': 'searx'
                })
        
        return results
    except json.JSONDecodeError:
        return []

def search_duckduckgo(query, limit=10, timeout=10):
    """Search using DuckDuckGo with enhanced debugging."""
    start_time = time.time()
    
    try:
        # Try multiple DuckDuckGo endpoints
        endpoints = [
            'https://html.duckduckgo.com/html/',
            'https://lite.duckduckgo.com/lite/',
            'https://duckduckgo.com/html/'
        ]
        
        for endpoint in endpoints:
            try:
                params = urlencode({'q': query, 'kl': 'us-en'})
                full_url = f"{endpoint}?{params}"
                
                # Enhanced headers to avoid blocking
                headers = {
                    'User-Agent': USER_AGENT,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
                
                req = Request(full_url, headers=headers)
                
                with urlopen(req, timeout=timeout) as response:
                    content = response.read()
                    
                    # Handle gzip encoding
                    if response.headers.get('Content-Encoding') == 'gzip':
                        import gzip
                        content = gzip.decompress(content)
                    
                    html_content = content.decode('utf-8', errors='ignore')
                
                if not html_content or len(html_content) < 1000:
                    continue
                
                results = parse_duckduckgo(html_content)
                
                if results:
                    response_time = time.time() - start_time
                    log_search_stats(query, 'duckduckgo', True, response_time)
                    return results[:limit]
                    
            except Exception as e:
                # Log specific endpoint failure but continue
                debug_log = DATA_DIR / "debug_search.log"
                try:
                    with open(debug_log, 'a') as f:
                        f.write(f"DuckDuckGo endpoint {endpoint} failed: {str(e)}\n")
                except:
                    pass
                continue
        
        # If we get here, all endpoints failed
        response_time = time.time() - start_time
        log_search_stats(query, 'duckduckgo', False, response_time)
        return []
        
    except Exception as e:
        response_time = time.time() - start_time
        log_search_stats(query, 'duckduckgo', False, response_time)
        
        # Log the error for debugging
        debug_log = DATA_DIR / "debug_search.log"
        try:
            with open(debug_log, 'a') as f:
                f.write(f"DuckDuckGo search failed for '{query}': {str(e)}\n")
        except:
            pass
        
        return []

def search_fallback_google(query, limit=10, timeout=10):
    """Fallback search using Google (basic scraping)."""
    start_time = time.time()
    
    try:
        # Google search URL
        params = urlencode({'q': query, 'num': min(limit, 10)})
        full_url = f"https://www.google.com/search?{params}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        req = Request(full_url, headers=headers)
        
        with urlopen(req, timeout=timeout) as response:
            content = response.read()
            
            if response.headers.get('Content-Encoding') == 'gzip':
                import gzip
                content = gzip.decompress(content)
            
            html_content = content.decode('utf-8', errors='ignore')
        
        results = []
        
        # Parse Google results with multiple patterns
        patterns = [
            r'<h3[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?</h3>.*?<span[^>]*>(.*?)</span>',
            r'<div[^>]*data-ved[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*><h3[^>]*>(.*?)</h3></a>.*?<span[^>]*>(.*?)</span>',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
            if matches:
                for match in matches:
                    url = match[0]
                    title = html.unescape(re.sub(r'<.*?>', '', match[1])).strip()
                    snippet = html.unescape(re.sub(r'<.*?>', '', match[2])).strip()
                    
                    # Clean up Google redirect URLs
                    if url.startswith('/url?q='):
                        url = url.split('/url?q=')[1].split('&')[0]
                    
                    if (url.startswith('http') and title and 
                        'google.com' not in url and len(title) > 3):
                        results.append({
                            'title': title[:200],
                            'url': url,
                            'snippet': snippet[:300],
                            'source': 'google'
                        })
                
                if results:
                    break
        
        response_time = time.time() - start_time
        success = len(results) > 0
        log_search_stats(query, 'google', success, response_time)
        
        return results[:limit]
        
    except Exception as e:
        response_time = time.time() - start_time
        log_search_stats(query, 'google', False, response_time)
        
        debug_log = DATA_DIR / "debug_search.log"
        try:
            with open(debug_log, 'a') as f:
                f.write(f"Google search failed for '{query}': {str(e)}\n")
        except:
            pass
        
        return []

def web_search(query, limit=10, timeout=10, engine='auto'):
    """Perform web search with multiple fallback engines and debug logging."""
    # Check cache first
    cached = get_cached_results(query, engine)
    if cached:
        return cached[:limit]
    
    results = []
    engines_tried = []
    
    # Log search attempt
    debug_log = DATA_DIR / "debug_search.log"
    try:
        with open(debug_log, 'a') as f:
            f.write(f"\n=== SEARCH: '{query}' (engine: {engine}, limit: {limit}) ===\n")
    except:
        pass
    
    if engine == 'duckduckgo':
        engines_tried.append('duckduckgo')
        results = search_duckduckgo(query, limit, timeout)
    elif engine == 'google':
        engines_tried.append('google')
        results = search_fallback_google(query, limit, timeout)
    else:  # auto mode - try multiple engines
        # Try DuckDuckGo first
        engines_tried.append('duckduckgo')
        results = search_duckduckgo(query, limit, timeout)
        
        # If no results, try Google as fallback
        if not results:
            engines_tried.append('google')
            results = search_fallback_google(query, limit, timeout)
        
        # If still no results, try a simple web scraping approach
        if not results:
            engines_tried.append('simple')
            results = search_simple_fallback(query, limit, timeout)
    
    # Log results
    try:
        with open(debug_log, 'a') as f:
            f.write(f"Engines tried: {engines_tried}\n")
            f.write(f"Results found: {len(results)}\n")
            if results:
                f.write(f"First result: {results[0]['title'][:50]}...\n")
            f.write("=== END SEARCH ===\n\n")
    except:
        pass
    
    # Cache results if we got any
    if results:
        cache_results(query, results, engine)
    
    return results

def search_simple_fallback(query, limit=10, timeout=10):
    """Simple fallback search using basic web search."""
    results = []
    
    # Try StartPage (privacy-focused Google proxy)
    try:
        params = urlencode({'q': query})
        url = f"https://www.startpage.com/sp/search?{params}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        req = Request(url, headers=headers)
        with urlopen(req, timeout=timeout) as response:
            html_content = response.read().decode('utf-8', errors='ignore')
        
        # Basic pattern for StartPage results
        pattern = r'<a[^>]*class="[^"]*result-link[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>'
        matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        for match in matches[:limit]:
            url_result = match[0]
            title = html.unescape(re.sub(r'<.*?>', '', match[1])).strip()
            
            if url_result.startswith('http') and title and len(title) > 3:
                results.append({
                    'title': title[:200],
                    'url': url_result,
                    'snippet': '',
                    'source': 'startpage'
                })
        
    except Exception as e:
        debug_log = DATA_DIR / "debug_search.log"
        try:
            with open(debug_log, 'a') as f:
                f.write(f"StartPage search failed: {str(e)}\n")
        except:
            pass
    
    return results

def fetch_url(url, timeout=10):
    """Fetch content from a specific URL."""
    try:
        # Basic URL validation
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return {"error": "Invalid URL format", "success": False}
        
        content = make_request(url, timeout)
        if content:
            # Basic content extraction (remove HTML tags for text content)
            text_content = re.sub(r'<script.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
            text_content = re.sub(r'<style.*?</style>', '', text_content, flags=re.DOTALL | re.IGNORECASE)
            text_content = re.sub(r'<.*?>', '', text_content)
            text_content = html.unescape(text_content)
            
            # Clean up whitespace
            text_content = re.sub(r'\s+', ' ', text_content).strip()
            
            return {
                "url": url,
                "content": text_content[:5000],  # Limit content size
                "content_length": len(content),
                "success": True
            }
        
        return {"error": "Failed to fetch content", "success": False}
        
    except Exception as e:
        return {"error": f"Error fetching URL: {str(e)}", "success": False}

def clear_cache():
    """Clear the search cache."""
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM search_cache")
        deleted = cursor.rowcount
        conn.commit()
    
    return {"cleared_entries": deleted, "success": True}

def get_stats():
    """Get usage statistics."""
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        
        # Total searches
        cursor.execute("SELECT COUNT(*) FROM search_stats")
        total_searches = cursor.fetchone()[0]
        
        # Success rate
        cursor.execute("SELECT COUNT(*) FROM search_stats WHERE success = 1")
        successful_searches = cursor.fetchone()[0]
        
        # Average response time
        cursor.execute("SELECT AVG(response_time) FROM search_stats WHERE success = 1")
        avg_response_time = cursor.fetchone()[0] or 0
        
        # Searches by engine
        cursor.execute("SELECT engine, COUNT(*) FROM search_stats GROUP BY engine")
        engine_stats = dict(cursor.fetchall())
        
        # Cache stats
        cursor.execute("SELECT COUNT(*) FROM search_cache")
        cached_queries = cursor.fetchone()[0]
        
        return {
            "total_searches": total_searches,
            "successful_searches": successful_searches,
            "success_rate": successful_searches / max(total_searches, 1),
            "average_response_time": round(avg_response_time, 2),
            "engine_usage": engine_stats,
            "cached_queries": cached_queries,
            "success": True
        }

def main():
    """Main entry point."""
    init_database()
    
    if len(sys.argv) < 2:
        print("Error: Operation parameters required.", file=sys.stderr)
        sys.exit(1)
    
    try:
        params = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON parameters: {e}", file=sys.stderr)
        sys.exit(1)
    
    operation = params.get("operation")
    if not operation:
        print("Error: 'operation' parameter missing.", file=sys.stderr)
        sys.exit(1)
    
    if operation == "search":
        query = params.get("query")
        if not query:
            print("Error: 'query' required for search operation.", file=sys.stderr)
            sys.exit(1)
        
        limit = params.get("limit", 10)
        timeout = params.get("timeout", 10)
        engine = params.get("engine", "auto")
        
        results = web_search(query, limit, timeout, engine)
        print(json.dumps({
            "query": query,
            "results": results,
            "count": len(results),
            "success": True
        }))
    
    elif operation == "fetch":
        url = params.get("url")
        if not url:
            print("Error: 'url' required for fetch operation.", file=sys.stderr)
            sys.exit(1)
        
        timeout = params.get("timeout", 10)
        result = fetch_url(url, timeout)
        print(json.dumps(result))
    
    elif operation == "clear_cache":
        result = clear_cache()
        print(json.dumps(result))
    
    elif operation == "get_stats":
        result = get_stats()
        print(json.dumps(result, indent=2))
    
    else:
        print(f"Error: Unknown operation '{operation}'", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
