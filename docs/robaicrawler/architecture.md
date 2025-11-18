---
layout: default
title: Architecture
parent: robaicrawler
nav_order: 4
---

# Architecture

Comprehensive guide to robaicrawler's architecture, data flow, and integration patterns within the robaitools ecosystem.

## Design Overview

robaicrawler is designed as a **stateless microservice** that serves as the foundational data ingestion layer for the entire RAG system. It operates independently with zero upstream dependencies, making it the critical first service in the dependency chain.

**Core Design Principles:**

1. **Stateless Operation**
   - No persistent storage in the container
   - All state managed by downstream services (robaitragmcp)
   - Enables horizontal scaling and easy restarts

2. **Single Responsibility**
   - Focus on web content extraction only
   - Delegates storage to downstream services
   - Delegates security checks to calling services

3. **Progressive Fallback**
   - Multiple retry strategies for problematic sites
   - Graceful degradation when features fail
   - Always returns useful data or clear error

4. **Host Networking**
   - Direct localhost communication (no Docker bridge)
   - Low-latency access for frequent calls
   - Simpler networking configuration

## System Position

### Dependency Tree

```
Level 0: robaicrawler ← CRITICAL PATH (no dependencies)
    ↓
Level 1: neo4j (waits for crawl4ai healthy)
    ↓
Level 2: kg-service (waits for neo4j)
         robaitragmcp (waits for crawl4ai + kg-service)
    ↓
Level 3: robairagapi (waits for robaitragmcp)
    ↓
Level 4: open-webui (optional UI)
```

**Why This Matters:**
- If robaicrawler fails, the entire stack cannot start
- Health checks propagate upward (dependent services wait)
- Restart robaicrawler → triggers dependent service reconnection

### Integration Points

**Incoming Connections:**
1. **robaitragmcp (MCP Server)** - Primary consumer
   - Calls via Crawl4AIRAG facade from robaimodeltools
   - Three main tools: crawl_url, crawl_and_store, deep_crawl_and_store
   - HTTP POST to `http://localhost:11235/crawl`

2. **robairagapi (REST API)** - Secondary consumer
   - Forwards MCP tool calls from open-webui
   - Same endpoint usage as robaitragmcp

3. **robaiproxy (API Gateway)** - Indirect consumer
   - Orchestrates research mode (2-4 iterations)
   - Calls via robaitragmcp MCP tools
   - No direct HTTP connection

**Outgoing Connections:**
- None (stateless service)
- All storage handled by calling services

## Components

### Docker Container

**Image Details:**
- **Base:** unclecode/crawl4ai:latest (community image)
- **Platform:** linux/amd64
- **Engine:** Headless Chrome (Playwright-based)
- **Size:** ~2GB (includes Chrome + Python dependencies)

**Container Configuration:**
```yaml
container_name: robaicrawl4ai
restart: unless-stopped
network_mode: host
shm_size: 1gb  # Required for Chrome shared memory
```

**Why Shared Memory (shm)?**
- Headless Chrome uses shared memory for rendering
- Default 64MB is insufficient (crashes on complex pages)
- 1GB allows concurrent tabs and large DOM trees

### HTTP API Server

**Framework:** FastAPI (Python)
**Port:** 11235
**Endpoints:**
1. `GET /health` - Health check (returns 200 OK)
2. `POST /crawl` - Main crawl endpoint

**Request Processing:**
1. Accept JSON payload with URLs and options
2. Launch headless Chrome instance
3. Navigate to URL and wait for JavaScript execution
4. Extract content and convert to markdown
5. Return JSON response with content + metadata

### Headless Chrome Engine

**Technology:** Playwright (Chromium-based)

**Process Flow:**
1. Browser pool: Pre-warmed Chrome instances
2. New tab per request (parallel processing)
3. JavaScript rendering: Waits for dynamic content
4. DOM extraction: Full page HTML after JS execution
5. Tab cleanup: Closes after content extraction

**JavaScript Handling:**
- Waits for network idle (no active requests)
- Executes all inline and external scripts
- Handles AJAX/fetch updates
- Timeout: 30 seconds default

### Content Extraction Pipeline

**Stage 1: HTML Cleaning**
- Remove `<script>`, `<style>`, `<nav>`, `<header>`, `<footer>` tags
- Remove `<form>` elements (optional)
- Filter by word count threshold (removes short text blocks)

