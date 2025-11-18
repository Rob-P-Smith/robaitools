---
layout: default
title: Getting Started
parent: robaicrawler
nav_order: 1
---

# Getting Started with robaicrawler

Learn how to install, configure, and use the robaicrawler web content extraction service.

## Prerequisites

**Required:**
- Docker and Docker Compose installed
- 2GB RAM minimum (1GB for shared memory, 1GB for Chrome)
- 2 CPU cores recommended for concurrent crawling
- Port 11235 available

**Optional:**
- Access to target websites (no firewall blocks)
- Serper API key (for research mode web search)

## Installation

### Step 1: Start the Service

robaicrawler is defined in the master `docker-compose.yml` at the repository root. Start it with all dependencies:

```bash
cd /path/to/robaitools
docker compose up -d crawl4ai
```

The service will:
- Pull the `unclecode/crawl4ai:latest` image from Docker Hub
- Start with host networking on port 11235
- Run health checks every 30 seconds
- Auto-restart unless explicitly stopped

### Step 2: Verify Health

Check that the service is running and healthy:

```bash
# Check container status
docker compose ps crawl4ai

# Test health endpoint
curl http://localhost:11235/health

# View logs
docker compose logs crawl4ai
```

Expected output: `200 OK` response from health endpoint and container status showing "healthy".

### Step 3: Verify Dependent Services

robaicrawler has no upstream dependencies, but downstream services depend on it. Check they're waiting for health:

```bash
# These services should show "waiting" until crawl4ai is healthy
docker compose ps neo4j
docker compose ps robaitragmcp
```

Once crawl4ai shows `service_healthy`, dependent services will automatically start.

## Basic Usage

### Direct API Call (Manual Testing)

Test the crawler directly via HTTP POST:

```bash
curl -X POST http://localhost:11235/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://docs.python.org/3/library/asyncio.html"],
    "word_count_threshold": 10,
    "excluded_tags": ["nav", "header", "footer", "script", "style"],
    "remove_forms": true,
    "only_text": true
  }'
```

**Response:**
```json
{
  "success": true,
  "results": [{
    "url": "https://docs.python.org/3/library/asyncio.html",
    "cleaned_html": "...",
    "markdown": {
      "fit_markdown": "# asyncio — Asynchronous I/O\n\nasyncio is a library to write concurrent code...",
      "raw_markdown": "..."
    },
    "metadata": {
      "title": "asyncio — Asynchronous I/O — Python 3.x documentation",
      "status_code": 200,
      "images": [...],
      "links": [...]
    }
  }]
}
```

### Via MCP Server (Recommended)

The primary way to use robaicrawler is through MCP tools exposed by robaitragmcp:

**Available Tools:**
- `crawler_crawl_url` - Single URL crawl with truncated content for LLM
- `crawler_crawl_and_store` - Crawl, clean, store in database, generate embeddings
- `crawler_deep_crawl_and_store` - Multi-page BFS crawl with filtering

**Example: Using Open WebUI Chat Interface**

1. Open chat interface at `http://localhost` or `http://192.168.10.50`
2. Use a tag to enable tool calling:
   ```
   [[autonomous]] crawl and store https://docs.python.org/3/library/asyncio.html
   ```
3. The system will:
   - Route to autonomous mode
   - Call `crawler_crawl_and_store` MCP tool
   - Crawl the URL via robaicrawler
   - Store content in SQLite database
   - Generate embeddings for semantic search
   - Queue for knowledge graph extraction
   - Return summary to chat

**Example: Deep Crawl**

```
[[autonomous]] deep crawl https://fastapi.tiangolo.com starting from the homepage,
crawl up to 30 pages with depth 3
```

This will use `crawler_deep_crawl_and_store` to:
- Start from homepage
- Follow links up to 3 levels deep
- Store up to 30 pages
- Filter out social media links and external domains
- Only process English content

### Via REST API

If using robairagapi REST API directly:

```bash
curl -X POST http://localhost:8081/api/v1/tools/call \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "tool_name": "crawler_crawl_and_store",
    "parameters": {
      "url": "https://docs.python.org/3/library/asyncio.html",
      "retention_policy": "permanent",
      "tags": "python,documentation,asyncio"
    }
  }'
```

## Understanding Data Flow

When you call `crawler_crawl_and_store`:

1. **Security Checks** (Pre-Crawl)
   - SSRF protection: Blocks private IPs, cloud metadata endpoints
   - SQL injection defense: Sanitizes URL parameters
   - Domain blocking: Checks user-configured blocklist

2. **Crawl Execution** (With Fallback)
   - Attempt 1: Full parameters (only_text=true, excluded_tags)
   - Attempt 2: Without only_text (if first fails)
   - Attempt 3: Minimal parameters (if second fails)
   - This handles sites with complex layouts

3. **Post-Crawl Processing**
   - Status code validation (reject 4xx/5xx)
   - Error page detection (rate limits, redirects)
   - Content cleaning (remove navigation, images, boilerplate)
   - Language detection (English-only for storage)

