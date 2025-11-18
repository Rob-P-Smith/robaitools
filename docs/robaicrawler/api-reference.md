---
layout: default
title: API Reference
parent: robaicrawler
nav_order: 3
---

# API Reference

Complete reference for robaicrawler HTTP API endpoints and MCP tool interfaces.

## HTTP API

robaicrawler exposes a FastAPI-based HTTP REST API on port 11235.

### Base URL

```
http://localhost:11235
```

### Endpoints

#### GET /health

Health check endpoint for Docker healthcheck and monitoring.

**Request:**
```
GET http://localhost:11235/health
```

**Response:**
```
200 OK
```

**Usage:**
- Docker healthcheck runs every 30 seconds
- Used by dependent services to wait for readiness
- No authentication required

---

#### POST /crawl

Main endpoint for crawling URLs and extracting content.

**Request:**
```
POST http://localhost:11235/crawl
Content-Type: application/json

{
  "urls": ["https://example.com"],
  "word_count_threshold": 10,
  "excluded_tags": ["nav", "header", "footer", "script", "style"],
  "remove_forms": true,
  "only_text": true
}
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| urls | array[string] | Yes | - | List of URLs to crawl |
| word_count_threshold | integer | No | 10 | Minimum words per text block |
| excluded_tags | array[string] | No | [] | HTML tags to remove |
| remove_forms | boolean | No | false | Remove form elements |
| only_text | boolean | No | false | Aggressive text-only extraction |

**Response:**
```json
{
  "success": true,
  "results": [{
    "url": "https://example.com",
    "cleaned_html": "<html>...</html>",
    "markdown": {
      "fit_markdown": "# Example Domain\n\nThis domain is for use...",
      "raw_markdown": "# Example Domain\n\n[Full content...]"
    },
    "metadata": {
      "title": "Example Domain",
      "status_code": 200,
      "images": ["https://example.com/image.jpg"],
      "links": ["https://example.com/page"]
    }
  }]
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Failed to crawl URL: Connection timeout",
  "url": "https://example.com",
  "status_code": null
}
```

## MCP Tool Interface

The primary way to use robaicrawler is through MCP tools exposed by robaitragmcp. These tools are automatically discovered from the Crawl4AIRAG class in robaimodeltools.

### Available Tools

#### crawler_crawl_url

Crawls a single URL and returns truncated content for LLM context.

**MCP Tool Definition:**
```json
{
  "name": "crawler_crawl_url",
  "description": "Crawl a URL and return markdown content (truncated for LLM)",
  "inputSchema": {
    "type": "object",
    "properties": {
      "url": {
        "type": "string",
        "description": "Target URL to crawl"
      },
      "return_full_content": {
        "type": "boolean",
        "description": "If true, returns full content without truncation",
        "default": false
      }
    },
    "required": ["url"]
  }
}
```

**Tool Call Example:**
```json
{
  "tool": "crawler_crawl_url",
  "parameters": {
    "url": "https://docs.python.org/3/library/asyncio.html",
    "return_full_content": false
  }
}
```

**Response:**
```json
{
  "success": true,
  "url": "https://docs.python.org/3/library/asyncio.html",
  "title": "asyncio — Asynchronous I/O",
  "markdown": "[Truncated to 8000 chars...]",
  "content_length": 8000,
  "status_code": 200,
  "message": "Successfully crawled URL. Content truncated to 8000 characters."
}
```

---

#### crawler_crawl_and_store

Crawls a URL, stores in database, generates embeddings, and queues for knowledge graph processing.

**MCP Tool Definition:**
```json
{
  "name": "crawler_crawl_and_store",
  "description": "Crawl URL, store in database, generate embeddings, queue for KG",
  "inputSchema": {
    "type": "object",
    "properties": {
      "url": {
        "type": "string",
        "description": "Target URL to crawl and store"
      },
      "retention_policy": {
        "type": "string",
        "enum": ["permanent", "session_only", "30_days"],
        "description": "How long to keep content",
        "default": "permanent"
      },
      "tags": {
        "type": "string",
        "description": "Comma-separated tags (e.g., 'python,docs,asyncio')",
        "default": ""
      }
    },
    "required": ["url"]
  }
}
```

**Tool Call Example:**
```json
{
  "tool": "crawler_crawl_and_store",
  "parameters": {
    "url": "https://fastapi.tiangolo.com",
    "retention_policy": "permanent",
    "tags": "python,fastapi,documentation"
  }
}
```

**Response:**
```json
{
  "success": true,
  "content_id": 123,
  "url": "https://fastapi.tiangolo.com",
  "title": "FastAPI - Modern web framework for building APIs",
  "stored_at": "2025-01-15T10:30:00Z",
  "embeddings_generated": 15,
  "kg_queued": true
}
```

---

#### crawler_deep_crawl_and_store

Performs breadth-first crawl starting from a URL, following links up to specified depth and page count.

**MCP Tool Definition:**
```json
{
  "name": "crawler_deep_crawl_and_store",
  "description": "Deep crawl multiple pages from a starting URL (BFS algorithm)",
  "inputSchema": {
    "type": "object",
    "properties": {
      "url": {
        "type": "string",
        "description": "Starting URL for deep crawl"
      },
      "retention_policy": {
        "type": "string",
        "enum": ["permanent", "session_only", "30_days"],
        "default": "permanent"
      },
      "tags": {
        "type": "string",
        "description": "Tags applied to all crawled pages",
        "default": ""
      },
      "max_depth": {
        "type": "integer",
        "minimum": 1,
        "maximum": 5,
        "description": "Maximum link depth to follow",
        "default": 2
      },
      "max_pages": {
        "type": "integer",
        "minimum": 1,
        "maximum": 250,
        "description": "Maximum pages to store",
        "default": 10
      },
      "include_external": {
        "type": "boolean",
        "description": "Follow external domain links",
        "default": false
      }
    },
    "required": ["url"]
  }
}
```

**Tool Call Example:**
```json
{
  "tool": "crawler_deep_crawl_and_store",
  "parameters": {
    "url": "https://fastapi.tiangolo.com",
    "max_depth": 3,
    "max_pages": 50,
    "retention_policy": "permanent",
    "tags": "fastapi,documentation,tutorial",
    "include_external": false
  }
}
```

**Response:**
```json
{
  "success": true,
  "stored_count": 47,
  "skipped_count": 3,
  "start_url": "https://fastapi.tiangolo.com",
  "max_depth_reached": 3,
  "duration_seconds": 125,
  "skipped_reasons": {
    "non_english": 2,
    "error": 1
  }
}
```

## Examples

### Example 1: Direct HTTP Call

Test the crawler service directly:

```bash
curl -X POST http://localhost:11235/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com"],
    "word_count_threshold": 10,
    "excluded_tags": ["nav", "header", "footer"],
    "only_text": true
  }'