**Stage 2: Markdown Conversion**
- Uses html2text library
- Preserves headings, lists, links, tables
- Two outputs: fit_markdown (cleaned), raw_markdown (full)

**Stage 3: Metadata Extraction**
- Title: `<title>` tag or `<h1>` fallback
- Images: All `<img>` src attributes
- Links: All `<a>` href attributes
- Status code: HTTP response code

## Data Flow

### Complete Request-Response Flow

```
┌─────────────────────────────────────────────────────────┐
│ 1. User Request via Chat Interface                     │
│    "[[autonomous]] crawl https://example.com"           │
└─────────────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│ 2. robaiproxy/robairagapi                               │
│    - Detect autonomous tag                              │
│    - Route to LLM with tool definitions                 │
└─────────────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│ 3. LLM Decision                                         │
│    - Decides to call crawler_crawl_and_store            │
│    - Extracts parameters: url, retention_policy, tags   │
└─────────────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│ 4. robaitragmcp (MCP Server)                            │
│    - Receives tool call request                         │
│    - Looks up tool: crawler_crawl_and_store             │
│    - Calls Crawl4AIRAG.crawl_and_store()                │
└─────────────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│ 5. Crawl4AIRAG Facade (robaimodeltools)                 │
│    - Delegates to crawl_operations.crawl_and_store()    │
│    - Pre-crawl security checks (SSRF, SQL injection)    │
│    - Domain blocking check                              │
└─────────────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│ 6. crawl_operations.crawl_url()                         │
│    - Calls robaicrawler via HTTP POST                   │
│    - Progressive fallback on failure                    │
└─────────────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│ 7. robaicrawler Service (THIS COMPONENT)                │
│    - Launch headless Chrome                             │
│    - Navigate to URL                                    │
│    - Wait for JavaScript execution                      │
│    - Extract content                                    │
│    - Convert to markdown                                │
│    - Return JSON: {success, markdown, metadata}         │
└─────────────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│ 8. Post-Crawl Processing (crawl_operations.py)          │
│    - Status code check (reject 4xx/5xx)                 │
│    - Error page detection                               │
│    - Content cleaning (remove navigation, images)       │
│    - Language detection (English only)                  │
└─────────────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│ 9. Storage Layer (storage.py)                           │
│    - SQLite: INSERT crawled_content table               │
│    - Generate embeddings (384-dim vectors)              │
│    - Queue for knowledge graph processing               │
└─────────────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│ 10. Return to User                                      │
│     {success: true, content_id: 123, url: "..."}        │
└─────────────────────────────────────────────────────────┘
```

### Data Transformations

**Stage 1: Raw HTML (from robaicrawler)**
```html
<!DOCTYPE html>
<html>
  <head><title>Example Domain</title></head>
  <body>
    <h1>Example Domain</h1>
    <p>This domain is for use in illustrative examples...</p>
  </body>
</html>
```

**Stage 2: Cleaned Markdown (fit_markdown)**
```markdown
# Example Domain

This domain is for use in illustrative examples in documents.
```

**Stage 3: Content Cleaning (ContentCleaner)**
```
Example Domain

This domain is for use in illustrative examples in documents.

[Removed: navigation links, social media buttons, footer]
[Cleaned: 1,247 characters → 89 characters (92.9% reduction)]
```

**Stage 4: Chunking (for embeddings)**
```
Chunk 1: "Example Domain\n\nThis domain is for use in..."
Chunk 2: (if content > 1,000 chars, split here)
```

**Stage 5: Vector Embeddings**
```
Chunk 1 → [0.123, -0.456, 0.789, ...] (384 dimensions)
Chunk 2 → [0.234, -0.567, 0.890, ...] (384 dimensions)
```

## Progressive Fallback Strategy

### Crawl Attempt Sequence

robaicrawler may fail on sites with complex layouts or aggressive markdown processing. The system uses a **3-attempt fallback strategy**:

**Attempt 1: Full Parameters (Most Aggressive)**
```json
{
  "urls": ["https://example.com"],
  "word_count_threshold": 10,
  "excluded_tags": ["nav", "header", "footer", "script", "style"],
  "remove_forms": true,
  "only_text": true
}
```

**If fails → Attempt 2: Without only_text (Less Aggressive)**
```json
{
  "urls": ["https://example.com"],
  "word_count_threshold": 10,
  "excluded_tags": ["nav", "header", "footer", "script", "style"],
  "remove_forms": true
  // Removed: only_text=true
}
```

