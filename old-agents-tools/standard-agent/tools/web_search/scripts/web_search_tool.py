#!/usr/bin/env python3
import json
import os
import sys
import logging
import requests
import hashlib
import time
import re
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlencode, quote_plus
from typing import Dict, List, Any, Optional
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
SOURCES_DIR = os.getenv("SOURCES_DIR", "./.sources")
CACHE_EXPIRY = int(os.getenv("CACHE_EXPIRY_HOURS", "24"))
MAX_RESULTS = int(os.getenv("MAX_RESULTS", "20"))
DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", "10"))
USER_AGENT = os.getenv("USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
RATE_LIMIT = int(os.getenv("RATE_LIMIT_SECONDS", "2"))
DEFAULT_ENGINE = os.getenv("DEFAULT_ENGINE", "auto")

# Error classes
class WebSearchError(Exception):
    """Base error for web search operations"""
    pass

class RequestError(WebSearchError):
    """Error during HTTP request"""
    pass

class ParsingError(WebSearchError):
    """Error during content parsing"""
    pass

class ValidationError(WebSearchError):
    """Error during parameter validation"""
    pass

class FileError(WebSearchError):
    """Error during file operations"""
    pass

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
                    "sources_aggregated": 0,
                    "sources_exported": 0,
                    "sources_imported": 0,
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
                "sources_aggregated": 0,
                "sources_exported": 0,
                "sources_imported": 0,
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
            "sources_aggregated": 0,
            "sources_exported": 0,
            "sources_imported": 0,
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
                
            # Check expiry
            timestamp = datetime.fromisoformat(cached_data.get("timestamp", "2000-01-01T00:00:00"))
            if datetime.now() - timestamp > timedelta(hours=CACHE_EXPIRY):
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

# Source management
class SourceManager:
    def __init__(self):
        self.sources_dir = Path(SOURCES_DIR)
        os.makedirs(self.sources_dir, exist_ok=True)
        self.collections_file = self.sources_dir / "collections.json"
        self.collections = self._load_collections()
        
    def _load_collections(self):
        """Load existing source collections"""
        try:
            if self.collections_file.exists():
                with open(self.collections_file, 'r') as f:
                    return json.load(f)
            else:
                return {}
        except Exception as e:
            logger.error(f"Error loading source collections: {e}")
            return {}
    
    def _save_collections(self):
        """Save source collections index"""
        try:
            with open(self.collections_file, 'w') as f:
                json.dump(self.collections, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving source collections: {e}")
            return False
    
    def create_collection(self, name, description=None):
        """Create a new source collection"""
        collection_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        self.collections[collection_id] = {
            "id": collection_id,
            "name": name,
            "description": description,
            "created_at": timestamp,
            "updated_at": timestamp,
            "source_count": 0,
            "file": f"{collection_id}.json"
        }
        
        # Create empty collection file
        collection_file = self.sources_dir / f"{collection_id}.json"
        with open(collection_file, 'w') as f:
            json.dump({
                "id": collection_id,
                "name": name,
                "description": description,
                "created_at": timestamp,
                "updated_at": timestamp,
                "sources": []
            }, f, indent=2)
        
        self._save_collections()
        return collection_id
    
    def get_collections(self):
        """Get all source collections"""
        return self.collections
    
    def get_collection(self, collection_id):
        """Get a specific collection by ID"""
        if collection_id not in self.collections:
            return None
        
        try:
            collection_file = self.sources_dir / f"{collection_id}.json"
            with open(collection_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading collection {collection_id}: {e}")
            return None
    
    def add_source(self, collection_id, source):
        """Add a source to a collection"""
        if collection_id not in self.collections:
            return False
        
        try:
            collection_file = self.sources_dir / f"{collection_id}.json"
            
            # Load current collection
            with open(collection_file, 'r') as f:
                collection = json.load(f)
            
            # Add source with metadata
            source_id = str(uuid.uuid4())
            source_with_meta = {
                "id": source_id,
                "added_at": datetime.now().isoformat(),
                "data": source
            }
            
            collection["sources"].append(source_with_meta)
            collection["updated_at"] = datetime.now().isoformat()
            
            # Update collection file
            with open(collection_file, 'w') as f:
                json.dump(collection, f, indent=2)
            
            # Update collection index
            self.collections[collection_id]["source_count"] = len(collection["sources"])
            self.collections[collection_id]["updated_at"] = collection["updated_at"]
            self._save_collections()
            
            return source_id
        except Exception as e:
            logger.error(f"Error adding source to collection {collection_id}: {e}")
            return False
    
    def export_collection(self, collection_id, output_path=None):
        """Export a collection to a specific file path"""
        if collection_id not in self.collections:
            return False
        
        try:
            collection = self.get_collection(collection_id)
            if not collection:
                return False
            
            # If no output path provided, create one based on collection name
            if not output_path:
                sanitized_name = re.sub(r'[^\w\-_]', '_', collection["name"])
                output_path = f"{sanitized_name}_{datetime.now().strftime('%Y%m%d')}.json"
            
            with open(output_path, 'w') as f:
                json.dump(collection, f, indent=2)
            
            return output_path
        except Exception as e:
            logger.error(f"Error exporting collection {collection_id}: {e}")
            return False
    
    def import_collection(self, file_path, new_name=None):
        """Import a collection from a file"""
        try:
            with open(file_path, 'r') as f:
                imported = json.load(f)
            
            # Validate imported data
            if not isinstance(imported, dict) or "sources" not in imported:
                raise ValidationError("Invalid collection format")
            
            # Create new collection with imported data
            collection_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()
            
            # Use provided name or original name
            name = new_name or imported.get("name", f"Imported {timestamp}")
            description = imported.get("description", f"Imported from {file_path}")
            
            # Create collection entry
            self.collections[collection_id] = {
                "id": collection_id,
                "name": name,
                "description": description,
                "created_at": timestamp,
                "updated_at": timestamp,
                "source_count": len(imported["sources"]),
                "file": f"{collection_id}.json"
            }
            
            # Create collection file
            collection_file = self.sources_dir / f"{collection_id}.json"
            
            # Preserve source IDs if possible, but ensure all sources have IDs
            sources = []
            for source in imported["sources"]:
                if isinstance(source, dict):
                    if "id" not in source:
                        source["id"] = str(uuid.uuid4())
                    if "added_at" not in source:
                        source["added_at"] = timestamp
                    sources.append(source)
                else:
                    # Handle case where source is not properly formatted
                    sources.append({
                        "id": str(uuid.uuid4()),
                        "added_at": timestamp,
                        "data": source
                    })
            
            # Create collection with imported sources
            with open(collection_file, 'w') as f:
                json.dump({
                    "id": collection_id,
                    "name": name,
                    "description": description,
                    "created_at": timestamp,
                    "updated_at": timestamp,
                    "imported_from": file_path,
                    "sources": sources
                }, f, indent=2)
            
            self._save_collections()
            return collection_id
        except Exception as e:
            logger.error(f"Error importing collection from {file_path}: {e}")
            return False
    
    def delete_collection(self, collection_id):
        """Delete a collection"""
        if collection_id not in self.collections:
            return False
        
        try:
            # Delete collection file
            collection_file = self.sources_dir / f"{collection_id}.json"
            if collection_file.exists():
                collection_file.unlink()
            
            # Remove from collections index
            del self.collections[collection_id]
            self._save_collections()
            
            return True
        except Exception as e:
            logger.error(f"Error deleting collection {collection_id}: {e}")
            return False

# Initialize source manager
source_manager = SourceManager()

# Request helpers
def make_request(url, timeout=DEFAULT_TIMEOUT):
    """Make HTTP request with proper headers and error handling"""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logger.error(f"Request error for {url}: {e}")
        stats.increment("errors")
        raise RequestError(f"Failed to fetch content from {url}: {str(e)}")

# Search engines
class SearchEngine:
    """Base class for search engines"""
    
    def __init__(self, timeout=DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Enforce rate limiting between requests"""
        now = time.time()
        elapsed = now - self.last_request_time
        
        if elapsed < RATE_LIMIT:
            time.sleep(RATE_LIMIT - elapsed)
            
        self.last_request_time = time.time()
    
    def search(self, query, limit=10):
        """Perform search and return results"""
        raise NotImplementedError("Each search engine must implement this method")

class DuckDuckGoSearch(SearchEngine):
    def search(self, query, limit=10):
        self._rate_limit()
        
        # Build search URL
        search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        
        try:
            html_content = make_request(search_url, self.timeout)
            
            # Parse results
            soup = BeautifulSoup(html_content, 'html.parser')
            results = []
            
            for result in soup.select('.result'):
                title_elem = result.select_one('.result__title')
                link_elem = result.select_one('.result__url')
                snippet_elem = result.select_one('.result__snippet')
                
                if title_elem and link_elem:
                    title = title_elem.get_text().strip()
                    href = link_elem.get_text().strip()
                    
                    # Normalize URL if needed
                    if not href.startswith(('http://', 'https://')):
                        href = f"https://{href}"
                        
                    snippet = snippet_elem.get_text().strip() if snippet_elem else ""
                    
                    results.append({
                        "title": title,
                        "url": href,
                        "snippet": snippet,
                        "engine": "duckduckgo",
                        "query": query,
                        "search_time": datetime.now().isoformat()
                    })
                    
                    if len(results) >= limit:
                        break
            
            return results
        except Exception as e:
            logger.error(f"Error searching DuckDuckGo: {e}")
            stats.increment("errors")
            raise ParsingError(f"Failed to parse DuckDuckGo results: {str(e)}")

class SearXSearch(SearchEngine):
    def search(self, query, limit=10):
        self._rate_limit()
        
        # Use a public SearX instance
        search_url = f"https://searx.be/search?q={quote_plus(query)}&format=html"
        
        try:
            html_content = make_request(search_url, self.timeout)
            
            # Parse results
            soup = BeautifulSoup(html_content, 'html.parser')
            results = []
            
            for result in soup.select('.result'):
                title_elem = result.select_one('.result_header a')
                url_elem = result.select_one('.result_header a')
                snippet_elem = result.select_one('.result-content')
                
                if title_elem and url_elem:
                    title = title_elem.get_text().strip()
                    href = url_elem.get('href', '')
                    snippet = snippet_elem.get_text().strip() if snippet_elem else ""
                    
                    results.append({
                        "title": title,
                        "url": href,
                        "snippet": snippet,
                        "engine": "searx",
                        "query": query,
                        "search_time": datetime.now().isoformat()
                    })
                    
                    if len(results) >= limit:
                        break
            
            return results
        except Exception as e:
            logger.error(f"Error searching SearX: {e}")
            stats.increment("errors")
            raise ParsingError(f"Failed to parse SearX results: {str(e)}")

# Core operation handlers
def handle_operation(params):
    """Main entry point for all operations"""
    try:
        operation = params.get("operation")
        if not operation:
            raise ValidationError("Missing required parameter: operation")
        
        # Operation dispatch
        handlers = {
            "search": handle_search,
            "fetch": handle_fetch,
            "clear_cache": handle_clear_cache,
            "get_stats": handle_get_stats,
            "create_collection": handle_create_collection,
            "list_collections": handle_list_collections,
            "get_collection": handle_get_collection,
            "add_to_collection": handle_add_to_collection,
            "aggregate_sources": handle_aggregate_sources,
            "export_sources": handle_export_sources,
            "import_sources": handle_import_sources,
            "delete_collection": handle_delete_collection
        }
        
        handler = handlers.get(operation)
        if not handler:
            raise ValidationError(f"Unknown operation: {operation}")
        
        return handler(params)
    except WebSearchError as e:
        logger.error(f"Operation failed: {e}")
        stats.increment("errors")
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        stats.increment("errors")
        return {"success": False, "error": f"Unexpected error: {str(e)}"}

def handle_search(params):
    query = params.get("query")
    if not query:
        raise ValidationError("Missing required parameter: query")
    
    limit = min(int(params.get("limit", 10)), MAX_RESULTS)
    timeout = int(params.get("timeout", DEFAULT_TIMEOUT))
    engine = params.get("engine", DEFAULT_ENGINE)
    
    logger.info(f"Performing search: {query} (engine: {engine}, limit: {limit})")
    
    # Check cache first
    cache_params = {"query": query, "limit": limit, "engine": engine}
    cached_results = cache.get("search", cache_params)
    if cached_results:
        return {
            "success": True, 
            "results": cached_results,
            "cached": True,
            "count": len(cached_results)
        }
    
    # Select engine
    if engine == "duckduckgo" or (engine == "auto" and query):
        search_engine = DuckDuckGoSearch(timeout=timeout)
    elif engine == "searx":
        search_engine = SearXSearch(timeout=timeout)
    else:
        search_engine = DuckDuckGoSearch(timeout=timeout)
    
    # Perform search
    results = search_engine.search(query, limit=limit)
    stats.increment("total_searches")
    
    # Cache results
    cache.set("search", cache_params, results)
    
    return {
        "success": True,
        "results": results,
        "cached": False,
        "count": len(results)
    }

def handle_fetch(params):
    url = params.get("url")
    if not url:
        raise ValidationError("Missing required parameter: url")
    
    # Validate URL
    parsed_url = urlparse(url)
    if not all([parsed_url.scheme, parsed_url.netloc]):
        raise ValidationError(f"Invalid URL: {url}")
    
    timeout = int(params.get("timeout", DEFAULT_TIMEOUT))
    
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
    
    # Fetch content
    try:
        content = make_request(url, timeout)
        stats.increment("total_fetches")
        
        # Parse content with BeautifulSoup for better text extraction
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract useful content
        title = soup.title.string if soup.title else ""
        
        # Strip scripts and styles
        for script in soup(["script", "style"]):
            script.extract()
            
        # Get text content
        text = soup.get_text(separator="\n")
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = "\n".join(chunk for chunk in chunks if chunk)
        
        result = {
            "title": title,
            "text": text[:5000],  # Limit text length
            "url": url,
            "fetch_time": datetime.now().isoformat()
        }
        
        # Cache result
        cache.set("fetch", cache_params, result)
        
        return {
            "success": True,
            "url": url,
            "content": result,
            "cached": False
        }
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        stats.increment("errors")
        raise RequestError(f"Failed to fetch content from {url}: {str(e)}")

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

def handle_create_collection(params):
    name = params.get("name")
    if not name:
        raise ValidationError("Missing required parameter: name")
    
    description = params.get("description", f"Collection created on {datetime.now().isoformat()}")
    
    collection_id = source_manager.create_collection(name, description)
    if not collection_id:
        raise FileError("Failed to create collection")
    
    return {
        "success": True,
        "collection_id": collection_id,
        "name": name
    }

def handle_list_collections(params):
    collections = source_manager.get_collections()
    return {
        "success": True,
        "collections": collections
    }

def handle_get_collection(params):
    collection_id = params.get("collection_id")
    if not collection_id:
        raise ValidationError("Missing required parameter: collection_id")
    
    collection = source_manager.get_collection(collection_id)
    if not collection:
        raise FileError(f"Collection not found: {collection_id}")
    
    return {
        "success": True,
        "collection": collection
    }

def handle_add_to_collection(params):
    collection_id = params.get("collection_id")
    if not collection_id:
        raise ValidationError("Missing required parameter: collection_id")
    
    source = params.get("source")
    if not source:
        raise ValidationError("Missing required parameter: source")
    
    source_id = source_manager.add_source(collection_id, source)
    if not source_id:
        raise FileError(f"Failed to add source to collection: {collection_id}")
    
    return {
        "success": True,
        "collection_id": collection_id,
        "source_id": source_id
    }

def handle_aggregate_sources(params):
    query = params.get("query")
    if not query:
        raise ValidationError("Missing required parameter: query")
    
    collection_name = params.get("collection_name", f"Collection for '{query}'")
    limit = min(int(params.get("limit", 10)), MAX_RESULTS)
    fetch_content = params.get("fetch_content", False)
    
    # Create a new collection for the query
    collection_id = source_manager.create_collection(
        collection_name, 
        f"Aggregated sources for query: {query}"
    )
    
    if not collection_id:
        raise FileError("Failed to create collection for aggregated sources")
    
    # Perform the search
    search_result = handle_search({
        "operation": "search",
        "query": query,
        "limit": limit
    })
    
    if not search_result["success"]:
        source_manager.delete_collection(collection_id)
        raise WebSearchError(f"Search failed: {search_result.get('error')}")
    
    # Add search results to the collection
    results = search_result["results"]
    added_sources = []
    
    for result in results:
        # If fetch_content is True, fetch the content for each result
        if fetch_content:
            try:
                fetch_result = handle_fetch({
                    "operation": "fetch",
                    "url": result["url"],
                    "timeout": DEFAULT_TIMEOUT
                })
                
                if fetch_result["success"]:
                    result["content"] = fetch_result["content"]
            except Exception as e:
                logger.warning(f"Failed to fetch content for {result['url']}: {e}")
        
        # Add the result to the collection
        source_id = source_manager.add_source(collection_id, result)
        if source_id:
            added_sources.append({
                "source_id": source_id,
                "title": result["title"],
                "url": result["url"]
            })
    
    stats.increment("sources_aggregated")
    
    return {
        "success": True,
        "collection_id": collection_id,
        "collection_name": collection_name,
        "sources_added": len(added_sources),
        "sources": added_sources
    }

def handle_export_sources(params):
    collection_id = params.get("collection_id")
    if not collection_id:
        raise ValidationError("Missing required parameter: collection_id")
    
    output_path = params.get("output_path")
    
    result = source_manager.export_collection(collection_id, output_path)
    if not result:
        raise FileError(f"Failed to export collection: {collection_id}")
    
    stats.increment("sources_exported")
    
    return {
        "success": True,
        "collection_id": collection_id,
        "exported_to": result
    }

def handle_import_sources(params):
    file_path = params.get("file_path")
    if not file_path:
        raise ValidationError("Missing required parameter: file_path")
    
    new_name = params.get("new_name")
    
    collection_id = source_manager.import_collection(file_path, new_name)
    if not collection_id:
        raise FileError(f"Failed to import collection from: {file_path}")
    
    collection = source_manager.get_collection(collection_id)
    stats.increment("sources_imported")
    
    return {
        "success": True,
        "collection_id": collection_id,
        "name": collection["name"],
        "sources_count": len(collection["sources"])
    }

def handle_delete_collection(params):
    collection_id = params.get("collection_id")
    if not collection_id:
        raise ValidationError("Missing required parameter: collection_id")
    
    success = source_manager.delete_collection(collection_id)
    if not success:
        raise FileError(f"Failed to delete collection: {collection_id}")
    
    return {
        "success": True,
        "collection_id": collection_id,
        "message": f"Collection {collection_id} deleted successfully"
    }

# Main entry point
if __name__ == "__main__":
    try:
        # Ensure directories exist
        os.makedirs(CACHE_DIR, exist_ok=True)
        os.makedirs(SOURCES_DIR, exist_ok=True)
        
        # Parse input
        params = json.loads(sys.stdin.read())
        result = handle_operation(params)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)
