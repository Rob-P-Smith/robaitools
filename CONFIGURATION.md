# RobAI Tools - Centralized Configuration Guide

## Overview

All RobAI Tools services are now configured through a **single centralized `.env` file** located at the root of the robaitools directory. This simplifies deployment and makes it easy to manage all environment variables in one place.

---

## Quick Start

1. **Copy the template:**
   ```bash
   cd /home/robiloo/Documents/robaitools
   cp .env.example .env
   ```

2. **Edit `.env` with your values:**
   ```bash
   nano .env  # or use your preferred editor
   ```

3. **Start all services:**
   ```bash
   docker compose up -d
   ```

---

## Configuration File Structure

The `.env` file is organized into logical sections:

### 1. **Core Services** (Shared Infrastructure)
- **vLLM** - Large Language Model inference
- **Crawl4AI** - Web scraping service
- **Neo4j** - Knowledge Graph database
- **KG Service** - Knowledge Graph processing

### 2. **RAG System** (MCP Server & API)
- **robaitragmcp** - MCP server for RAG operations
- **robairagapi** - REST API bridge to MCP

### 3. **Proxy Service**
- **robaiproxy** - Request router with research capabilities

### 4. **Deployment Configuration**
- Docker Compose settings
- Volume paths
- Model cache locations

---

## Key Environment Variables

### Must Configure

These variables **must be set** for the system to work:

```bash
# Neo4j Authentication
NEO4J_PASSWORD=knowledge_graph_2024  # Change this!

# API Keys
LOCAL_API_KEY=your-secret-api-key-here  # Change this!
BLOCKED_DOMAIN_KEYWORD=your-secret-keyword-here  # Change this!

# Optional: External APIs
SERPER_API_KEY=your-serper-api-key-here  # For web search
REST_API_KEY=your-mcp-api-key-here  # For proxy → MCP auth
```

### Service Ports

Default port assignments (modify if needed):

| Service | Port | Description |
|---------|------|-------------|
| vLLM | 8078 | OpenAI-compatible LLM API |
| Research Proxy | 8079 | Request router |
| RAG API Bridge | 8080 | REST API for RAG |
| KG Service | 8088 | Knowledge Graph API |
| MCP Server | 3000 | Internal MCP protocol (TCP) |
| Neo4j Browser | 7474 | Neo4j web interface |
| Neo4j Bolt | 7687 | Neo4j database connection |
| Crawl4AI | 11235 | Web crawling service |

### Resource Limits

Adjust based on your system RAM:

```bash
# Neo4j Memory (default: 16GB heap + 2GB cache)
NEO4J_HEAP_INITIAL_SIZE=512m
NEO4J_HEAP_MAX_SIZE=16G        # Reduce if you have less RAM
NEO4J_PAGECACHE_SIZE=2G

# vLLM (configured in docker-compose.yml)
# GPU memory usage: 0.91 (91% of available VRAM)
```

---

## Service Dependencies

Understanding the startup order:

```
1. vllm-qwen3 (independent)
2. crawl4ai (independent)
3. neo4j → waits for crawl4ai network
4. kg-service → waits for neo4j + vllm-qwen3
5. robaitragmcp → waits for crawl4ai + kg-service
6. robairagapi → waits for robaitragmcp
7. robaiproxy (standalone, configured separately)
```

Docker Compose automatically manages these dependencies with health checks.

---

## Data Persistence

### Database Locations

All persistent data is stored in centralized locations:

```
robaitools/
├── robaidata/                    # Main data directory
│   ├── crawl4ai_rag.db          # RAG database (SQLite)
│   ├── crawl4ai.db              # Additional databases
│   └── knowledge.db
├── robaikg/
│   └── neo4j/
│       ├── data/                # Neo4j graph database
│       ├── logs/                # Neo4j logs
│       └── import/              # Import directory
└── robaikg/kg-service/
    └── models/                  # Cached ML models (GLiNER)
```

### Backup Strategy

To backup all data:

```bash
# Stop services
docker compose down

# Backup databases
tar czf robai-backup-$(date +%Y%m%d).tar.gz \
  robaidata/ \
  robaikg/neo4j/data/

# Restart services
docker compose up -d
```

---

## Advanced Configuration

### Memory Database Mode

The RAG database can run in RAM for faster performance:

```bash
USE_MEMORY_DB=true  # Default: enabled
```

**Benefits:**
- 10-100x faster queries
- Automatic background sync to disk
- No data loss

**Drawbacks:**
- Uses system RAM
- Slower startup (loads from disk)

### Entity Extraction Tuning

Adjust GLiNER entity extraction sensitivity:

```bash
GLINER_THRESHOLD=0.45      # Default: 0.45 (lower = more entities)
USE_GLINER_ENTITIES=true   # Enable/disable GLiNER
```

### Relationship Extraction

Control how relationships are extracted:

```bash
RELATION_MIN_CONFIDENCE=0.35     # Minimum confidence (0.0-1.0)
RELATION_MAX_DISTANCE=5          # Max sentence distance
RELATION_CONTEXT_WINDOW=100      # Context window size
```

