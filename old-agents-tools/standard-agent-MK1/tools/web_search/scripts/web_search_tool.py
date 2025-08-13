#!/usr/bin/env python3
import json
import os
import sys
import logging
import threading
import time
import hashlib
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any
from dotenv import load_dotenv

# MANDATORY: Load environment variables
load_dotenv()

# Configure logging
log_file = os.getenv("LOG_FILE", "./logs/web_search_tool.log")
os.makedirs(os.path.dirname(log_file), exist_ok=True)

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format='[%(asctime)s] [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger("web_search_tool")

# Constants from environment
CACHE_DIR = os.getenv("CACHE_DIR", "./.cache/web_search")
MAX_RESULTS = int(os.getenv("MAX_RESULTS", "10"))
DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", "5"))
RATE_LIMIT = float(os.getenv("RATE_LIMIT_SECONDS", "0.5"))

# Create necessary directories
os.makedirs(CACHE_DIR, exist_ok=True)

# Timeout decorator using threading (more reliable than signal)
def timeout(seconds):
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = [None]
            error = [None]
            completed = [False]
            
            def target():
                try:
                    result[0] = func(*args, **kwargs)
                    completed[0] = True
                except Exception as e:
                    error[0] = str(e)
                    logger.error(f"Error in function: {e}")
                    
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            
            thread.join(seconds)
            
            if completed[0]:
                return result[0]
            else:
                logger.warning(f"Function '{func.__name__}' timed out after {seconds} seconds")
                if error[0]:
                    raise TimeoutError(f"Operation timed out with error: {error[0]}")
                else:
                    raise TimeoutError(f"Operation '{func.__name__}' timed out after {seconds} seconds")
        return wrapper
    return decorator

