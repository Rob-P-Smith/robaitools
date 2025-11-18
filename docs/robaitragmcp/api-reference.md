---
layout: default
title: API Reference
parent: robaitragmcp
nav_order: 3
---

# API Reference

Complete documentation of all robaitragmcp MCP tools.

## MCP Tools Overview

robaitragmcp exposes 15+ tools via the Model Context Protocol (JSON-RPC 2.0).

| Tool | Purpose | Input | Output |
|------|---------|-------|--------|
| `crawl_url` | Extract web content | url, selector | content, metadata |
| `search` | Full-text search | query, tags, limit | results array |
| `vector_search` | Semantic similarity | query, limit, threshold | results with scores |
| `get_memory` | Retrieve stored content | id | full content |
| `create_tag` | Create content tag | name, description | tag_id |
| `list_tags` | List all tags | - | tags array |
| `update_memory` | Update content | id, updates | status |
| `delete_memory` | Remove content | id | deleted_id |
| `export_content` | Export data | format, tags | exported data |
| `clear_memory` | Wipe all data | confirm | status |

## Web Crawling

### crawl_url

Extract content from a web page using Crawl4AI.

**Input**:
```json
{
  "url": "https://example.com",
  "selector": "main",
  "wait_for_element": ".content",
  "timeout": 30
}
```

**Parameters**:
- `url` (string, required) - Web page URL
- `selector` (string, optional) - CSS selector to extract
- `wait_for_element` (string, optional) - Wait for element before extracting
- `timeout` (integer, optional) - Timeout in seconds

**Output**:
```json
{
  "success": true,
  "url": "https://example.com",
  "title": "Page Title",
  "content": "Extracted markdown content",
  "metadata": {
    "description": "Meta description",
    "keywords": "tag1, tag2",
    "timestamp": "2025-10-17T14:30:00Z"
  }
}
```

**Example**:
```python
crawl_result = call_mcp_tool("crawl_url",
    url="https://docs.python.org/3/library/asyncio.html",
    timeout=30
)
```

## Search Operations

### search

Full-text search across indexed content.

**Input**:
```json
{
  "query": "python async patterns",
  "tags": ["python", "asyncio"],
  "limit": 5,
  "fuzzy": true
}
```

**Parameters**:
- `query` (string, required) - Search query
- `tags` (array, optional) - Filter by tags
- `limit` (integer, default: 10) - Max results
- `fuzzy` (boolean, default: false) - Fuzzy matching

**Output**:
```json
{
  "results": [
    {
      "id": "memory-123",
      "title": "Asyncio Documentation",
      "url": "https://docs.python.org",
      "relevance": 0.95,
      "snippet": "asyncio is a library to write concurrent code...",
      "tags": ["python", "asyncio"]
    }
  ],
  "total": 5
}
```

**Example**:
```python
results = call_mcp_tool("search",
    query="python async patterns",
    tags=["python"],
    limit=5
)
```

### vector_search

Semantic similarity search using embeddings.

**Input**:
```json
{
  "query": "how to implement concurrent operations",
  "limit": 10,
  "threshold": 0.7,
  "tags": ["python"]
}
```

**Parameters**:
- `query` (string, required) - Search query
- `limit` (integer, default: 10) - Max results
- `threshold` (float, default: 0.5) - Similarity threshold
- `tags` (array, optional) - Filter by tags

**Output**:
```json
{
  "results": [
    {
      "id": "chunk-456",
      "text": "Chunk preview text...",
      "similarity": 0.89,
      "source_id": "memory-123",
      "source_title": "Asyncio Tutorial",
      "source_url": "https://docs.python.org"
    }
  ],
  "count": 8
}
```

**Example**:
```python
semantic = call_mcp_tool("vector_search",
    query="concurrent programming in Python",
    limit=5,
    threshold=0.75
)
```

## Content Management

### get_memory

Retrieve full content by ID.

**Input**:
```json
{
  "id": "memory-123"
}
```

**Output**:
```json
{
  "id": "memory-123",
  "url": "https://docs.python.org",
  "title": "Asyncio Documentation",
  "content": "Full markdown content...",
  "tags": ["python", "asyncio"],
  "created_at": "2025-10-17T12:00:00Z",
  "updated_at": "2025-10-17T14:30:00Z"
}
```

