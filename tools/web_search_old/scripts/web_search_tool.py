#!/usr/bin/env python3
"""
Web Search Tool for Chimera Ecosystem
Fixed version with proper error handling and working search engines
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
import gzip
import io

# Configuration
DATA_DIR = Path(os.getenv("AGENT_WORKSPACE", ".")) / ".data"
DB_PATH = DATA_DIR / "web_search.db"
CACHE_DURATION = 3600  # 1 hour cache
MAX_RETRIES = 2
USER_AGENTS = [
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
]

def ensure_data_dir():
    """Create the data directory if it doesn't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

def init_database():
    """Initialize the database with required tables."""
    ensure_data_dir()
    try:
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
    except Exception as e:
        debug_log(f"Database init error: {e}")

def debug_log(message):
    """Simple debug logging."""
    try:
        ensure_data_dir()
        with open(DATA_DIR / "debug.log", "a") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
    except:
        pass

def get_query_hash(query, engine=""):
    """Generate a hash for cache key."""
    return hashlib.md5(f"{query}:{engine}".encode()).hexdigest()

def get_cached_results(query, engine=""):
    """Retrieve cached search results if they exist and are fresh."""
    try:
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
    except Exception as e:
        debug_log(f"Cache read error: {e}")
    
    return None

def cache_results(query, results, engine=""):
    """Cache search results."""
    try:
        query_hash = get_query_hash(query, engine)
        current_time = int(time.time())
        
        with sqlite3.connect(str(DB_PATH)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO search_cache (query_hash, query, results, timestamp, engine) VALUES (?, ?, ?, ?, ?)",
                (query_hash, query, json.dumps(results), current_time, engine)
            )
            conn.commit()
    except Exception as e:
        debug_log(f"Cache write error: {e}")

def log_search_stats(query, engine, success, response_time):
    """Log search statistics."""
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO search_stats (query, engine, timestamp, success, response_time) VALUES (?, ?, ?, ?, ?)",
                (query, engine, int(time.time()), success, response_time)
            )
            conn.commit()
    except Exception as e:
        debug_log(f"Stats log error: {e}")

def make_request(url, timeout=15, user_agent_index=0):
    """Make HTTP request with proper headers and encoding handling."""
    headers = {
        'User-Agent': USER_AGENTS[user_agent_index % len(USER_AGENTS)],
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }
    
    req = Request(url, headers=headers)
    
    for attempt in range(MAX_RETRIES):
        try:
            with urlopen(req, timeout=timeout) as response:
                content = response.read()
                
                # Handle gzip encoding
                if response.headers.get('Content-Encoding') == 'gzip':
                    content = gzip.decompress(content)
                
                return content.decode('utf-8', errors='ignore')
                
        except (URLError, HTTPError) as e:
            debug_log(f"Request attempt {attempt + 1} failed for {url}: {e}")
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(1 * (attempt + 1))
    
    return None

def search_bing(query, limit=10, timeout=15):
    """Search using Bing (most reliable for scraping)."""
    start_time = time.time()
    results = []
    
    try:
        # Bing search URL
        params = urlencode({
            'q': query,
            'count': min(limit, 50),
            'first': 1,
            'FORM': 'PERE'
        })
        url = f"https://www.bing.com/search?{params}"
        
        debug_log(f"Searching Bing: {url}")
        content = make_request(url, timeout)
        
        if not content:
            debug_log("No content received from Bing")
            return []
        
        # Parse Bing results with improved regex
        # Pattern for Bing's current HTML structure
        pattern = r'<h2><a href="([^"]+)"[^>]*>([^<]+)</a></h2>.*?<p[^>]*>([^<]*(?:<[^>]+>[^<]*)*)</p>'
        matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
        
        if not matches:
            # Fallback pattern for different Bing layouts
            pattern = r'<a[^>]*href="([^"]+)"[^>]*><h2[^>]*>([^<]+)</h2></a>.*?<p[^>]*class="[^"]*snippet[^"]*"[^>]*>([^<]*)</p>'
            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
        
        if not matches:
            # Most basic pattern - just get any results
            pattern = r'href="(https?://[^"]+)"[^>]*>([^<]+)</a>'
            matches = re.findall(pattern, content)
            matches = [(url, title, '') for url, title in matches if 'bing.com' not in url and 'microsoft.com' not in url]
        
        debug_log(f"Bing matches found: {len(matches)}")
        
        for match in matches[:limit]:
            if len(match) >= 2:
                url_result = match[0]
                title = html.unescape(re.sub(r'<.*?>', '', match[1])).strip()
                snippet = html.unescape(re.sub(r'<.*?>', '', match[2] if len(match) > 2 else '')).strip()
                
                # Clean up URLs and filter out unwanted results
                if (url_result.startswith('http') and 
                    title and len(title) > 3 and
                    'bing.com' not in url_result and
                    'microsoft.com' not in url_result):
                    
                    results.append({
                        'title': title[:200],
                        'url': url_result,
                        'snippet': snippet[:300],
                        'source': 'bing'
                    })
        
        response_time = time.time() - start_time
        success = len(results) > 0
        log_search_stats(query, 'bing', success, response_time)
        
        debug_log(f"Bing search completed: {len(results)} results in {response_time:.2f}s")
        return results
        
    except Exception as e:
        response_time = time.time() - start_time
        log_search_stats(query, 'bing', False, response_time)
        debug_log(f"Bing search failed: {e}")
        return []

