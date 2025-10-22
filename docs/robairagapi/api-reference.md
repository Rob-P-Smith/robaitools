---
layout: default
title: API Reference
parent: robairagapi
nav_order: 3
---

# API Reference

Complete REST API endpoint documentation for robairagapi.

**Base URL**: `http://localhost:8080`

**Authentication**: Bearer token (all endpoints except `/health` and `/api/v1/help`)

**Content-Type**: `application/json`

## Health & Status Endpoints

### GET /health

Public health check endpoint (no authentication required).

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:45.123456",
  "mcp_connected": true,
  "version": "1.0.0"
}
```

**Status Codes**: 200 (healthy), 503 (unhealthy)

---

### GET /api/v1/status

Detailed system status (authentication required).

**Headers**:
```
Authorization: Bearer YOUR_API_KEY
```

**Response**:
```json
{
  "api_status": "running",
  "mcp_status": "direct",
  "timestamp": "2024-01-15T10:30:45.123456",
  "components": {
    "crawl4ai_url": "http://localhost:11235",
    "mode": "direct"
  }
}
```

---

## Crawling Endpoints

### POST /api/v1/crawl

Crawl URL without storing (preview only).

**Request**:
```json
{
  "url": "https://example.com/article"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "url": "https://example.com/article",
    "title": "Article Title",
    "content": "Extracted text...",
    "markdown": "# Article Title\n\nMarkdown content...",
    "status": "success"
  },
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

**Status Codes**: 200 (success), 400 (invalid URL), 401 (unauthorized), 500 (crawl failed)

---

### POST /api/v1/crawl/store

Crawl and permanently store URL.

**Request**:
```json
{
  "url": "https://example.com/article",
  "tags": "python,tutorial,documentation",
  "retention_policy": "permanent"
}
```

**Parameters**:
- `url` (required): URL to crawl and store
- `tags` (optional): Comma-separated tags
- `retention_policy` (optional): `permanent` | `session_only` | `30_days`