**If fails → Attempt 3: Minimal Parameters (Most Permissive)**
```json
{
  "urls": ["https://example.com"],
  "excluded_tags": ["nav", "header", "footer", "script", "style"]
  // Removed: word_count_threshold, remove_forms, only_text
}
```

**If all fail → Return error:**
```json
{
  "success": false,
  "error": "Failed to crawl URL after 3 attempts",
  "url": "https://example.com"
}
```

### Why This Works

- **Attempt 1 failures:** Usually due to `only_text` breaking on rich media sites
- **Attempt 2 failures:** Usually due to `word_count_threshold` filtering all content
- **Attempt 3 failures:** Usually due to site blocking or network issues
- Each fallback increases success rate by ~15-20%
- Total success rate: ~85-90% of all URLs

## Security Architecture

### Four-Layer Defense System

**Layer 1: SSRF Protection (Pre-Crawl)**
```
validate_url(url) checks:
- Private IPs: 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
- Loopback: 127.0.0.0/8, ::1
- Link-local: 169.254.0.0/16
- Cloud metadata: 169.254.169.254 (AWS/GCP/Azure)
- Localhost variants: localhost, 0.0.0.0

If blocked → Return error before crawl
```

**Layer 2: SQL Injection Defense (Pre-Crawl)**
```
SQLInjectionDefense.sanitize_url(url) checks:
- SQL keywords: SELECT, DROP, INSERT, DELETE, etc.
- Encoded attacks: URL-encoded SQL patterns
- NULL bytes: %00, \x00
- Length limits: Max 2,000 characters

If detected → Return error before crawl
```

**Layer 3: Domain Blocking (Pre-Crawl)**
```
GLOBAL_DB.is_domain_blocked(url) checks:
- User blocklist: Configurable via add_blocked_domain()
- Pre-loaded patterns: Adult content keywords
- Wildcard support: *.ru, *spam*, exact matches

If blocked → Return error with reason
```

**Layer 4: Content Validation (Post-Crawl)**
```
After crawl success:
- Re-sanitize URL (may have redirected)
- Sanitize page title (SQL injection check)
- Language detection (English only)
- Error page detection (rate limits, redirects)
- Adult content filtering (deep crawl only)

If fails → Skip storage, log reason
```

## Deep Crawl Architecture

### BFS Algorithm

Deep crawl uses **breadth-first search** to explore multi-page sites:

**Data Structures:**
```
visited: Set of URLs already crawled
queue: Deque of (url, depth) tuples
stored_count: Counter for stored pages
```

**Algorithm:**
```
1. Initialize: queue = [(start_url, 0)]
2. While queue not empty AND stored_count < max_pages:
   a. Pop (url, depth) from queue
   b. Skip if visited or depth > max_depth
   c. Crawl URL via robaicrawler
   d. Check language (keyword-based)
   e. If English: store in database (stored_count++)
   f. Extract links from content
   g. Filter links (same domain, not social media)
   h. Add to queue: queue.append((link, depth + 1))
   i. Mark visited: visited.add(url)
3. Return {stored_count, skipped_count}
```

**Link Filtering:**
- **Domain check:** Same domain only (unless include_external=true)
- **Social media:** Filter facebook, twitter, youtube, instagram, etc.
- **Adult content:** Filter based on URL patterns
- **Duplicates:** Skip if in visited set
- **Depth limit:** Skip if depth > max_depth

### Performance Optimization

**Rate Limiting:**
- Delay between requests: 1-2 seconds (configurable)
- Prevents server overload and rate limiting responses
- Uses `asyncio.sleep()` between crawls

**Concurrent Crawling:**
- Multiple tabs in same Chrome instance
- Parallel processing of independent URLs
- Max concurrency: 5 tabs default

**Memory Management:**
- Tab cleanup after each crawl
- Browser restart every 100 pages
- Prevents memory leaks in long crawls

## Health Monitoring

### Health Check Mechanism

**From docker-compose.yml:**
```yaml
healthcheck:
  test: ["CMD-SHELL", "curl -f http://localhost:11235/health || exit 1"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 30s
```

**How It Works:**
1. Every 30 seconds, Docker runs: `curl -f http://localhost:11235/health`
2. If response is 200 OK → healthy
3. If response is error or timeout → unhealthy (after 3 retries)
4. Start period: 30 seconds grace period on startup