def search_duckduckgo_lite(query, limit=10, timeout=15):
    """Search using DuckDuckGo Lite (simpler, more reliable)."""
    start_time = time.time()
    results = []
    
    try:
        # Use DuckDuckGo Lite which has simpler HTML
        params = urlencode({
            'q': query,
            'kl': 'us-en'
        })
        url = f"https://lite.duckduckgo.com/lite/?{params}"
        
        debug_log(f"Searching DuckDuckGo Lite: {url}")
        content = make_request(url, timeout)
        
        if not content:
            debug_log("No content received from DuckDuckGo Lite")
            return []
        
        # Parse DuckDuckGo Lite results (simpler structure)
        # Look for result links in the lite interface
        pattern = r'<a rel="nofollow" href="([^"]+)">([^<]+)</a>'
        matches = re.findall(pattern, content)
        
        debug_log(f"DuckDuckGo Lite matches found: {len(matches)}")
        
        for match in matches[:limit]:
            url_result, title = match
            title = html.unescape(title).strip()
            
            if (url_result.startswith('http') and 
                title and len(title) > 3 and
                'duckduckgo.com' not in url_result):
                
                results.append({
                    'title': title[:200],
                    'url': url_result,
                    'snippet': '',
                    'source': 'duckduckgo'
                })
        
        response_time = time.time() - start_time
        success = len(results) > 0
        log_search_stats(query, 'duckduckgo', success, response_time)
        
        debug_log(f"DuckDuckGo search completed: {len(results)} results in {response_time:.2f}s")
        return results
        
    except Exception as e:
        response_time = time.time() - start_time
        log_search_stats(query, 'duckduckgo', False, response_time)
        debug_log(f"DuckDuckGo search failed: {e}")
        return []

def search_searx(query, limit=10, timeout=15):
    """Search using Searx instances."""
    start_time = time.time()
    results = []
    
    # List of public Searx instances
    instances = [
        'https://searx.be',
        'https://search.sapti.me',
        'https://searx.tiekoetter.com',
        'https://searx.org'
    ]
    
    for instance in instances:
        try:
            params = urlencode({
                'q': query,
                'format': 'json',
                'categories': 'general'
            })
            url = f"{instance}/search?{params}"
            
            debug_log(f"Trying Searx instance: {url}")
            content = make_request(url, timeout)
            
            if content:
                data = json.loads(content)
                for result in data.get('results', []):
                    if result.get('url') and result.get('title'):
                        results.append({
                            'title': result.get('title', '')[:200],
                            'url': result.get('url', ''),
                            'snippet': result.get('content', '')[:300],
                            'source': 'searx'
                        })
                
                if results:
                    break  # Success with this instance
                    
        except Exception as e:
            debug_log(f"Searx instance {instance} failed: {e}")
            continue
    
    response_time = time.time() - start_time
    success = len(results) > 0
    log_search_stats(query, 'searx', success, response_time)
    
    debug_log(f"Searx search completed: {len(results)} results in {response_time:.2f}s")
    return results[:limit]

