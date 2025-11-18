---
layout: default
title: Getting Started
parent: robairagapi
nav_order: 2
---

# Getting Started

Quick installation and usage guide for robairagapi REST API bridge.

## Prerequisites

- **Python 3.11+**
- **Docker and Docker Compose** (recommended)
- **robaimodeltools** (shared library, mounted as volume)
- **Crawl4AI service** running on port 11235
- **Neo4j + kg-service** (optional, for KG search endpoints)
- **API Key** (OPENAI_API_KEY environment variable)

## Quick Start with Docker

### Step 1: Verify Dependencies Running

```bash
# Check Crawl4AI
curl http://localhost:11235/health

# Check Neo4j (optional, for KG features)
curl http://localhost:7474

# Check kg-service (optional, for KG features)
curl http://localhost:8088/health
```

### Step 2: Configure Environment

Edit main `.env` file in repo root:

```bash
# Required - at least one API key
OPENAI_API_KEY=sk-your-key-here
OPENAI_API_KEY_2=sk-secondary-key-optional

# Service URLs
CRAWL4AI_URL=http://localhost:11235
KG_SERVICE_URL=http://localhost:8088

# Database
USE_MEMORY_DB=true

# Optional Security Settings
ENABLE_MAC_VALIDATION=false
STRICT_AUTH_FOR_PFSENSE=false
TRUSTED_LAN_SUBNET=192.168.10.0/24
```

### Step 3: Start Service

```bash
cd /home/robiloo/Documents/robaitools
docker compose up -d robairagapi
```

### Step 4: Verify Running

```bash
# Check container status
docker compose ps robairagapi

# Check logs
docker compose logs robairagapi

# Test health endpoint (no auth required)
curl http://localhost:8081/health

# Expected response:
# {
#   "status": "healthy",
#   "timestamp": "2025-01-18T10:30:45.123456",
#   "mcp_connected": true,
#   "version": "1.0.0"
# }
```

## Local Development Setup

### Step 1: Install Dependencies

```bash
cd robairagapi
pip install -r requirements.txt
```

**Core Dependencies** (7 packages):
- fastapi (0.115.6) - Web framework
- uvicorn (0.32.1) - ASGI server
- pydantic (2.10.4) - Request/response validation
- python-dotenv (1.0.1) - Environment management
- httpx (0.28.1) - HTTP client
- gunicorn (23.0.0) - Production server

### Step 2: Run Development Server

```bash
python main.py
```

Server starts on **port 8081** (configurable via SERVER_PORT).

### Step 3: Test with cURL

```bash
# Health check
curl http://localhost:8081/health

# Status (requires auth)
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  http://localhost:8081/api/v1/status
```

## Basic Usage

### Authentication

All endpoints except `/health` require **Bearer token authentication**:

```bash
# Set API key from environment
export API_KEY="$OPENAI_API_KEY"

# Use in requests
curl -H "Authorization: Bearer $API_KEY" \
  http://localhost:8081/api/v1/status
```

**Multi-Key Support**:
- OPENAI_API_KEY (primary key)
- OPENAI_API_KEY_2 (secondary key for rotation)

Both keys are accepted. Useful for key rotation without downtime.

### Rate Limiting

**Default**: 60 requests per minute per API key

**Configure**:
```bash
# In .env
RATE_LIMIT_PER_MINUTE=120  # Increase limit
ENABLE_RATE_LIMIT=false    # Disable completely
```

**Rate limit behavior**:
- Sliding 60-second window
- Per-API-key tracking
- Returns 404 (not 429) on rate limit exceeded (security by obscurity)

### Session Management

**Automatic session creation**:
- 24-hour timeout
- Auto-cleanup every hour
- Session ID returned in response (internal use)

No client-side session handling needed.

## Example Workflows

### Workflow 1: Crawl and Store URL

**Request**:
```bash
curl -X POST http://localhost:8081/api/v1/crawl/store \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://docs.python.org/3/tutorial/",
    "tags": "python,tutorial,documentation",
    "retention_policy": "permanent"
  }'
```

