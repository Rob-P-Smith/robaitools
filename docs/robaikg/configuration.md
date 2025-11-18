---
layout: default
title: Configuration
parent: robaikg
nav_order: 3
---

# Configuration

Complete configuration reference for robaikg knowledge graph service.

## Environment Variables

All configuration is managed through environment variables, typically set in the `.env` file at the repository root.

### Service Configuration

**KG_SERVICE_PORT**
- Type: Integer
- Default: `8088`
- Description: HTTP API port for kg-service
- Example: `KG_SERVICE_PORT=8088`

**API_HOST**
- Type: String
- Default: `0.0.0.0`
- Description: Bind address for kg-service
- Example: `API_HOST=0.0.0.0` (all interfaces)

**DEBUG**
- Type: Boolean
- Default: `false`
- Description: Enable debug mode (auto-reload, verbose logging)
- Example: `DEBUG=true`

**LOG_LEVEL**
- Type: String
- Default: `INFO`
- Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`
- Description: Logging verbosity level
- Example: `LOG_LEVEL=INFO`

### Neo4j Configuration

**NEO4J_URI**
- Type: String
- Default: `bolt://localhost:7687`
- Description: Neo4j Bolt protocol connection string
- Example: `NEO4J_URI=bolt://localhost:7687`
- Note: Use `bolt://` for unencrypted, `bolt+s://` for encrypted

**NEO4J_USER**
- Type: String
- Default: `neo4j`
- Description: Neo4j authentication username
- Example: `NEO4J_USER=neo4j`

**NEO4J_PASSWORD**
- Type: String
- Default: `knowledge_graph_2024`
- Description: Neo4j authentication password
- Example: `NEO4J_PASSWORD=your_secure_password`
- **Security:** Change from default in production

**NEO4J_DATABASE**
- Type: String
- Default: `neo4j`
- Description: Neo4j database name (Enterprise Edition supports multiple)
- Example: `NEO4J_DATABASE=neo4j`

**NEO4J_HEAP_MAX_SIZE**
- Type: String
- Default: `16G`
- Description: Maximum JVM heap size for Neo4j
- Example: `NEO4J_HEAP_MAX_SIZE=16G`
- Recommendations:
  - 8GB system: `2G`
  - 16GB system: `8G`
  - 32GB+ system: `16G`

**NEO4J_PAGECACHE_SIZE**
- Type: String
- Default: `2G`
- Description: Neo4j page cache size for disk access
- Example: `NEO4J_PAGECACHE_SIZE=2G`
- Recommendations:
  - 8GB system: `1G`
  - 16GB system: `2G`
  - 32GB+ system: `4G`

### vLLM Configuration

**AUGMENT_LLM_URL**
- Type: String
- Default: `http://localhost:8078`
- Description: vLLM server base URL for entity/relationship extraction
- Example: `AUGMENT_LLM_URL=http://192.168.10.50:8078`
- Note: Must be accessible from kg-service container

**VLLM_TIMEOUT**
- Type: Integer (seconds)
- Default: `1800` (30 minutes)
- Description: Timeout for vLLM extraction requests
- Example: `VLLM_TIMEOUT=3600` (1 hour for very large documents)
- Recommendations:
  - Small docs (< 10K words): `600` (10 min)
  - Medium docs (10-50K words): `1800` (30 min)
  - Large docs (> 50K words): `3600` (1 hour)

### Extraction Configuration

**ENTITY_MIN_CONFIDENCE**
- Type: Float (0.0 - 1.0)
- Default: `0.4`
- Description: Minimum confidence threshold for entity extraction
- Example: `ENTITY_MIN_CONFIDENCE=0.45`
- Impact:
  - Lower (0.3): More entities, more noise
  - Default (0.4): Balanced precision/recall
  - Higher (0.6): Fewer entities, higher precision

**RELATION_MIN_CONFIDENCE**
- Type: Float (0.0 - 1.0)
- Default: `0.45`
- Description: Minimum confidence threshold for relationship extraction
- Example: `RELATION_MIN_CONFIDENCE=0.5`
- Impact:
  - Lower (0.3): More relationships, more noise
  - Default (0.45): Balanced precision/recall
  - Higher (0.6): Fewer relationships, higher accuracy