4. **Storage**
   - SQLite table: `crawled_content`
   - Content hash: Deduplication via SHA256
   - Metadata: JSON with cleaning stats, language, etc.

5. **Embedding Generation**
   - Chunking: 1,000-character chunks
   - Model: SentenceTransformer 'all-MiniLM-L6-v2' (384 dimensions)
   - Storage: `content_vectors` table with sqlite-vec extension

6. **Knowledge Graph Queue**
   - HTTP POST to kg-service dashboard
   - Triggers entity extraction (119 entity types via GLiNER)
   - Stores relationships in Neo4j

## Common Workflows

### Workflow 1: Research Mode (Automatic)

User types: "research python asyncio best practices"

1. robaiproxy detects research intent
2. Iteration 1: Web search via Serper API (10 results)
3. For each result URL: Call `crawler_crawl_url` (truncated for LLM)
4. Iteration 2: Follow-up search based on findings
5. Generate final answer with accumulated context

No explicit tool call needed - automatic orchestration.

### Workflow 2: Autonomous Tool Use (Manual)

User types: `[[autonomous]] store this page: https://example.com with tags "reference,tutorial"`

1. LLM decides to call `crawler_crawl_and_store`
2. Crawls URL via robaicrawler
3. Stores in database with tags
4. Returns: `{success: true, content_id: 123, url: "https://example.com"}`
5. LLM responds: "Stored page 'Example Domain' with ID 123. Tagged as reference, tutorial."

### Workflow 3: Deep Crawl for Documentation

User types: `[[autonomous]] build a knowledge base from https://fastapi.tiangolo.com, crawl all documentation pages`

1. LLM calls `crawler_deep_crawl_and_store`
2. BFS algorithm:
   - Start from homepage
   - Extract all links
   - Filter (same domain, not social media)
   - Crawl each page
   - Detect language (English only)
   - Store if passes checks
3. Returns: `{success: true, stored_count: 47, skipped_count: 3}`
4. All 47 pages now in database with embeddings and queued for KG

## Troubleshooting

### Service Won't Start

**Symptom:** `docker compose up -d crawl4ai` fails or shows "unhealthy"

**Solutions:**
1. Check Docker Hub connectivity: `docker pull unclecode/crawl4ai:latest`
2. Verify port 11235 is free: `lsof -i :11235`
3. Check shared memory allocation in docker-compose.yml: `shm_size: '1gb'`
4. View logs: `docker compose logs crawl4ai`

### Health Check Failing

**Symptom:** Container shows "unhealthy" status

**Solutions:**
1. Test health endpoint manually: `curl http://localhost:11235/health`
2. Wait 60 seconds (30s start period + 30s retry window)
3. Check logs for startup errors: `docker compose logs crawl4ai`
4. Restart: `docker compose restart crawl4ai`

### Crawl Request Times Out

**Symptom:** MCP tool call returns timeout error after 30+ seconds

**Solutions:**
1. Target URL may be slow/unresponsive - test directly: `curl -I https://target-url.com`
2. Check crawler logs: `docker compose logs crawl4ai | grep ERROR`
3. Increase timeout in request (if using direct API): `"timeout": 60`
4. Check network connectivity from container

### Content Not Storing

**Symptom:** `crawler_crawl_and_store` succeeds but content not in database

**Solutions:**
1. Check language detection - only English content stored
   - View logs: `docker compose logs robaitragmcp | grep "language"`
2. Check content cleaning - may be rejected as low-quality
   - View logs: `docker compose logs robaitragmcp | grep "quality"`
3. Check database file exists: `ls -lh robaidata/crawl4ai_rag.db`
4. Query database directly:
   ```bash
   sqlite3 robaidata/crawl4ai_rag.db "SELECT url, title FROM crawled_content ORDER BY id DESC LIMIT 5"
   ```

### Dependent Services Not Starting

**Symptom:** neo4j or robaitragmcp stuck in "waiting" state

**Solutions:**
1. Check crawl4ai health: `docker compose ps crawl4ai`
2. Must show "healthy" before dependent services start
3. If stuck, restart crawl4ai: `docker compose restart crawl4ai`
4. Wait up to 60 seconds for health check to pass

## Next Steps

1. **Configuration:** Learn about [environment variables and tuning options](configuration.md)
2. **Architecture:** Understand [data flow and integration patterns](architecture.md)
3. **API Reference:** Explore [all endpoints and parameters](api-reference.md)
4. **Advanced Features:** Configure domain blocking, retention policies, and deep crawl options

## Example: Complete First Crawl

```bash
# 1. Ensure service is running
docker compose ps crawl4ai
# Should show "healthy"

# 2. Test direct crawl
curl -X POST http://localhost:11235/crawl \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://example.com"]}'
# Should return success with markdown

# 3. Use via chat interface
# Open http://localhost
# Type: [[autonomous]] crawl and store https://example.com
# Should show success message with content ID

# 4. Verify storage
sqlite3 robaidata/crawl4ai_rag.db \
  "SELECT id, url, title FROM crawled_content WHERE url LIKE '%example.com%'"
# Should show stored record
```

Congratulations! You've successfully installed and used robaicrawler for web content extraction.