**Response**:
```json
{
  "success": true,
  "data": {
    "url": "https://docs.python.org/3/tutorial/",
    "title": "The Python Tutorial",
    "content_id": 123,
    "chunks_stored": 45,
    "word_count": 12500,
    "retention_policy": "permanent",
    "tags": ["python", "tutorial", "documentation"],
    "extracted_at": "2025-01-18T10:30:45.123456"
  },
  "timestamp": "2025-01-18T10:30:45.123456"
}
```

**Retention policies**:
- `permanent` - Never auto-deleted
- `session_only` - Deleted when session expires
- `30_days` - Auto-deleted after 30 days

### Workflow 2: Simple Vector Search

**Use case**: Fast vector similarity search, no KG overhead

**Request**:
```bash
curl -X POST http://localhost:8081/api/v1/search \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "async await patterns in Python",
    "limit": 5,
    "tags": "python"
  }'
```

**Response**:
```json
{
  "success": true,
  "data": {
    "query": "async await patterns in Python",
    "results": [
      {
        "chunk_id": 1234,
        "content_id": 123,
        "url": "https://docs.python.org/3/library/asyncio.html",
        "title": "asyncio — Asynchronous I/O",
        "chunk_text": "async def main():\n    await asyncio.sleep(1)\n    print('hello')",
        "similarity_score": 0.89,
        "chunk_index": 3,
        "tags": ["python", "async"]
      }
    ],
    "count": 5,
    "search_time_ms": 45
  },
  "timestamp": "2025-01-18T10:31:20.456789"
}
```

**Performance**: 50-100ms typical

### Workflow 3: KG Search (5-Phase Pipeline)

**Use case**: Complex queries requiring entity extraction and graph traversal

**Request**:
```bash
curl -X POST http://localhost:8081/api/v1/search/kg \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "React performance optimization with hooks",
    "rag_limit": 5,
    "kg_limit": 10,
    "enable_expansion": true,
    "include_context": true
  }'
```

**What happens internally**:
1. **Phase 1**: GLiNER entity extraction from query (finds "React", "hooks" as entities)
2. **Phase 2**: Parallel vector search (SQLite) + Neo4j graph search
3. **Phase 3**: KG entity expansion (finds related entities via graph traversal)
4. **Phase 4**: Multi-signal ranking (5 signals: vector 35%, graph 25%, BM25 20%, recency 10%, title 10%)
5. **Phase 5**: Context extraction and formatting

**Response**:
```json
{
  "success": true,
  "data": {
    "query": "React performance optimization with hooks",
    "rag_results": [
      {
        "content_id": 456,
        "url": "https://react.dev/learn/...",
        "title": "Optimizing Performance",
        "chunk_text": "useMemo and useCallback hooks...",
        "similarity_score": 0.92,
        "rank_score": 0.88,
        "signals": {
          "vector": 0.92,
          "graph": 0.85,
          "bm25": 0.78,
          "recency": 0.95,
          "title_match": 0.80
        }
      }
    ],
    "kg_results": [
      {
        "entity": "useMemo",
        "type": "Function",
        "confidence": 0.91,
        "related_entities": ["useCallback", "React.memo"],
        "graph_distance": 1
      }
    ],
    "rag_count": 5,
    "kg_count": 10,
    "processing_time_ms": 250
  },
  "timestamp": "2025-01-18T10:32:15.789012"
}
```

**Performance**: 150-250ms typical
**Data size**: 1-4MB typical (comprehensive results)
**Requirements**: Neo4j + kg-service must be running

### Workflow 4: Enhanced Search (Optimized)

**Use case**: Need comprehensive context with controlled data size

**Request**:
```bash
curl -X POST http://localhost:8081/api/v1/search/enhanced \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "FastAPI dependency injection",
    "rag_limit": 1,
    "kg_limit": 10
  }'
```

**What you get**:
- **1 top RAG result** (full document, 100K char limit)
- **10 KG chunks** (entity-rich snippets)
- **1 top KG document** (full document, 100K char limit, different URL from RAG)