### Background Worker Configuration

**KG_NUM_WORKERS**
- Type: Integer
- Default: `1`
- Description: Number of concurrent queue processing workers
- Example: `KG_NUM_WORKERS=2`
- Recommendations:
  - Light load (< 100 docs/hour): `1`
  - Medium load (100-500 docs/hour): `2`
  - Heavy load (> 500 docs/hour): `4`
- **Warning:** More than 4 workers may cause SQLite lock contention

**KG_POLL_INTERVAL**
- Type: Float (seconds)
- Default: `5.0`
- Description: Seconds between queue polling attempts
- Example: `KG_POLL_INTERVAL=10.0`
- Impact:
  - Lower (2.0): Faster pickup, more CPU usage
  - Default (5.0): Balanced responsiveness
  - Higher (15.0): Slower pickup, less CPU usage

**KG_BATCH_SIZE**
- Type: Integer
- Default: `5`
- Description: Number of queue items claimed per poll
- Example: `KG_BATCH_SIZE=10`
- **Note:** Not configurable via environment (hardcoded in worker)

**KG_DASHBOARD_ENABLED**
- Type: Boolean
- Default: `true`
- Description: Enable web dashboard on port 8090
- Example: `KG_DASHBOARD_ENABLED=false`

### Database Configuration

**DB_PATH**
- Type: String
- Default: `/data/crawl4ai_rag.db`
- Description: Path to SQLite database file
- Example: `DB_PATH=/mnt/data/crawl4ai_rag.db`
- **Note:** Must be accessible from kg-service container

**USE_MEMORY_DB**
- Type: Boolean
- Default: `true`
- Description: Use in-memory SQLite with differential sync
- Example: `USE_MEMORY_DB=false`
- Impact:
  - `true`: 10x faster, requires RAM
  - `false`: Slower, no extra RAM needed

### Authentication Configuration

**OPENAI_API_KEY**
- Type: String
- Required: Yes
- Description: API key for queue endpoint authentication
- Example: `OPENAI_API_KEY=sk-your-api-key-here`
- **Security:** Keep secret, rotate regularly

## Configuration Profiles

### Development Profile

**Purpose:** Local development with minimal resource usage.

```bash
# Service
DEBUG=true
LOG_LEVEL=DEBUG

# Neo4j (lightweight)
NEO4J_HEAP_MAX_SIZE=2G
NEO4J_PAGECACHE_SIZE=1G

# vLLM
VLLM_TIMEOUT=600

# Extraction (permissive)
ENTITY_MIN_CONFIDENCE=0.3
RELATION_MIN_CONFIDENCE=0.3

# Workers (single)
KG_NUM_WORKERS=1
KG_POLL_INTERVAL=10.0
KG_DASHBOARD_ENABLED=true

# Database (disk mode)
USE_MEMORY_DB=false
```

**Characteristics:**
- Low memory usage (~2GB total)
- Slower processing (disk I/O)
- More entities/relationships (lower thresholds)
- Single worker, slow polling
- Dashboard enabled for monitoring

### Production Profile

**Purpose:** High-throughput production deployment.

```bash
# Service
DEBUG=false
LOG_LEVEL=INFO

# Neo4j (optimized)
NEO4J_HEAP_MAX_SIZE=16G
NEO4J_PAGECACHE_SIZE=4G

# vLLM
VLLM_TIMEOUT=1800

# Extraction (balanced)
ENTITY_MIN_CONFIDENCE=0.4
RELATION_MIN_CONFIDENCE=0.45

# Workers (parallel)
KG_NUM_WORKERS=4
KG_POLL_INTERVAL=5.0
KG_DASHBOARD_ENABLED=true

# Database (RAM mode)
USE_MEMORY_DB=true
```

**Characteristics:**
- High memory usage (~20GB total)
- Fast processing (RAM + multiple workers)
- Balanced precision/recall
- 4 workers, fast polling
- Dashboard for monitoring

