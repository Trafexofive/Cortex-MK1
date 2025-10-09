# Web Scraper Tool

**Web page fetching for web_researcher agent**

## Overview

Fetches web page content with proper headers and error handling. Local tool for the web_researcher agent.

## Features

- HTTP/HTTPS page fetching
- Custom User-Agent support
- Timeout configuration
- Status code handling
- Error handling for network issues

## Usage

```bash
# Fetch a web page
python3 scripts/web_scraper.py '{"url": "https://example.com"}'

# With custom timeout
python3 scripts/web_scraper.py '{
  "url": "https://example.com",
  "timeout": 60,
  "user_agent": "CustomBot/1.0"
}'

# Health check
python3 scripts/web_scraper.py --health-check
```

## Output

```json
{
  "success": true,
  "url": "https://example.com",
  "status_code": 200,
  "content": "HTML content...",
  "content_length": 1234,
  "headers": {...}
}
```

## Production Integration

For production use, integrate with:
- **requests** - More robust HTTP library
- **scrapy** - Full-featured web scraping framework
- **httpx** - Async HTTP support

Install dependencies:
```bash
pip install requests scrapy httpx
```

## Current Implementation

Uses Python's built-in urllib for simple HTTP fetching. Replace with requests or scrapy for production use.

## Manifest

- **Path:** `agents/research_orchestrator/agents/web_researcher/tools/web_scraper/tool.yml`
- **Version:** 1.0
- **State:** stable
- **Local to:** web_researcher agent