**Health States:**
- **starting:** First 30 seconds (grace period)
- **healthy:** Health check passing for 30+ seconds
- **unhealthy:** Health check failed 3 consecutive times

### Dependent Service Monitoring

**From robaitragmcp/core/health_monitor.py:**

The MCP server actively monitors robaicrawler container health:

**Monitoring Loop:**
```
Every 30 seconds:
1. Query Docker API for robaicrawl4ai container status
2. Check container state: running, restarting, exited
3. Check health status: healthy, unhealthy, starting
4. If restart detected: Trigger tool re-discovery
5. Log any state changes
```

**On Restart Detection:**
```
1. Log: "robaicrawl4ai restarted at {timestamp}"
2. Call: discovery_engine.discover_all_tools()
3. Update: Available MCP tools list
4. Notify: All connected clients
```

**Why This Matters:**
- Automatic tool re-discovery on service restart
- No manual intervention needed
- Tools always reflect current service state

## Performance Characteristics

### Response Times

**Single URL Crawl:**
- Simple page (example.com): 2-3 seconds
- Medium page (blog post): 4-6 seconds
- Complex page (SPA with JS): 8-10 seconds

**Breakdown:**
- Network request: 500-1000ms
- JavaScript execution: 1000-3000ms
- Content extraction: 500-1000ms
- Markdown conversion: 200-500ms

**Deep Crawl:**
- 10 pages: 30-40 seconds
- 50 pages: 90-120 seconds
- 100 pages: 180-240 seconds
- Rate limiting adds ~1-2s per page

### Resource Usage

**Memory:**
- Base container: 500MB
- Per Chrome tab: 100-200MB
- Peak (5 concurrent tabs): 1.5-2GB

**CPU:**
- Idle: <5%
- Single crawl: 20-40%
- 5 concurrent crawls: 80-100%

**Network:**
- Per page: 100KB-5MB (depends on content)
- Images not downloaded (src only extracted)
- JavaScript files downloaded (for execution)

## Error Handling

### Failure Modes

**1. Network Timeout**
- Cause: Target site slow or unresponsive
- Handling: Return error after 30s timeout
- User impact: Tool call fails, LLM tries alternative

**2. JavaScript Error**
- Cause: Page JavaScript throws exception
- Handling: Continue with partial content
- User impact: May miss dynamic content

**3. Chrome Crash**
- Cause: Out of memory or page too complex
- Handling: Restart browser, retry once
- User impact: ~5s delay, usually succeeds on retry

**4. HTTP Error (4xx/5xx)**
- Cause: Page not found or server error
- Handling: Return error with status code
- User impact: Tool call fails with clear error message

**5. Content Too Large**
- Cause: Page > 10MB HTML
- Handling: Truncate to first 10MB
- User impact: May miss end of page

### Error Responses

**Crawl Failure:**
```json
{
  "success": false,
  "error": "Failed to crawl URL: Connection timeout",
  "url": "https://example.com",
  "status_code": null
}
```

**Security Block:**
```json
{
  "success": false,
  "error": "Domain blocked: Adult content pattern",
  "url": "https://blocked-site.com",
  "blocked": true,
  "reason": "matches *.adult.*"
}
```

**Language Rejection:**
```json
{
  "success": false,
  "error": "Content not in English",
  "url": "https://example.fr",
  "detected_language": "fr"
}
```

## Scalability Considerations

### Horizontal Scaling

**Current Limitations:**
- Single instance per host (port 11235)
- No load balancing built-in
- Stateless design enables scaling

**Future Scaling Options:**
1. **Multiple ports:** Run multiple containers on 11235, 11236, 11237, etc.
2. **Load balancer:** nginx/HAProxy in front of crawler instances
3. **Service mesh:** Kubernetes with pod autoscaling

### Vertical Scaling

**Tuning for Higher Throughput:**
1. Increase shared memory: `shm_size: '2gb'` or `shm_size: '4gb'`
2. Increase CPU allocation: `cpus: '4'` in docker-compose
3. Increase memory limit: `mem_limit: '4g'`
4. Increase concurrent tabs: Modify Crawl4AI config

**Trade-offs:**
- More memory → more concurrent crawls
- More CPU → faster JavaScript execution
- Diminishing returns beyond 4 cores

## Integration Patterns

### Pattern 1: Synchronous Tool Call

Used for single URL crawls with immediate response:

```
User → LLM → MCP Server → Crawl4AIRAG → robaicrawler
                                             ↓
User ← LLM ← MCP Server ← Crawl4AIRAG ← Response
```