```

### Example 2: Via Chat Interface (Autonomous Mode)

User types in open-webui:
```
[[autonomous]] Crawl and store https://fastapi.tiangolo.com with tags "python,framework"
```

LLM calls `crawler_crawl_and_store`:
```json
{
  "url": "https://fastapi.tiangolo.com",
  "retention_policy": "permanent",
  "tags": "python,framework"
}
```

### Example 3: Deep Crawl Documentation Site

User types:
```
[[autonomous]] Build a knowledge base from https://docs.python.org/3/library/asyncio.html,
crawl all related pages up to 30 pages
```

LLM calls `crawler_deep_crawl_and_store`:
```json
{
  "url": "https://docs.python.org/3/library/asyncio.html",
  "max_depth": 2,
  "max_pages": 30,
  "retention_policy": "permanent",
  "tags": "python,asyncio,documentation"
}
```

### Example 4: Research Mode (Automatic)

User types:
```
research python async best practices
```

robaiproxy automatically:
1. Searches web via Serper (10 results)
2. For each URL: calls `crawler_crawl_url` (parallel)
3. Accumulates context from all pages
4. Generates answer with citations

No explicit tool call - automatic orchestration.

## Error Handling

### HTTP Errors

**4xx Client Errors:**
```json
{
  "success": false,
  "error": "Page not found",
  "url": "https://example.com/missing",
  "status_code": 404
}
```

**5xx Server Errors:**
```json
{
  "success": false,
  "error": "Server error",
  "url": "https://example.com",
  "status_code": 500
}
```

### Security Blocks

**SSRF Protection:**
```json
{
  "success": false,
  "error": "URL blocked: Private IP address",
  "url": "http://192.168.1.1",
  "blocked": true,
  "reason": "SSRF protection"
}
```

**Domain Blocking:**
```json
{
  "success": false,
  "error": "Domain blocked: Adult content pattern",
  "url": "https://blocked-site.com",
  "blocked": true,
  "reason": "matches *.adult.*"
}
```

### Content Rejections

**Language Detection:**
```json
{
  "success": false,
  "error": "Content not in English",
  "url": "https://example.fr",
  "detected_language": "fr",
  "skipped": true
}
```

**Error Page Detection:**
```json
{
  "success": false,
  "error": "Rate limit or error page detected",
  "url": "https://example.com",
  "status_code": 200,
  "detected_error_pattern": "too many requests"
}
```

## Rate Limits

robaicrawler itself has no rate limits, but:

1. **Target sites** may rate limit your requests
   - Deep crawl includes 1-2s delay between requests
   - Reduces rate limit errors

2. **Browser resources** limit concurrent requests
   - Default: 5 concurrent Chrome tabs
   - Increase shared memory for more concurrency

3. **MCP server** has tool call timeout
   - Default: 30 seconds per call
   - Deep crawls may take 30-240 seconds

## Authentication

robaicrawler service has **no authentication** - relies on network isolation.

**Security:**
- Use host networking (localhost only)
- Or restrict CORS origins in production
- Downstream services (robairagapi) have API key auth

**For Production:**
Consider adding reverse proxy with authentication if exposing externally.

## Response Formats

### Markdown Formats

**fit_markdown:** Cleaned, optimized for LLM consumption
- Navigation removed
- Boilerplate filtered
- Images stripped
- Forms removed

**raw_markdown:** Full conversion with minimal cleaning
- All content preserved
- Only script/style tags removed
- Used for storage, not LLM context

### Metadata Structure

```json
{
  "title": "Page Title",
  "status_code": 200,
  "images": ["https://example.com/img1.jpg", "https://example.com/img2.jpg"],
  "links": ["https://example.com/page1", "https://example.com/page2"],
  "content_hash": "abc123...",
  "timestamp": "2025-01-15T10:30:00Z",
  "language": "en",
  "cleaning_stats": {
    "original_size": 12500,
    "cleaned_size": 3200,
    "reduction_ratio": 0.744
  }
}
```

## Performance Tips

1. **Use return_full_content=false** for LLM context (faster)
2. **Batch crawls in parallel** via deep_crawl instead of sequential calls
3. **Cache results** - check database before crawling duplicate URLs
4. **Set reasonable max_pages** - deep crawls can take minutes for 100+ pages
5. **Monitor memory** - each Chrome tab uses 100-200MB
6. **Use tags** - organize content for easy retrieval later

## Related Documentation

- [Getting Started](getting-started.md) - Installation and first crawl
- [Configuration](configuration.md) - Environment variables and tuning
- [Architecture](architecture.md) - Data flow and integration patterns