### Query Logging

Enable Neo4j slow query logging:

```bash
NEO4J_QUERY_LOG_ENABLED=INFO           # Log level
NEO4J_QUERY_LOG_THRESHOLD=1s           # Log queries > 1 second
```

---

## Troubleshooting

### Services Won't Start

1. **Check env file exists:**
   ```bash
   ls -la /home/robiloo/Documents/robaitools/.env
   ```

2. **Validate env variables:**
   ```bash
   docker compose config
   ```

3. **Check logs:**
   ```bash
   docker compose logs -f [service-name]
   ```

### Database Connection Issues

**Symptom:** `kg-service` can't connect to Neo4j

**Solution:** Check Neo4j credentials match:
```bash
# In .env file:
NEO4J_USER=neo4j
NEO4J_PASSWORD=knowledge_graph_2024  # Must match!
NEO4J_URI=bolt://localhost:7687
```

### Port Conflicts

**Symptom:** "Port already in use"

**Solution:** Check what's using the port:
```bash
sudo netstat -tlnp | grep 8080  # Replace with your port
```

Either stop the conflicting service or change the port in `.env`:
```bash
RAGAPI_SERVER_PORT=8081  # Use different port
```

### Out of Memory

**Symptom:** Neo4j or services crash

**Solution:** Reduce memory limits in `.env`:
```bash
NEO4J_HEAP_MAX_SIZE=8G         # Reduce from 16G
NEO4J_PAGECACHE_SIZE=1G        # Reduce from 2G
```

---

## Environment Variable Reference

### Complete List by Service

#### vLLM (robaivllm)
```bash
VLLM_BASE_URL=http://localhost:8078
VLLM_TIMEOUT=1800
VLLM_MAX_TOKENS=65536
VLLM_TEMPERATURE=0.1
```

#### Crawl4AI (robaicrawler)
```bash
CRAWL4AI_URL=http://localhost:11235
```

#### Neo4j (robaikg/neo4j)
```bash
NEO4J_USER=neo4j
NEO4J_PASSWORD=knowledge_graph_2024
NEO4J_URI=bolt://localhost:7687
NEO4J_DATABASE=neo4j
NEO4J_HEAP_INITIAL_SIZE=512m
NEO4J_HEAP_MAX_SIZE=16G
NEO4J_PAGECACHE_SIZE=2G
```

#### KG Service (robaikg/kg-service)
```bash
KG_SERVICE_PORT=8088
KG_LOG_LEVEL=INFO
GLINER_MODEL=urchade/gliner_large-v2.1
GLINER_THRESHOLD=0.45
USE_GLINER_ENTITIES=true
```

#### MCP Server (robaitragmcp)
```bash
DB_PATH=/app/data/crawl4ai_rag.db
USE_MEMORY_DB=true
BLOCKED_DOMAIN_KEYWORD=your-secret-keyword
MCP_LOG_LEVEL=INFO
```

#### RAG API (robairagapi)
```bash
RAGAPI_SERVER_PORT=8080
LOCAL_API_KEY=your-secret-api-key
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=3000
```

#### Proxy (robaiproxy)
```bash
PROXY_PORT=8079
REST_API_URL=http://localhost:8080/api/v1
REST_API_KEY=your-mcp-api-key
SERPER_API_KEY=your-serper-api-key
```

---

## Migration from Individual .env Files

If you previously had `.env` files in individual project directories:

1. **Backup old files:**
   ```bash
   find robaitools -name ".env" -exec cp {} {}.bak \;
   ```

2. **Use centralized .env:**
   The new centralized `.env` at the root takes precedence

3. **Old files can be deleted** (but keep backups):
   ```bash
   # Optional: Remove old .env files
   rm robaiproxy/.env
   rm robairagapi/.env
   rm robaitragmcp/.env
   ```

---

## Security Best Practices

1. **Never commit `.env` to git:**
   ```bash
   # Already in .gitignore, but verify:
   cat .gitignore | grep ".env"
   ```

2. **Use strong passwords:**
   ```bash
   # Generate random passwords:
   openssl rand -base64 32
   ```

3. **Restrict API access:**
   ```bash
   # Use specific CORS origins instead of *
   CORS_ORIGINS=http://localhost:80,http://192.168.10.50:80
   ```

4. **Enable rate limiting:**
   ```bash
   ENABLE_RATE_LIMIT=true
   RATE_LIMIT_PER_MINUTE=60
   ```

---

## Further Reading

- [Docker Compose Environment Variables](https://docs.docker.com/compose/environment-variables/)
- [Neo4j Configuration](https://neo4j.com/docs/operations-manual/current/configuration/)
- [vLLM Configuration](https://docs.vllm.ai/en/latest/)

---

**Questions or Issues?**
Check logs: `docker compose logs -f [service]`
Validate config: `docker compose config`
Full restart: `docker compose down && docker compose up -d`