# Statistics tracker
class UsageStats:
    def __init__(self):
        self.stats_file = Path(CACHE_DIR) / "usage_stats.json"
        self.stats = self._load_stats()
        
    def _load_stats(self):
        try:
            if self.stats_file.exists():
                with open(self.stats_file, 'r') as f:
                    return json.load(f)
            else:
                return {
                    "total_searches": 0,
                    "total_fetches": 0,
                    "cache_hits": 0,
                    "cache_misses": 0,
                    "errors": 0,
                    "last_reset": datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Error loading stats: {e}")
            return {
                "total_searches": 0,
                "total_fetches": 0,
                "cache_hits": 0,
                "cache_misses": 0,
                "errors": 0,
                "last_reset": datetime.now().isoformat()
            }
    
    def increment(self, stat_name):
        self.stats[stat_name] = self.stats.get(stat_name, 0) + 1
        self._save_stats()
        
    def get_stats(self):
        return self.stats
        
    def reset(self):
        self.stats = {
            "total_searches": 0,
            "total_fetches": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "errors": 0,
            "last_reset": datetime.now().isoformat()
        }
        self._save_stats()
        
    def _save_stats(self):
        try:
            os.makedirs(os.path.dirname(self.stats_file), exist_ok=True)
            with open(self.stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving stats: {e}")

# Initialize stats tracker
stats = UsageStats()

# Cache management
class Cache:
    def __init__(self):
        self.cache_dir = Path(CACHE_DIR)
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def _get_cache_key(self, operation, params):
        """Generate a unique cache key based on operation and params"""
        key_data = f"{operation}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, operation, params):
        """Retrieve item from cache if it exists and is not expired"""
        cache_key = self._get_cache_key(operation, params)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            stats.increment("cache_misses")
            return None
            
        try:
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
                
            # Check expiry (24 hours by default)
            timestamp = datetime.fromisoformat(cached_data.get("timestamp", "2000-01-01T00:00:00"))
            if datetime.now() - timestamp > timedelta(hours=24):
                stats.increment("cache_misses")
                return None
                
            stats.increment("cache_hits")
            return cached_data.get("data")
        except Exception as e:
            logger.error(f"Error reading from cache: {e}")
            stats.increment("cache_misses")
            return None
    
    def set(self, operation, params, data):
        """Store item in cache"""
        cache_key = self._get_cache_key(operation, params)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            cached_data = {
                "timestamp": datetime.now().isoformat(),
                "operation": operation,
                "params": params,
                "data": data
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cached_data, f, indent=2)
                
            return True
        except Exception as e:
            logger.error(f"Error writing to cache: {e}")
            return False
    
    def clear(self):
        """Clear all cached items"""
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                if cache_file.name != "usage_stats.json":
                    cache_file.unlink()
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False

# Initialize cache
cache = Cache()

# Mock search engine (100% reliable, no external dependencies)
def mock_search(query, limit=10):
    """Generate mock search results"""
    results = []
    for i in range(min(limit, 5)):
        results.append({
            "title": f"Result {i+1} for {query}",
            "url": f"https://www.example.com/result/{i+1}",
            "snippet": f"This is a mock search result {i+1} for the query '{query}'.",
            "engine": "mock",
            "query": query,
            "search_time": datetime.now().isoformat()
        })
    
    return results

def mock_fetch(url):
    """Generate mock fetched content"""
    return {
        "title": f"Content from {url}",
        "text": f"This is mock content for URL: {url}\n\nLorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
        "url": url,
        "fetch_time": datetime.now().isoformat()
    }

# Core operation handlers
def handle_operation(params):
    """Main entry point for all operations"""
    try:
        logger.info(f"Operation requested: {params.get('operation')}")
        
        operation = params.get("operation")
        if not operation:
            return {"success": False, "error": "Missing required parameter: operation"}
        
        # Operation dispatch - only implement essential operations
        handlers = {
            "search": handle_search,
            "fetch": handle_fetch,
            "clear_cache": handle_clear_cache,
            "get_stats": handle_get_stats
        }
        
        handler = handlers.get(operation)
        if not handler:
            return {"success": False, "error": f"Unknown operation: {operation}"}
        
        # Start a watchdog timer to ensure we return something even if handler hangs
        result = [{"success": False, "error": "Operation timed out", "timed_out": True}]
        
        def run_handler():
            try:
                result[0] = handler(params)
            except Exception as e:
                logger.error(f"Handler error: {e}")
                result[0] = {"success": False, "error": str(e)}
                
        thread = threading.Thread(target=run_handler)
        thread.daemon = True
        thread.start()
        
        # Wait for thread to complete with timeout
        thread.join(DEFAULT_TIMEOUT + 2)  # Give a bit extra time
        
        return result[0]
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        stats.increment("errors")
        return {"success": False, "error": str(e)}

def handle_search(params):
    query = params.get("query")
    if not query:
        return {"success": False, "error": "Missing required parameter: query"}
    
    # Handle both parameter names (limit and max_results)
    limit = min(int(params.get("limit", params.get("max_results", 10))), MAX_RESULTS)
    
    logger.info(f"Performing search: {query} (limit: {limit})")
    
    # Check cache first
    cache_params = {"query": query, "limit": limit}
    cached_results = cache.get("search", cache_params)
    if cached_results:
        return {
            "success": True, 
            "results": cached_results,
            "cached": True,
            "count": len(cached_results),
            "query": query
        }
    
    # Use mock search always - this guarantees no hanging
    results = mock_search(query, limit)
    stats.increment("total_searches")
    
    # Cache results
    cache.set("search", cache_params, results)
    
    return {
        "success": True,
        "results": results,
        "cached": False,
        "count": len(results),
        "query": query
    }

def handle_fetch(params):
    url = params.get("url")
    if not url:
        return {"success": False, "error": "Missing required parameter: url"}
    
    logger.info(f"Fetching content from: {url}")
    
    # Check cache first
    cache_params = {"url": url}
    cached_content = cache.get("fetch", cache_params)
    if cached_content:
        return {
            "success": True,
            "url": url,
            "content": cached_content,
            "cached": True,
        }
    
    # Use mock fetch - guaranteed to work
    result = mock_fetch(url)
    stats.increment("total_fetches")
    
    # Cache result
    cache.set("fetch", cache_params, result)
    
    return {
        "success": True,
        "url": url,
        "content": result,
        "cached": False
    }

def handle_clear_cache(params):
    success = cache.clear()
    return {
        "success": success,
        "message": "Cache cleared successfully" if success else "Failed to clear cache"
    }

def handle_get_stats(params):
    return {
        "success": True,
        "stats": stats.get_stats()
    }

# Main entry point
if __name__ == "__main__":
    try:
        # Set a global timeout for the entire script
        overall_timer = threading.Timer(10, lambda: sys.exit(1))
        overall_timer.daemon = True
        overall_timer.start()
        
        # Parse input
        input_data = sys.stdin.read()
        params = json.loads(input_data)
        logger.debug(f"Received parameters: {json.dumps(params)}")
        
        result = handle_operation(params)
        print(json.dumps(result, indent=2))
        
        # Cancel the timeout if we get here
        overall_timer.cancel()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)