### High-Precision Profile

**Purpose:** Maximize extraction quality over speed.

```bash
# Extraction (strict)
ENTITY_MIN_CONFIDENCE=0.6
RELATION_MIN_CONFIDENCE=0.65

# vLLM (allow more time)
VLLM_TIMEOUT=3600

# Workers (sequential, careful)
KG_NUM_WORKERS=1
KG_POLL_INTERVAL=10.0
```

**Characteristics:**
- Fewer but higher-quality entities/relationships
- Longer processing time per document
- Single worker prevents concurrent processing
- Suitable for critical documents

### High-Throughput Profile

**Purpose:** Maximum documents processed per hour.

```bash
# Neo4j (max resources)
NEO4J_HEAP_MAX_SIZE=24G
NEO4J_PAGECACHE_SIZE=8G

# Workers (maximum safe)
KG_NUM_WORKERS=4
KG_POLL_INTERVAL=2.0

# Database (RAM mode required)
USE_MEMORY_DB=true

# vLLM (aggressive timeout)
VLLM_TIMEOUT=900  # 15 min (may skip very large docs)
```

**Characteristics:**
- ~600-800 docs/hour (depending on doc size)
- Requires 32GB+ system RAM
- Fast polling, max workers
- May timeout on very large documents

## Docker Configuration

### Docker Compose Settings

**Container Name:**
```yaml
services:
  kg-service:
    container_name: robaikg
```

**Network Mode:**
```yaml
network_mode: "host"  # Direct localhost access
```

**Volumes:**
```yaml
volumes:
  - ../robaivenv:/robaivenv                    # Python environment
  - ../robaimodeltools:/robaimodeltools        # Shared library
  - ../robaidata:/data                         # SQLite database
  - ../robaikg/coordinator:/robaikg/coordinator # Workers
```

**Environment File:**
```yaml
env_file:
  - ../.env  # Load from repository root
```

**Health Check:**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8088/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### Neo4j Docker Settings

**Container Name:**
```yaml
services:
  neo4j:
    container_name: robaineo4j
```

**Image:**
```yaml
image: neo4j:5.25-community
```

**Ports:**
```yaml
ports:
  - "7474:7474"  # HTTP (Browser)
  - "7687:7687"  # Bolt (Driver)
```

**Environment:**
```yaml
environment:
  - NEO4J_AUTH=${NEO4J_USER}/${NEO4J_PASSWORD}
  - NEO4J_dbms_memory_heap_max__size=${NEO4J_HEAP_MAX_SIZE}
  - NEO4J_dbms_memory_pagecache_size=${NEO4J_PAGECACHE_SIZE}
  - NEO4J_dbms_security_procedures_unrestricted=apoc.*
  - NEO4J_dbms_security_procedures_allowlist=apoc.*
```

**Volumes:**
```yaml
volumes:
  - neo4j_data:/data      # Graph database files
  - neo4j_logs:/logs      # Log files
  - neo4j_import:/import  # Import directory
```

## Performance Tuning

### Optimizing Processing Speed

**Problem:** Documents processing too slowly

**Solutions:**

1. **Increase workers:**
   ```bash
   KG_NUM_WORKERS=4  # Up to 4 recommended
   ```

2. **Enable RAM mode:**
   ```bash
   USE_MEMORY_DB=true
   ```

3. **Reduce polling interval:**
   ```bash
   KG_POLL_INTERVAL=2.0  # Poll more frequently
   ```

4. **Lower confidence thresholds:**
   ```bash
   ENTITY_MIN_CONFIDENCE=0.3  # Accept more entities
   RELATION_MIN_CONFIDENCE=0.35
   ```

### Optimizing Memory Usage

**Problem:** System running out of memory

**Solutions:**

1. **Reduce Neo4j heap:**
   ```bash
   NEO4J_HEAP_MAX_SIZE=4G   # From 16G
   NEO4J_PAGECACHE_SIZE=1G  # From 4G
   ```

2. **Disable RAM mode:**
   ```bash
   USE_MEMORY_DB=false  # Use disk SQLite
   ```