### update_memory

Modify stored content.

**Input**:
```json
{
  "id": "memory-123",
  "title": "New Title",
  "tags": ["python", "asyncio", "concurrency"]
}
```

**Output**:
```json
{
  "success": true,
  "id": "memory-123",
  "updated_fields": ["title", "tags"]
}
```

### delete_memory

Remove content from memory.

**Input**:
```json
{
  "id": "memory-123"
}
```

**Output**:
```json
{
  "success": true,
  "deleted_id": "memory-123"
}
```

## Tag Management

### create_tag

Create new content tag.

**Input**:
```json
{
  "name": "python/asyncio",
  "description": "Python asyncio patterns and tutorials",
  "color": "#3776ab"
}
```

**Output**:
```json
{
  "tag_id": "tag-789",
  "name": "python/asyncio",
  "description": "Python asyncio patterns and tutorials",
  "created_at": "2025-10-17T14:30:00Z"
}
```

### list_tags

List all available tags.

**Output**:
```json
{
  "tags": [
    {
      "tag_id": "tag-1",
      "name": "python",
      "description": "Python language resources",
      "count": 45
    },
    {
      "tag_id": "tag-2",
      "name": "python/asyncio",
      "description": "Python asyncio patterns",
      "count": 12
    }
  ],
  "total": 24
}
```

## Data Management

### export_content

Export stored content in various formats.

**Input**:
```json
{
  "format": "markdown",
  "tags": ["python"],
  "include_metadata": true
}
```

**Parameters**:
- `format` (string) - Export format: markdown, json, html
- `tags` (array, optional) - Filter by tags
- `include_metadata` (boolean, default: true)

**Output**:
```json
{
  "format": "markdown",
  "content": "# Python Resources\n\n## Asyncio\n...",
  "file_size": 125000,
  "item_count": 15
}
```

### clear_memory

Remove all stored content (requires confirmation).

**Input**:
```json
{
  "confirm": true
}
```

**Output**:
```json
{
  "success": true,
  "deleted_items": 42,
  "freed_space_mb": 125
}
```

## Error Handling

All tools return error responses on failure:

```json
{
  "error": true,
  "code": "NOT_FOUND",
  "message": "Content with id 'memory-123' not found",
  "details": {
    "id": "memory-123"
  }
}
```

**Common Error Codes**:
- `NOT_FOUND` - Content not found
- `INVALID_INPUT` - Malformed input
- `DATABASE_ERROR` - Storage issue
- `CRAWL_FAILED` - Web extraction failed
- `RATE_LIMITED` - Too many requests

## Integration Examples

### With Claude API

```python
import anthropic

# Configure tools
tools = [
    {
        "name": "crawl_url",
        "description": "Extract content from web page",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "timeout": {"type": "integer"}
            },
            "required": ["url"]
        }
    },
    {
        "name": "search",
        "description": "Search indexed content",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer"}
            },
            "required": ["query"]
        }
    }
]

# Use with Claude
client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    tools=tools,
    messages=[
        {
            "role": "user",
            "content": "Search for Python asyncio information and summarize"
        }
    ]
)
```

### Batch Operations

```python
# Crawl multiple pages
urls = [
    "https://docs.python.org/3/library/asyncio.html",
    "https://peps.python.org/pep-3156/",
    "https://example.com/async-tutorial"
]

results = []
for url in urls:
    result = call_mcp_tool("crawl_url", url=url)
    results.append(result)

# Tag all
for result in results:
    call_mcp_tool("create_tag", name="python/asyncio")
```

## Rate Limiting

Tools have per-session rate limits:
- `crawl_url`: 10 per minute
- `search`: 100 per minute
- `vector_search`: 50 per minute
- All other tools: 200 per minute

Exceeding limits returns `RATE_LIMITED` error.

## Next Steps

- [Getting Started](getting-started.html) - Installation and usage
- [Configuration](configuration.html) - Environment settings
- [Architecture](architecture.html) - System design