**Response structure**:
```json
{
  "success": true,
  "data": {
    "rag_result": {
      "url": "https://fastapi.tiangolo.com/tutorial/dependencies/",
      "title": "Dependencies - FastAPI",
      "full_markdown": "# Dependencies\n\nFastAPI has a very powerful...",
      "similarity_score": 0.94,
      "char_count": 45000
    },
    "kg_chunks": [
      {
        "chunk_text": "Depends() function allows...",
        "entities": ["Depends", "FastAPI", "dependency injection"],
        "entity_density": 0.15
      }
    ],
    "kg_document": {
      "url": "https://fastapi.tiangolo.com/advanced/dependencies/",
      "title": "Advanced Dependencies",
      "full_markdown": "# Advanced Dependencies...",
      "entity_density": 0.22,
      "char_count": 38000
    }
  },
  "timestamp": "2025-01-18T10:33:45.123456"
}
```

**Performance**: 200-300ms typical
**Data size**: 200-250KB typical (90% smaller than full KG search)
**Requirements**: Neo4j + kg-service must be running

### Workflow 5: Deep Crawl

**Use case**: Crawl documentation sites with multiple pages

**Request**:
```bash
curl -X POST http://localhost:8081/api/v1/crawl/deep/store \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://docs.python.org/3/library/",
    "max_depth": 2,
    "max_pages": 50,
    "include_external": false,
    "score_threshold": 0.0,
    "tags": "python,stdlib,documentation",
    "retention_policy": "permanent",
    "timeout": 300
  }'
```

**Parameters**:
- `max_depth`: 1-5 (default 2) - How many link levels to follow
- `max_pages`: 1-250 (default 10) - Maximum pages to crawl
- `include_external`: true/false - Follow external domain links
- `score_threshold`: 0.0-1.0 - Minimum URL relevance score
- `timeout`: 60-1800 seconds - Overall crawl timeout

**Response**:
```json
{
  "success": true,
  "data": {
    "root_url": "https://docs.python.org/3/library/",
    "pages_crawled": 50,
    "pages_stored": 48,
    "pages_skipped": 2,
    "urls_crawled": [
      "https://docs.python.org/3/library/asyncio.html",
      "https://docs.python.org/3/library/typing.html",
      ...
    ],
    "content_ids": [124, 125, 126, ...],
    "total_chunks": 2400,
    "crawl_duration_seconds": 180,
    "timestamp": "2025-01-18T10:38:45.123456"
  },
  "timestamp": "2025-01-18T10:38:45.123456"
}
```

**Performance**: 30-180 seconds typical (depends on max_pages)
**Rate limiting**: Built-in delays between requests to avoid overloading target server

### Workflow 6: Memory Management

**List all stored content**:
```bash
curl -H "Authorization: Bearer $API_KEY" \
  "http://localhost:8081/api/v1/memory?limit=100"
```

**Filter by retention policy**:
```bash
curl -H "Authorization: Bearer $API_KEY" \
  "http://localhost:8081/api/v1/memory?retention_policy=permanent&limit=50"
```

**Delete specific URL**:
```bash
curl -X DELETE \
  -H "Authorization: Bearer $API_KEY" \
  "http://localhost:8081/api/v1/memory?url=https://example.com/old-page"
```

**Clear all temporary content**:
```bash
curl -X DELETE \
  -H "Authorization: Bearer $API_KEY" \
  http://localhost:8081/api/v1/memory/temp
```

### Workflow 7: Domain Blocking

**Add blocked domain pattern**:
```bash
curl -X POST http://localhost:8081/api/v1/blocked-domains \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "pattern": "*.ru",
    "description": "Block all .ru domains"
  }'
```

**Pattern types**:
- `*.ru` - Wildcard suffix (blocks all .ru domains)
- `*spam*` - Keyword wildcard (blocks any URL containing "spam")
- `example.com` - Exact match

**List blocked domains**:
```bash
curl -H "Authorization: Bearer $API_KEY" \
  http://localhost:8081/api/v1/blocked-domains
```

**Remove blocked domain**:
```bash
curl -X DELETE \
  -H "Authorization: Bearer $API_KEY" \
  "http://localhost:8081/api/v1/blocked-domains?pattern=*.ru&keyword=authorization-keyword"
```