3. **Reduce workers:**
   ```bash
   KG_NUM_WORKERS=1  # Single worker
   ```

4. **Limit concurrent extractions:**
   - Reduce KG_NUM_WORKERS
   - Increase KG_POLL_INTERVAL

### Optimizing Extraction Quality

**Problem:** Too many low-quality entities/relationships

**Solutions:**

1. **Increase confidence thresholds:**
   ```bash
   ENTITY_MIN_CONFIDENCE=0.6
   RELATION_MIN_CONFIDENCE=0.65
   ```

2. **Increase vLLM timeout:**
   ```bash
   VLLM_TIMEOUT=3600  # Allow more processing time
   ```

3. **Use single worker:**
   ```bash
   KG_NUM_WORKERS=1  # Sequential processing
   ```

### Handling Large Documents

**Problem:** Timeouts on documents > 50K words

**Solutions:**

1. **Increase vLLM timeout:**
   ```bash
   VLLM_TIMEOUT=3600  # 1 hour instead of 30 min
   ```

2. **Check vLLM server capacity:**
   ```bash
   curl http://localhost:8088/api/v1/extraction/status
   ```

3. **Monitor extraction metrics:**
   - `active_extractions` should be < `max_concurrent`
   - If at capacity, reduce KG_NUM_WORKERS

## Monitoring Configuration

### Health Check Endpoints

**Service health:**
```bash
curl http://localhost:8088/health

# Returns:
{
  "status": "healthy",
  "services": {
    "neo4j": "connected",
    "vllm": "connected (model_name)",
    "llm_extraction": "available"
  },
  "uptime_seconds": 3600.5
}
```

**Service statistics:**
```bash
curl http://localhost:8088/stats

# Returns:
{
  "total_documents_processed": 523,
  "total_entities_extracted": 45234,
  "total_relationships_extracted": 12456,
  "avg_processing_time_ms": 2341.5,
  "failed_count": 2
}
```

**Extraction status:**
```bash
curl http://localhost:8088/api/v1/extraction/status

# Returns:
{
  "status": "healthy",
  "active_extractions": 2,
  "total_queued": 1234,
  "total_completed": 1200,
  "total_failed": 12,
  "max_concurrent": 4,
  "slots_available": 2
}
```

### Dashboard Configuration

**Enable/disable:**
```bash
KG_DASHBOARD_ENABLED=true
```

**Access:**
- URL: http://localhost:8090
- Auto-refresh: Every 30 seconds
- No authentication required (internal use only)

**Metrics displayed:**
- Queue status distribution
- Processing throughput
- Success/failure rates
- Long-running items alert

**Security:** Dashboard runs on separate port, should only be accessible internally.

## Security Configuration

### API Authentication

**Configure API key:**
```bash
OPENAI_API_KEY=your-secret-key-here
```

**Protected endpoints:**
- POST /api/v1/queue/claim-items
- GET /api/v1/queue/chunks/{id}
- POST /api/v1/queue/write-results
- POST /api/v1/queue/mark-*
- GET /api/v1/queue/stats
- GET /api/v1/queue/long-running

