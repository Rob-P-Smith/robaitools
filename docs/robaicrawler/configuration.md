---
layout: default
title: Configuration
parent: robaicrawler
nav_order: 2
---

# Configuration

Complete guide to configuring the robaicrawler service through environment variables, Docker compose settings, and runtime parameters.

## Environment Variables

robaicrawler reads configuration from the root `.env` file in the robaitools repository. All variables are prefixed with `CRAWL4AI_` to avoid conflicts.

### Core Service Configuration

**CRAWL4AI_PORT**
- **Type:** Integer
- **Default:** `11235`
- **Description:** HTTP port for the crawler API
- **Usage:** Set to different port if 11235 is in use
- **Example:** `CRAWL4AI_PORT=11236`

**CRAWL4AI_LOG_LEVEL**
- **Type:** String (DEBUG, INFO, WARNING, ERROR)
- **Default:** `INFO`
- **Description:** Logging verbosity for the crawler service
- **Usage:** Set to DEBUG for troubleshooting, WARNING for production
- **Example:** `CRAWL4AI_LOG_LEVEL=DEBUG`

**CRAWL4AI_CORS_ORIGINS**
- **Type:** Comma-separated list of URLs
- **Default:** `http://localhost:80,http://192.168.10.50:80,*`
- **Description:** Allowed origins for CORS requests
- **Usage:** Restrict in production to specific domains only
- **Example:** `CRAWL4AI_CORS_ORIGINS=https://app.example.com,https://dashboard.example.com`
- **Warning:** Using `*` allows all origins (insecure for production)

### Docker Configuration

**CRAWL4AI_SHM_SIZE**
- **Type:** Size string (e.g., 1gb, 2gb)
- **Default:** `1gb`
- **Description:** Shared memory allocation for headless Chrome
- **Usage:** Increase for concurrent crawling or complex pages
- **Example:** `CRAWL4AI_SHM_SIZE=2gb`
- **Impact:** Each Chrome tab uses ~100-200MB of shared memory

**CRAWL4AI_RESTART_POLICY**
- **Type:** String (no, always, unless-stopped, on-failure)
- **Default:** `unless-stopped`
- **Description:** Docker restart behavior
- **Usage:** `unless-stopped` recommended for production
- **Example:** `CRAWL4AI_RESTART_POLICY=always`

### Health Check Configuration

**CRAWL4AI_HEALTH_INTERVAL**
- **Type:** Duration string (e.g., 30s, 1m)
- **Default:** `30s`
- **Description:** Time between health check attempts
- **Usage:** Decrease for faster failure detection, increase to reduce load
- **Example:** `CRAWL4AI_HEALTH_INTERVAL=15s`

**CRAWL4AI_HEALTH_TIMEOUT**
- **Type:** Duration string
- **Default:** `10s`
- **Description:** Maximum time to wait for health check response
- **Usage:** Increase if health checks timing out on slow systems
- **Example:** `CRAWL4AI_HEALTH_TIMEOUT=15s`

**CRAWL4AI_HEALTH_RETRIES**
- **Type:** Integer
- **Default:** `3`
- **Description:** Number of consecutive failures before marking unhealthy
- **Usage:** Increase to tolerate transient failures
- **Example:** `CRAWL4AI_HEALTH_RETRIES=5`
- **Impact:** Total failure window = timeout × retries (e.g., 10s × 3 = 30s)

### Calling Service Configuration

These variables are used by services that call robaicrawler (robaimodeltools, robaitragmcp):

**CRAWL4AI_URL**
- **Type:** URL string
- **Default:** `http://localhost:11235`
- **Description:** Base URL for calling the crawler service
- **Usage:** Only change if using custom port or remote instance
- **Example:** `CRAWL4AI_URL=http://192.168.1.100:11235`

**MCP_CRAWL4AI_URL**
- **Type:** URL string
- **Default:** `http://localhost:11235`
- **Description:** Crawler URL specifically for MCP server
- **Usage:** Same as CRAWL4AI_URL, used by robaitragmcp
- **Example:** `MCP_CRAWL4AI_URL=http://localhost:11235`

**CRAWL_URL_MAX_CHARS**
- **Type:** Integer
- **Default:** `8000`
- **Description:** Maximum characters returned from crawl_url() to LLM
- **Usage:** Increase for longer content, decrease to reduce token usage
- **Example:** `CRAWL_URL_MAX_CHARS=12000`
- **Impact:** Does NOT affect crawl_and_store (always stores full content)

## Configuration Options

### Crawl Parameters

When calling robaicrawler via MCP tools or direct API, you can configure crawl behavior through parameters:

#### crawl_url() Parameters

**url** (required)
- Type: String
- Description: Target URL to crawl
- Validation: Must pass SSRF checks and domain blocking

**return_full_content** (optional)
- Type: Boolean
- Default: `false`
- Description: If true, returns full markdown without truncation
- Usage: Set to true for storage, false for LLM context

#### crawl_and_store() Parameters

**url** (required)
- Type: String
- Description: Target URL to crawl and store

**retention_policy** (optional)
- Type: String (permanent, session_only, 30_days)
- Default: `permanent`
- Description: How long to keep content in database
- Usage: `session_only` for temporary research, `permanent` for knowledge base

**tags** (optional)
- Type: Comma-separated string
- Default: Empty string
- Description: Tags for organizing stored content
- Example: `"python,documentation,asyncio"`
- Validation: Alphanumeric + commas only

#### deep_crawl_and_store() Parameters

**url** (required)
- Type: String
- Description: Starting URL for deep crawl

**retention_policy** (optional)
- Type: String
- Default: `permanent`
- Description: Retention policy for all crawled pages

**tags** (optional)
- Type: String
- Default: Empty string
- Description: Tags applied to all crawled pages

**max_depth** (optional)
- Type: Integer (1-5)
- Default: `2`
- Description: Maximum link depth to follow from start URL
- Usage: 1 = start page only, 2 = start + direct links, etc.

**max_pages** (optional)
- Type: Integer (1-250)
- Default: `10`
- Description: Maximum number of pages to store
- Usage: Prevents runaway crawls on large sites

**include_external** (optional)
- Type: Boolean
- Default: `false`
- Description: If true, follows links to external domains
- Warning: Can lead to very large crawls if enabled

### Docker Compose Configuration

The master `docker-compose.yml` defines the crawler service. You can modify these settings for advanced configuration:

#### Resource Limits

Add resource constraints to prevent runaway resource usage:

```yaml
crawl4ai:
  deploy:
    resources:
      limits:
        cpus: '4'           # Max 4 CPU cores
        memory: 4G          # Max 4GB RAM
      reservations:
        cpus: '1'           # Minimum 1 CPU core
        memory: 1G          # Minimum 1GB RAM
```

#### Network Configuration

robaicrawler uses host networking by default for best performance. Alternative bridge mode available if needed for isolation.

#### Security Configuration

Domain blocking and SSRF protection are configured through robaimodeltools library, not environment variables.