### Workflow 8: Database Statistics

```bash
curl -H "Authorization: Bearer $API_KEY" \
  http://localhost:8081/api/v1/stats
```

**Response**:
```json
{
  "success": true,
  "stats": {
    "total_content": 1234,
    "total_chunks": 45678,
    "total_embeddings": 45678,
    "db_size_mb": 234.5,
    "permanent_content": 1000,
    "session_content": 150,
    "30day_content": 84,
    "tag_distribution": {
      "python": 450,
      "javascript": 320,
      "documentation": 680
    }
  },
  "timestamp": "2025-01-18T10:40:00.123456"
}
```

## Python Client Examples

### Installation

```python
pip install requests
```

### Basic Usage Class

```python
import requests
from typing import Optional, Dict, Any, List

class RobAIRAGClient:
    """Client for robairagapi REST API"""

    def __init__(self, base_url: str = "http://localhost:8081", api_key: str = None):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def crawl_and_store(self, url: str, tags: str = "", retention_policy: str = "permanent") -> Dict[str, Any]:
        """Crawl and store a URL"""
        response = requests.post(
            f"{self.base_url}/api/v1/crawl/store",
            headers=self.headers,
            json={"url": url, "tags": tags, "retention_policy": retention_policy}
        )
        return response.json()

    def search(self, query: str, limit: int = 5, tags: Optional[str] = None) -> Dict[str, Any]:
        """Simple vector search"""
        response = requests.post(
            f"{self.base_url}/api/v1/search",
            headers=self.headers,
            json={"query": query, "limit": limit, "tags": tags}
        )
        return response.json()

    def kg_search(self, query: str, rag_limit: int = 5, kg_limit: int = 10) -> Dict[str, Any]:
        """Full 5-phase KG search"""
        response = requests.post(
            f"{self.base_url}/api/v1/search/kg",
            headers=self.headers,
            json={"query": query, "rag_limit": rag_limit, "kg_limit": kg_limit}
        )
        return response.json()

    def enhanced_search(self, query: str, rag_limit: int = 1, kg_limit: int = 10) -> Dict[str, Any]:
        """Optimized enhanced search"""
        response = requests.post(
            f"{self.base_url}/api/v1/search/enhanced",
            headers=self.headers,
            json={"query": query, "rag_limit": rag_limit, "kg_limit": kg_limit}
        )
        return response.json()

    def list_memory(self, limit: int = 100, retention_policy: Optional[str] = None) -> Dict[str, Any]:
        """List stored content"""
        params = {"limit": limit}
        if retention_policy:
            params["retention_policy"] = retention_policy
        response = requests.get(
            f"{self.base_url}/api/v1/memory",
            headers=self.headers,
            params=params
        )
        return response.json()

    def forget_url(self, url: str) -> Dict[str, Any]:
        """Delete specific URL"""
        response = requests.delete(
            f"{self.base_url}/api/v1/memory",
            headers=self.headers,
            params={"url": url}
        )
        return response.json()


# Usage example
client = RobAIRAGClient(api_key="your-api-key")

# Crawl and store
result = client.crawl_and_store(
    url="https://docs.python.org/3/tutorial/",
    tags="python,tutorial",
    retention_policy="permanent"
)
print(f"Stored: {result['data']['title']}")

# Search
results = client.search(query="async await", limit=5, tags="python")
for item in results['data']['results']:
    print(f"[{item['similarity_score']:.2f}] {item['title']}")
```

## Production Deployment

### Docker Compose (Recommended)

Full service stack in master `docker-compose.yml`:

```bash
cd /home/robiloo/Documents/robaitools
docker compose up -d robairagapi
```

**Dependency order**:
1. crawl4ai
2. neo4j
3. kg-service
4. robaitragmcp (optional)
5. robairagapi

### Multi-Worker Production

```bash
# Run with gunicorn (4 workers)
gunicorn api.server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8081 \
  --timeout 120
```

### Health Checks

Docker Compose includes built-in health check:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8081/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 10s
```

### Load Balancing

Use nginx upstream for load balancing multiple instances:

```nginx
upstream robairagapi {
    server localhost:8081;
    server localhost:8082;
    server localhost:8083;
}