**Characteristics:**
- Blocking wait for response (2-10 seconds)
- User sees "processing" indicator
- Timeout: 30 seconds default

### Pattern 2: Research Mode (Multi-Iteration)

Used for automatic research with multiple crawls:

```
User → robaiproxy (orchestrator)
    ↓ Iteration 1
    Web Search (Serper) → 10 URLs
    For each URL: Crawl via robaicrawler (parallel)
    Accumulate context
    ↓ Iteration 2
    Generate follow-up query
    Web Search → 5 URLs
    For each URL: Crawl via robaicrawler (parallel)
    Accumulate context
    ↓ Generate Answer
    Return to user with full context
```

**Characteristics:**
- Non-blocking iterations
- Context accumulation (no truncation)
- Total time: 30-90 seconds for 2-4 iterations

### Pattern 3: Deep Crawl (Asynchronous)

Used for multi-page documentation crawling:

```
User → LLM → MCP Server → Crawl4AIRAG.deep_crawl_and_store()
                              ↓
                         BFS Loop (blocking)
                         For each page:
                           - Crawl via robaicrawler
                           - Store in database
                           - Extract links
                           - Add to queue
                              ↓
                         Return summary
User ← LLM ← MCP Server ← {stored: 47, skipped: 3}
```

**Characteristics:**
- Long-running operation (30-240 seconds)
- User sees "processing" for entire duration
- Stores all pages before returning

## Related Components

**Upstream (Callers):**
- robaitragmcp: MCP server with tool discovery
- robairagapi: REST API bridge
- robaiproxy: Research orchestration

**Downstream (Called):**
- None (stateless service)

**Parallel Services:**
- neo4j: Graph database (Level 1)
- kg-service: Knowledge graph extraction (Level 2)

**Shared Libraries:**
- robaimodeltools: Crawl4AIRAG facade, crawl_operations.py, deep_crawl.py
- robaimodeltools: storage.py, content_cleaner.py, validation.py

## Troubleshooting Architecture Issues

### Service Dependency Failures

**Symptom:** Dependent services stuck in "waiting" state

**Root Cause:** robaicrawler health check failing

**Investigation:**
```bash
# Check health endpoint
curl http://localhost:11235/health

# Check container status
docker compose ps crawl4ai

# View health check logs
docker inspect robaicrawl4ai | grep -A 10 "Health"
```

**Resolution:**
- Wait 60 seconds for health checks to pass
- Restart service: `docker compose restart crawl4ai`
- Check logs for errors: `docker compose logs crawl4ai`

### Tool Discovery Failures

**Symptom:** MCP server reports "crawler_crawl_url tool not found"

**Root Cause:** Tool discovery failed or service restart not detected

**Investigation:**
```bash
# Check MCP server logs
docker compose logs robaitragmcp | grep "discover"

# Check health monitor logs
docker compose logs robaitragmcp | grep "health_monitor"

# Verify crawler is healthy
docker compose ps crawl4ai
```

**Resolution:**
- Wait 30 seconds for automatic re-discovery
- Restart MCP server: `docker compose restart robaitragmcp`
- Tool discovery should trigger automatically

### Memory Issues

**Symptom:** Container crashes with "Killed" message

**Root Cause:** Insufficient shared memory or total memory

**Investigation:**
```bash
# Check current shm_size
docker inspect robaicrawl4ai | grep -i shm

# Check memory limits
docker stats robaicrawl4ai
```

**Resolution:**
1. Increase shm_size in docker-compose.yml: `shm_size: '2gb'`
2. Increase memory limit: `mem_limit: '4g'`
3. Restart service: `docker compose up -d --force-recreate crawl4ai`

## Best Practices

**For Operators:**
1. Monitor health check status regularly
2. Set alerts for "unhealthy" state
3. Allocate 2GB RAM minimum (4GB recommended)
4. Use host networking for best performance
5. Restart weekly to prevent memory leaks

**For Developers:**
1. Always use Crawl4AIRAG facade (don't call directly)
2. Handle errors gracefully (network failures common)
3. Use progressive fallback strategy
4. Respect rate limits (1-2s between requests)
5. Log all crawl attempts for debugging

**For Integrators:**
1. Wait for service_healthy before calling
2. Implement timeout handling (30s default)
3. Use MCP tools (not direct HTTP calls)
4. Cache results to reduce load
5. Monitor dependent service restarts