**Response**:
```json
{
  "success": true,
  "data": {
    "url": "https://example.com/article",
    "title": "Article Title",
    "content": "Extracted text...",
    "markdown": "...",
    "content_id": 123,
    "stored": true,
    "retention_policy": "permanent",
    "tags": ["python", "tutorial", "documentation"]
  },
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

---

### POST /api/v1/crawl/temp

Crawl and store temporarily (session-only, 24 hours).

**Request**: Same as `/crawl/store`

**Response**: Same as `/crawl/store` with `retention_policy: "session_only"`

---

### POST /api/v1/crawl/deep/store

Deep crawl a domain (recursive breadth-first search).

**Request**:
```json
{
  "url": "https://docs.python.org",
  "max_depth": 2,
  "max_pages": 10,
  "include_external": false,
  "score_threshold": 0.0,
  "timeout": 600,
  "tags": "python,docs",
  "retention_policy": "permanent"
}
```

**Parameters**:
- `url` (required): Root URL to crawl
- `max_depth` (1-5, default 2): Maximum crawl depth
- `max_pages` (1-250, default 10): Maximum pages
- `include_external` (default false): Follow external links
- `score_threshold` (0.0-1.0): URL relevance filter
- `timeout` (60-1800s): Total timeout
- `tags`, `retention_policy`: Same as `/crawl/store`

**Response**:
```json
{
  "success": true,
  "data": {
    "root_url": "https://docs.python.org",
    "pages_crawled": 8,
    "urls": ["https://docs.python.org/3/tutorial/", ...],
    "content_ids": [123, 124, 125, ...]
  },
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

---

## Search Endpoints

### POST /api/v1/search

Simple vector similarity search (fast, no knowledge graph).

**Request**:
```json
{
  "query": "FastAPI authentication",
  "limit": 5,
  "tags": "python,web"
}
```

**Parameters**:
- `query` (required, max 500 chars): Search query
- `limit` (1-1000, default 10): Number of results
- `tags` (optional): Filter by tags (comma-separated)

**Response**:
```json
{
  "success": true,
  "data": {
    "query": "FastAPI authentication",
    "results": [
      {
        "content_id": 123,
        "url": "https://example.com/fastapi-auth",
        "title": "FastAPI Authentication Guide",
        "chunk_text": "FastAPI uses Bearer tokens...",
        "similarity_score": 0.95,
        "tags": ["python", "web"]
      }
    ],
    "count": 5
  },
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

**Performance**: 100-500ms

---

### POST /api/v1/search/kg

Hybrid search (vector + knowledge graph).

**Request**:
```json
{
  "query": "FastAPI async patterns",
  "rag_limit": 5,
  "kg_limit": 10,
  "tags": "python",
  "enable_expansion": true,
  "include_context": true
}
```

**Parameters**:
- `query` (required): Search query
- `rag_limit` (1-100, default 5): Vector search results
- `kg_limit` (1-100, default 10): Graph search results
- `tags` (optional): Tag filter
- `enable_expansion` (default true): Entity expansion
- `include_context` (default true): Include surrounding text

**Response**:
```json
{
  "success": true,
  "data": {
    "query": "FastAPI async patterns",
    "rag_results": [...],
    "kg_results": [
      {
        "entity": "asyncio",
        "type": "Library",
        "context": "Python's asyncio library...",
        "confidence": 0.87,
        "referenced_chunks": [3, 5, 7]
      }
    ],
    "rag_count": 5,
    "kg_count": 10
  },
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

**Performance**: 500-2000ms

---

### POST /api/v1/search/enhanced

Full 5-phase RAG pipeline (most comprehensive).

**Request**:
```json
{
  "query": "React performance optimization",
  "tags": "javascript,react"
}
```

**Parameters**:
- `query` (required): Search query
- `tags` (optional): Tag filter

**Fixed Configuration** (not customizable):
- RAG results: 3 with full markdown
- KG results: 5 with referenced chunks
- Entity expansion: Always enabled
- Context extraction: Always enabled

**Response**:
```json
{
  "success": true,
  "data": {
    "query": "React performance optimization",
    "rag_results": [
      {
        "content_id": 150,
        "url": "https://react.dev/learn/...",
        "title": "Optimizing Performance - React",
        "markdown": "# Full markdown content...",
        "similarity_score": 0.95
      }
    ],
    "kg_results": [
      {
        "entity": "Virtual DOM",
        "type": "Concept",
        "description": "...",
        "referenced_chunks": [1, 3, 5]
      }
    ],
    "processing_stages": {
      "entity_extraction": "completed",
      "vector_search": "completed",
      "graph_search": "completed",
      "ranking": "completed"
    }
  },
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

**Performance**: 1-3 seconds

---

## Memory Management Endpoints

### GET /api/v1/memory

List stored content with optional filtering.

**Query Parameters**:
- `retention_policy` (optional): Filter by `permanent` | `session_only` | `30_days`
- `limit` (1-1000, default 100): Maximum results

**Response**:
```json
{
  "success": true,
  "content": [
    {
      "content_id": 123,
      "url": "https://example.com/article",
      "title": "Article Title",
      "tags": ["python", "tutorial"],
      "retention_policy": "permanent",
      "created_at": "2024-01-15T10:30:45.123456",
      "updated_at": "2024-01-15T10:35:20.654321",
      "word_count": 5000,
      "chunk_count": 5
    }
  ],
  "count": 5,
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

---

### DELETE /api/v1/memory

Remove specific URL from memory.

**Query Parameters**:
- `url` (required): URL to delete

**Example**:
```bash
DELETE /api/v1/memory?url=https://example.com/article
```

**Response**:
```json
{
  "success": true,
  "message": "Removed https://example.com/article",
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

---

### DELETE /api/v1/memory/temp

Clear all session-only (temporary) content.

**Response**:
```json
{
  "success": true,
  "message": "Cleared temporary content",
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

---

## Statistics Endpoint

### GET /api/v1/stats

Get database statistics and usage metrics.

**Aliases**: `/api/v1/db/stats`

**Response**:
```json
{
  "success": true,
  "stats": {
    "total_content": 42,
    "total_chunks": 512,
    "total_vectors": 512,
    "database_size_bytes": 52428800,
    "permanent_content": 35,
    "session_content": 5,
    "thirty_day_content": 2,
    "avg_content_size": 1243,
    "avg_chunk_size": 987,
    "oldest_content": "2024-01-01T10:30:45.123456",
    "newest_content": "2024-01-15T10:30:45.123456",
    "kg_processed": 38,
    "kg_pending": 4
  },
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

---

## Domain Management Endpoints

### GET /api/v1/blocked-domains

List all blocked domain patterns.

**Response**:
```json
{
  "success": true,
  "blocked_domains": [
    {
      "pattern": "*.ru",
      "keyword": "geo-blocking",
      "created_at": "2024-01-10T12:00:00"
    },
    {
      "pattern": "*spam*",
      "keyword": "malicious-content",
      "created_at": "2024-01-05T09:15:30"
    }
  ],
  "count": 2,
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

---

### POST /api/v1/blocked-domains

Add domain pattern to blocklist.

**Request**:
```json
{
  "pattern": "*.malicious.com",
  "description": "Known malicious domain"
}
```

**Pattern Types**:
- `*.ru` - Wildcard suffix
- `*spam*` - Keyword wildcard
- `example.com` - Exact match

**Response**:
```json
{
  "success": true,
  "message": "Added *.malicious.com",
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

---

### DELETE /api/v1/blocked-domains

Remove domain pattern from blocklist.

**Query Parameters**:
- `pattern` (required): Domain pattern
- `keyword` (required): Authorization keyword

**Example**:
```bash
DELETE /api/v1/blocked-domains?pattern=*.ru&keyword=YOUR_KEYWORD
```

**Response**:
```json
{
  "success": true,
  "message": "Removed *.ru",
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

---

## Help Endpoint

### GET /api/v1/help

Tool documentation for LLM providers (no authentication required).

**Response**:
```json
{
  "success": true,
  "tools": [
    {
      "name": "crawl_url",
      "example": "Crawl http://www.example.com without storing",
      "parameters": "url: string"
    },
    {
      "name": "crawl_and_store",
      "example": "Crawl and permanently store https://github.com/...",
      "parameters": "url: string, tags?: string, retention_policy?: string"
    }
  ],
  "api_info": {
    "base_url": "/api/v1",
    "authentication": "Bearer token required"
  }
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (invalid parameters) |
| 401 | Unauthorized (missing/invalid API key) |
| 429 | Too many requests (rate limit exceeded) |
| 500 | Internal server error |

### Error Response Format

**Standard Error** (4xx):
```json
{
  "detail": "Invalid or unsafe URL provided"
}
```

**Server Error** (500):
```json
{
  "success": false,
  "error": "Exception message",
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

---

## Response Headers

All responses include:
- `Content-Type: application/json`
- `X-Process-Time: 0.123` (execution time in seconds)
- Standard HTTP status codes

---

## Search Modes Comparison

| Feature | Simple | KG Search | Enhanced |
|---------|--------|-----------|----------|
| Speed | 100-500ms | 500-2000ms | 1-3s |
| Vector Search | ✓ | ✓ | ✓ |
| Knowledge Graph | ✗ | ✓ | ✓ |
| Entity Expansion | ✗ | Optional | Always |
| Full Markdown | ✗ | ✗ | ✓ |
| Configurable | ✓ | ✓ | ✗ (fixed) |
| Best For | Quick lookups | Research | Deep analysis |

---

## Next Steps

- [Configuration](configuration.html) - API configuration options
- [Architecture](architecture.html) - System design and patterns
- [Getting Started](getting-started.html) - Usage examples