server {
    listen 80;
    location / {
        proxy_pass http://robairagapi;
        proxy_set_header Authorization $http_authorization;
    }
}
```

## Troubleshooting

### Issue: Service Won't Start

**Symptoms**:
```
docker compose logs robairagapi
# Error: "No API keys configured"
```

**Solution**:
```bash
# Verify API key in .env
grep OPENAI_API_KEY .env

# Must have at least one of:
# - OPENAI_API_KEY
# - OPENAI_API_KEY_2
```

### Issue: Authentication Fails

**Symptoms**:
```
curl -H "Authorization: Bearer $API_KEY" http://localhost:8081/api/v1/status
# Returns: 404 Not Found
```

**Solution**:
- Service returns 404 (not 401/403) for invalid API keys (security by obscurity)
- Verify API key matches exactly
- Check logs: `docker compose logs robairagapi | grep SECURITY`
- Ensure no extra whitespace in Authorization header

### Issue: Rate Limit Exceeded

**Symptoms**:
```
# Returns 404 after 60 requests
```

**Solution**:
```bash
# Increase limit or disable
# In .env:
RATE_LIMIT_PER_MINUTE=120
# OR
ENABLE_RATE_LIMIT=false

# Restart service
docker compose restart robairagapi
```

### Issue: Crawl4AI Connection Error

**Symptoms**:
```
# Error: "Failed to connect to Crawl4AI"
```

**Solution**:
```bash
# Check Crawl4AI is running
curl http://localhost:11235/health

# Start if needed
docker compose up -d crawl4ai

# Check network connectivity
docker compose exec robairagapi curl http://localhost:11235/health
```

### Issue: KG Search Fails

**Symptoms**:
```
POST /api/v1/search/kg
# Returns error about Neo4j connection
```

**Solution**:
```bash
# KG search requires Neo4j + kg-service
docker compose ps neo4j kg-service

# Start if needed
docker compose up -d neo4j kg-service

# Verify connectivity
curl http://localhost:7474
curl http://localhost:8088/health
```

### Issue: Database Errors

**Symptoms**:
```
# SQLite errors or missing data
```

**Solution**:
```bash
# Check robaimodeltools volume mount
docker compose exec robairagapi ls -la /robaimodeltools

# Check database file
docker compose exec robairagapi ls -lh /data/crawl4ai_rag.db

# Verify USE_MEMORY_DB setting
docker compose exec robairagapi env | grep USE_MEMORY_DB
```

## Performance Tuning

### Search Performance

**Simple Search** (fastest):
- 50-100ms typical
- Use when you don't need KG features
- Endpoint: `/api/v1/search`

**Enhanced Search** (balanced):
- 200-300ms typical
- Smaller data size (200-250KB)
- Good balance of speed and quality
- Endpoint: `/api/v1/search/enhanced`

**KG Search** (comprehensive):
- 150-250ms typical
- Large data size (1-4MB)
- Maximum context and quality
- Endpoint: `/api/v1/search/kg`

### Worker Configuration

```bash
# Single worker (development)
python main.py

# Multiple workers (production)
gunicorn --workers $(nproc) \
  --worker-class uvicorn.workers.UvicornWorker \
  api.server:app
```

### Rate Limiting Strategy

```bash
# Low traffic (default)
RATE_LIMIT_PER_MINUTE=60

# Medium traffic
RATE_LIMIT_PER_MINUTE=120

# High traffic (use multiple keys)
OPENAI_API_KEY=key1
OPENAI_API_KEY_2=key2
# Each key gets independent rate limit

# Bulk operations (disable)
ENABLE_RATE_LIMIT=false
```

### Database Mode

```bash
# Disk mode (simpler)
USE_MEMORY_DB=false

# RAM mode (10x faster)
USE_MEMORY_DB=true
```

## Next Steps

- [Architecture](architecture.md) - How robairagapi works internally
- [Configuration](configuration.md) - Complete configuration reference
- [API Reference](api-reference.md) - All endpoints documented