**Usage:**
```bash
curl http://localhost:8088/api/v1/queue/stats \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Neo4j Security

**Change default password:**
```bash
NEO4J_PASSWORD=your_secure_password_here
```

**Network isolation:**
- Default: Accessible on localhost only
- Production: Consider firewall rules

**Bolt encryption:**
```bash
# Enable TLS for Bolt protocol
NEO4J_URI=bolt+s://localhost:7687
```

### Input Validation

**Automatic validation via Pydantic:**
- URL format validation
- Content ID > 0
- Chunk ordering validation
- Text length limits (max 1M chars)

**No additional configuration needed.**

## Troubleshooting Configuration

### Issue: Service won't start

**Check:**
1. Environment variables loaded:
   ```bash
   docker compose logs robaikg | grep "Service: kg-service"
   ```

2. Neo4j connection:
   ```bash
   docker compose logs robaikg | grep "Neo4j:"
   ```

3. vLLM connection:
   ```bash
   docker compose logs robaikg | grep "Augmentation LLM:"
   ```

### Issue: "Database not initialized"

**Cause:** Database instance not registered before API calls.

**Solution:** Wait 10-15 seconds after startup, or check logs:
```bash
docker compose logs robaikg | grep "Database initialized"
```

### Issue: High memory usage

**Diagnosis:**
```bash
docker stats robaikg robaineo4j
```

**Solutions:**
1. Reduce NEO4J_HEAP_MAX_SIZE
2. Reduce NEO4J_PAGECACHE_SIZE
3. Set USE_MEMORY_DB=false
4. Reduce KG_NUM_WORKERS

### Issue: Extraction timeouts

**Diagnosis:**
```bash
docker compose logs robaikg | grep "timeout"
```

**Solutions:**
1. Increase VLLM_TIMEOUT
2. Check vLLM server status:
   ```bash
   curl http://localhost:8078/health
   ```
3. Monitor extraction capacity:
   ```bash
   curl http://localhost:8088/api/v1/extraction/status
   ```

## Configuration Best Practices

### Development

1. **Use disk mode:** `USE_MEMORY_DB=false` (easier debugging)
2. **Enable debug logging:** `LOG_LEVEL=DEBUG`
3. **Lower thresholds:** More results, faster iteration
4. **Single worker:** Easier to trace issues
5. **Enable dashboard:** Monitor queue status

### Production

1. **Use RAM mode:** `USE_MEMORY_DB=true` (10x faster)
2. **Optimize Neo4j:** Allocate appropriate heap/pagecache
3. **Multiple workers:** Scale to throughput needs
4. **Balanced thresholds:** Default 0.4/0.45 works well
5. **Monitor metrics:** Set up health check alerts

### Security

1. **Change default passwords:** NEO4J_PASSWORD, OPENAI_API_KEY
2. **Restrict network access:** Use firewall rules
3. **Rotate API keys:** Regularly update OPENAI_API_KEY
4. **Disable debug mode:** `DEBUG=false` in production
5. **Monitor logs:** Watch for authentication failures

## Configuration Reference Table

| Variable | Default | Type | Required | Description |
|----------|---------|------|----------|-------------|
| KG_SERVICE_PORT | 8088 | int | No | HTTP API port |
| API_HOST | 0.0.0.0 | str | No | Bind address |
| DEBUG | false | bool | No | Debug mode |
| LOG_LEVEL | INFO | str | No | Log verbosity |
| NEO4J_URI | bolt://localhost:7687 | str | Yes | Neo4j connection |
| NEO4J_USER | neo4j | str | Yes | Neo4j username |
| NEO4J_PASSWORD | knowledge_graph_2024 | str | Yes | Neo4j password |
| NEO4J_HEAP_MAX_SIZE | 16G | str | No | JVM heap size |
| NEO4J_PAGECACHE_SIZE | 2G | str | No | Page cache size |
| AUGMENT_LLM_URL | http://localhost:8078 | str | Yes | vLLM server URL |
| VLLM_TIMEOUT | 1800 | int | No | vLLM timeout (seconds) |
| ENTITY_MIN_CONFIDENCE | 0.4 | float | No | Entity threshold |
| RELATION_MIN_CONFIDENCE | 0.45 | float | No | Relationship threshold |
| KG_NUM_WORKERS | 1 | int | No | Worker count |
| KG_POLL_INTERVAL | 5.0 | float | No | Poll interval (seconds) |
| KG_DASHBOARD_ENABLED | true | bool | No | Enable dashboard |
| DB_PATH | /data/crawl4ai_rag.db | str | Yes | SQLite database path |
| USE_MEMORY_DB | true | bool | No | RAM mode |
| OPENAI_API_KEY | - | str | Yes | API authentication |

## Next Steps

- **Architecture Details:** See [Architecture](architecture.md) for how configuration affects system behavior
- **API Usage:** Review [API Reference](api-reference.md) for endpoint-specific configuration
- **Deployment:** Plan production configuration based on workload
