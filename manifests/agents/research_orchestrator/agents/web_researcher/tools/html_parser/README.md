# HTML Parser Tool

**HTML parsing and content extraction**

## Overview

Parses HTML content and extracts structured data including text, links, and headings. Local tool for the web_researcher agent.

## Features

- Plain text extraction (removes HTML tags)
- Link extraction with anchor text
- Heading extraction (h1-h6)
- Statistics (link count, text length, heading count)
- Flexible extraction types

## Usage

```bash
# Extract all information
python3 scripts/html_parser.py '{
  "html": "<html><body><h1>Title</h1><p>Content</p></body></html>"
}'

# Extract only text
python3 scripts/html_parser.py '{
  "html": "<html><body><p>Some text</p></body></html>",
  "extract_type": "text"
}'

# Extract only links
python3 scripts/html_parser.py '{
  "html": "<html><body><a href=\"url\">Link</a></body></html>",
  "extract_type": "links"
}'

# Health check
python3 scripts/html_parser.py --health-check
```

## Extract Types

- `all` - Extract text, links, headings, and stats (default)
- `text` - Extract only plain text
- `links` - Extract only links with anchor text
- `headings` - Extract only headings (h1-h6)

## Output

```json
{
  "success": true,
  "text": "Plain text content...",
  "links": [
    {"url": "https://...", "text": "Link text"}
  ],
  "headings": {
    "h1": ["Main Title"],
    "h2": ["Subtitle 1", "Subtitle 2"]
  },
  "stats": {
    "total_links": 5,
    "text_length": 1234,
    "total_headings": 10
  }
}
```

## Production Integration

For production use, integrate with:
- **BeautifulSoup4** - Robust HTML parsing
- **lxml** - Fast XML/HTML processing
- **html5lib** - Standards-compliant HTML parsing

Install dependencies:
```bash
pip install beautifulsoup4 lxml html5lib
```

## Current Implementation

Uses Python's built-in regex for simple HTML parsing. Replace with BeautifulSoup for production use.

## Manifest

- **Path:** `agents/research_orchestrator/agents/web_researcher/tools/html_parser/tool.yml`
- **Version:** 1.0
- **State:** stable
- **Local to:** web_researcher agent