def web_search(query, limit=10, timeout=15, engine='auto'):
    """Perform web search with multiple engines and proper fallback."""
    debug_log(f"Starting search for: '{query}' (engine: {engine}, limit: {limit})")
    
    # Check cache first
    cached = get_cached_results(query, engine)
    if cached:
        debug_log(f"Returning {len(cached)} cached results")
        return cached[:limit]
    
    results = []
    engines_tried = []
    
    if engine == 'bing':
        engines_tried.append('bing')
        results = search_bing(query, limit, timeout)
    elif engine == 'duckduckgo':
        engines_tried.append('duckduckgo')
        results = search_duckduckgo_lite(query, limit, timeout)
    elif engine == 'searx':
        engines_tried.append('searx')
        results = search_searx(query, limit, timeout)
    else:  # auto mode
        # Try engines in order of reliability
        engines_tried.append('bing')
        results = search_bing(query, limit, timeout)
        
        if not results:
            engines_tried.append('duckduckgo')
            results = search_duckduckgo_lite(query, limit, timeout)
        
        if not results:
            engines_tried.append('searx')
            results = search_searx(query, limit, timeout)
    
    debug_log(f"Search completed. Engines tried: {engines_tried}, Results: {len(results)}")
    
    # Cache results if we got any
    if results:
        cache_results(query, results, engine)
    
    return results

def fetch_url(url, timeout=15):
    """Fetch content from a specific URL with better text extraction."""
    try:
        # Validate URL
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return {"error": "Invalid URL format", "success": False}
        
        debug_log(f"Fetching URL: {url}")
        content = make_request(url, timeout)
        
        if not content:
            return {"error": "Failed to fetch content", "success": False}
        
        # Extract text content
        # Remove script and style tags
        text_content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
        text_content = re.sub(r'<style[^>]*>.*?</style>', '', text_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove HTML tags
        text_content = re.sub(r'<[^>]+>', ' ', text_content)
        
        # Decode HTML entities
        text_content = html.unescape(text_content)
        
        # Clean up whitespace
        text_content = re.sub(r'\s+', ' ', text_content).strip()
        
        # Limit content size
        max_length = 5000
        if len(text_content) > max_length:
            text_content = text_content[:max_length] + "..."
        
        return {
            "url": url,
            "content": text_content,
            "content_length": len(content),
            "text_length": len(text_content),
            "success": True
        }
        
    except Exception as e:
        debug_log(f"URL fetch error: {e}")
        return {"error": f"Error fetching URL: {str(e)}", "success": False}

def clear_cache():
    """Clear the search cache."""
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM search_cache")
            deleted = cursor.rowcount
            conn.commit()
        
        debug_log(f"Cache cleared: {deleted} entries")
        return {"cleared_entries": deleted, "success": True}
    except Exception as e:
        debug_log(f"Cache clear error: {e}")
        return {"error": str(e), "success": False}

def get_stats():
    """Get usage statistics."""
    try:
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
    except Exception as e:
        debug_log(f"Stats error: {e}")
        return {"error": str(e), "success": False}

def main():
    """Main entry point with better error handling."""
    try:
        init_database()
        
        if len(sys.argv) < 2:
            print(json.dumps({"error": "Operation parameters required", "success": False}))
            sys.exit(1)
        
        try:
            params = json.loads(sys.argv[1])
        except json.JSONDecodeError as e:
            print(json.dumps({"error": f"Invalid JSON parameters: {e}", "success": False}))
            sys.exit(1)
        
        operation = params.get("operation")
        if not operation:
            print(json.dumps({"error": "'operation' parameter missing", "success": False}))
            sys.exit(1)
        
        debug_log(f"Operation: {operation}, Params: {params}")
        
        if operation == "search":
            query = params.get("query")
            if not query:
                print(json.dumps({"error": "'query' required for search operation", "success": False}))
                sys.exit(1)
            
            limit = params.get("limit", 10)
            timeout = params.get("timeout", 15)
            engine = params.get("engine", "auto")
            
            results = web_search(query, limit, timeout, engine)
            response = {
                "query": query,
                "results": results,
                "count": len(results),
                "success": True
            }
            print(json.dumps(response))
        
        elif operation == "fetch":
            url = params.get("url")
            if not url:
                print(json.dumps({"error": "'url' required for fetch operation", "success": False}))
                sys.exit(1)
            
            timeout = params.get("timeout", 15)
            result = fetch_url(url, timeout)
            print(json.dumps(result))
        
        elif operation == "clear_cache":
            result = clear_cache()
            print(json.dumps(result))
        
        elif operation == "get_stats":
            result = get_stats()
            print(json.dumps(result, indent=2))
        
        else:
            print(json.dumps({"error": f"Unknown operation '{operation}'", "success": False}))
            sys.exit(1)
            
    except Exception as e:
        debug_log(f"Main error: {e}")
        print(json.dumps({"error": f"Unexpected error: {str(e)}", "success": False}))
        sys.exit(1)

if __name__ == "__main__":
    main()
