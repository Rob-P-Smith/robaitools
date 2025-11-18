---
layout: default
title: Getting Started
parent: robaikg
nav_order: 2
---

# Getting Started with robaikg

Step-by-step guide to deploying and using the knowledge graph extraction service.

## Quick Start

### 1. Prerequisites

**Required Services:**
- Docker and Docker Compose
- Neo4j 5.25+ running (included in compose)
- vLLM server running on port 8078 (for LLM extraction)
- SQLite database at `/data/crawl4ai_rag.db`

**System Requirements:**
- RAM: 4GB minimum, 8GB recommended
- Disk: 2GB for Neo4j data
- CPU: 2+ cores recommended

### 2. Environment Configuration

Create or verify `.env` file in repository root:

```bash
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=knowledge_graph_2024
NEO4J_HEAP_MAX_SIZE=16G
NEO4J_PAGECACHE_SIZE=2G

# kg-service Configuration
KG_SERVICE_PORT=8088
AUGMENT_LLM_URL=http://localhost:8078
VLLM_TIMEOUT=1800

# Entity/Relationship Thresholds
ENTITY_MIN_CONFIDENCE=0.4
RELATION_MIN_CONFIDENCE=0.45

# Background Workers
KG_NUM_WORKERS=1
KG_POLL_INTERVAL=5.0
KG_DASHBOARD_ENABLED=true

# Authentication
OPENAI_API_KEY=your_api_key_here

# Database
DB_PATH=/data/crawl4ai_rag.db
```

### 3. Start Services

**Start Neo4j and kg-service:**
```bash
cd /home/robiloo/Documents/robaitools
docker compose up -d robaikg robaineo4j
```

**Verify services started:**
```bash
docker compose ps

# Should show:
# robaikg       running    8088/tcp
# robaineo4j    running    7474/tcp, 7687/tcp
```

**Check logs:**
```bash
docker compose logs -f robaikg

# Expected output:
# Starting kg-service
# Service: kg-service v1.0.0
# API: 0.0.0.0:8088
# Neo4j: bolt://localhost:7687
# Augmentation LLM: http://localhost:8078
# Entity Min Confidence: 0.4
# ✓ KG Processor initialized successfully
# Starting KG Workers
# ✓ Database initialized for workers
# ✓ KG workers started
# ✓ KG Dashboard started on http://0.0.0.0:8090
# ✓ kg-service ready
```

### 4. Verify Installation

**Health check:**
```bash
curl http://localhost:8088/health

# Response:
{
  "status": "healthy",
  "timestamp": "2025-11-18T12:00:00Z",
  "services": {
    "neo4j": "connected",
    "vllm": "connected (Qwen/Qwen2.5-7B-Instruct)",
    "llm_extraction": "available"
  },
  "version": "1.0.0",
  "uptime_seconds": 45.2
}
```

**Check Neo4j Browser:**
```bash
# Open in browser: http://localhost:7474
# Username: neo4j
# Password: knowledge_graph_2024

# Run test query:
MATCH (n) RETURN count(n) as node_count
```

**Check Dashboard:**
```bash
# Open in browser: http://localhost:8090
# View queue statistics and processing metrics
```

## Basic Workflows

### Workflow 1: Manual Document Processing

Send a document directly to kg-service for entity/relationship extraction.

**Step 1: Prepare document data**

Assume you have:
- content_id: 123 (from crawled_content table)
- URL: https://docs.fastapi.com
- Title: "FastAPI Documentation"
- Full markdown content
- Chunk boundaries with vector_rowids

**Step 2: Send to kg-service**

```bash
curl -X POST http://localhost:8088/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "content_id": 123,
    "url": "https://docs.fastapi.com",
    "title": "FastAPI Documentation",
    "markdown": "# FastAPI\n\nFastAPI is a modern, fast web framework...",
    "chunks": [
      {
        "vector_rowid": 45001,
        "chunk_index": 0,
        "char_start": 0,
        "char_end": 2500,
        "text": "# FastAPI\n\nFastAPI is a modern web framework..."
      },
      {
        "vector_rowid": 45002,
        "chunk_index": 1,
        "char_start": 2500,
        "char_end": 5000,
        "text": "## Features\n\nFastAPI provides..."
      }
    ],
    "metadata": {
      "tags": "python,api,web",
      "timestamp": "2025-11-18T12:00:00Z"
    }
  }'
```

**Step 3: Process response**

The service returns:

```json
{
  "success": true,
  "content_id": 123,
  "neo4j_document_id": "4:doc:456",
  "entities_extracted": 87,
  "relationships_extracted": 43,
  "processing_time_ms": 2341,
  "entities": [
    {
      "text": "FastAPI",
      "normalized": "fastapi",
      "type_primary": "Framework",
      "type_sub1": "Backend",
      "type_sub2": "Python",
      "type_full": "Framework::Backend::Python",
      "confidence": 0.95,
      "neo4j_node_id": "4:entity:789",
      "chunk_appearances": [
        {
          "vector_rowid": 45001,
          "chunk_index": 0,
          "offset_start": 342,
          "offset_end": 349
        }
      ],
      "spans_multiple_chunks": false
    }
  ],
  "relationships": [
    {
      "subject_text": "FastAPI",
      "predicate": "uses",
      "object_text": "Pydantic",
      "confidence": 0.88,
      "context": "FastAPI uses Pydantic for data validation",
      "neo4j_relationship_id": "5:rel:101",
      "chunk_rowids": [45001]
    }
  ],
  "summary": {
    "entities_by_type": {
      "Framework": 12,
      "Language": 3,
      "Concept": 5
    },
    "relationships_by_predicate": {
      "uses": 15,
      "competes_with": 3,
      "implements": 8
    },
    "chunks_with_entities": 18,
    "avg_entities_per_chunk": 4.8
  }
}
```

**What happened:**
1. kg-service received document with chunk boundaries
2. LLM extracted entities and relationships from full markdown
3. Entities mapped to specific chunks using character offsets
4. Everything stored in Neo4j graph database
5. Document node, Entity nodes, Chunk nodes, and relationships created
6. Results returned for storage in SQLite

### Workflow 2: Queue-Based Processing

Use the background worker system for automated batch processing.

**Step 1: Add documents to queue**

```python
# From robaimodeltools or direct SQLite
import sqlite3

db = sqlite3.connect('/data/crawl4ai_rag.db')

# Queue document for KG processing
db.execute('''
    INSERT INTO kg_processing_queue (content_id, priority, status)
    VALUES (?, ?, 'pending')
''', (123, 0))
db.commit()
```

**Step 2: Workers automatically process**

The KG worker running in kg-service automatically:
1. Claims pending items from queue (batch of 5)
2. Fetches document and chunk data
3. Sends to KG processor
4. Writes results back to SQLite
5. Marks queue item as completed

**Step 3: Monitor progress**

```bash
# Check queue statistics
curl http://localhost:8088/api/v1/queue/stats \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Response:
{
  "success": true,
  "stats": {
    "pending": 15,
    "processing": 3,
    "completed": 487,
    "failed": 2,
    "dead_letter": 0,
    "long_running": 1,
    "total": 508
  }
}
```

**Step 4: View dashboard**

Open http://localhost:8090 to see:
- Queue status counts
- Recent processing activity
- Success/failure rates
- Long-running items

### Workflow 3: Entity Search

Search for entities by name to find related documents.

**Step 1: Search for entity**

```bash
curl -X POST http://localhost:8088/api/v1/search/entities \
  -H "Content-Type: application/json" \
  -d '{
    "entity_terms": ["FastAPI", "Python"],
    "limit": 50,
    "min_mentions": 1
  }'
```

**Step 2: Review results**

```json
{
  "success": true,
  "entities": [
    {
      "entity_id": "4:entity:789",
      "text": "FastAPI",
      "normalized": "fastapi",
      "type_primary": "Framework",
      "type_full": "Framework::Backend::Python",
      "mention_count": 127,
      "confidence": 0.92
    },
    {
      "entity_id": "4:entity:12",
      "text": "Python",
      "normalized": "python",
      "type_primary": "Language",
      "type_full": "Language::Programming",
      "mention_count": 543,
      "confidence": 0.95
    }
  ],
  "total_found": 2
}
```

**Step 3: Get chunks containing entities**

```bash
curl -X POST http://localhost:8088/api/v1/search/chunks \
  -H "Content-Type: application/json" \
  -d '{
    "entity_names": ["FastAPI"],
    "limit": 100,
    "include_document_info": true
  }'
```

**Step 4: Use results in RAG pipeline**

The chunks returned contain `vector_rowid` which maps directly to SQLite `content_vectors.rowid` for retrieval.

### Workflow 4: Entity Expansion

Discover related entities through graph relationships.

**Step 1: Start with known entities**

```bash
curl -X POST http://localhost:8088/api/v1/expand/entities \
  -H "Content-Type: application/json" \
  -d '{
    "entity_names": ["FastAPI"],
    "max_expansions": 10,
    "min_confidence": 0.3,
    "expansion_depth": 1
  }'
```

**Step 2: Review related entities**

```json
{
  "success": true,
  "original_entities": ["FastAPI"],
  "expanded_entities": [
    {
      "entity_id": "4:entity:790",
      "text": "Pydantic",
      "normalized": "pydantic",
      "type_primary": "Library",
      "type_full": "Library::Python",
      "mention_count": 89,
      "relationship_type": "CO_OCCURS",
      "relationship_confidence": 0.9,
      "path_distance": 1
    },
    {
      "entity_id": "4:entity:812",
      "text": "Starlette",
      "normalized": "starlette",
      "type_primary": "Framework",
      "type_full": "Framework::Backend::Python",
      "mention_count": 34,
      "relationship_type": "CO_OCCURS",
      "relationship_confidence": 0.7,
      "path_distance": 1
    }
  ],
  "total_discovered": 2
}
```

**What this tells you:**
- FastAPI frequently co-occurs with Pydantic (9+ chunks in common)
- FastAPI also co-occurs with Starlette (3+ chunks)
- These are semantically related concepts from the knowledge base

**Step 3: Use expansions in query enhancement**

The robaimodeltools EntityExpander uses this endpoint to enrich user queries with related concepts.

## Common Tasks

### Task 1: Re-process a Document

If you re-crawl a URL and want to update the knowledge graph:

**Just call /api/v1/ingest again with the same content_id.**

The kg-service automatically:
1. Detects existing document by content_id
2. Deletes old Neo4j nodes/relationships
3. Processes new content
4. Creates fresh graph data

```bash
# No special cleanup needed - just POST again
curl -X POST http://localhost:8088/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{"content_id": 123, "url": "...", ...}'
```

### Task 2: Check Processing Status

**For a specific content_id:**

```bash
# Check if processed
sqlite3 /data/crawl4ai_rag.db \
  "SELECT kg_processed, kg_entity_count, kg_relationship_count
   FROM crawled_content WHERE id = 123"

# Output: 1|87|43 (processed, 87 entities, 43 relationships)
```

**For queue status:**

```bash
curl http://localhost:8088/api/v1/queue/stats \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Task 3: Handle Failed Items

**View dead letter queue:**

```bash
curl http://localhost:8088/api/v1/queue/stats \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Look for "dead_letter": N
```

**Inspect failed items in SQLite:**

```sql
SELECT q.id, q.content_id, c.url, q.retry_count, q.error_message
FROM kg_processing_queue q
JOIN crawled_content c ON q.content_id = c.id
WHERE q.status = 'dead_letter'
ORDER BY q.created_at DESC
LIMIT 10;
```

**Re-queue a failed item:**

```sql
UPDATE kg_processing_queue
SET status = 'pending', retry_count = 0, priority = 10, error_message = NULL
WHERE id = 456;
```

### Task 4: Monitor Long-Running Items

**Check for stale processing:**

```bash
curl "http://localhost:8088/api/v1/queue/long-running?minutes_threshold=60" \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

**Response:**

```json
{
  "success": true,
  "items": [
    {
      "queue_id": 789,
      "content_id": 145,
      "url": "https://example.com/very-long-doc",
      "processing_started_at": "2025-11-18T10:30:00Z",
      "minutes_elapsed": 75.3
    }
  ],
  "count": 1
}
```

**Action:** These items are automatically marked as "long_running" status by the worker cleanup task.

### Task 5: Query Neo4j Directly

**Connect to Neo4j Browser:**
- URL: http://localhost:7474
- Username: neo4j
- Password: knowledge_graph_2024

**Example queries:**

```cypher
// Find all frameworks
MATCH (e:Entity)
WHERE e.type_primary = 'Framework'
RETURN e.text, e.mention_count
ORDER BY e.mention_count DESC
LIMIT 10;

// Find entities related to FastAPI
MATCH (e1:Entity {normalized: 'fastapi'})-[:MENTIONED_IN]->(c:Chunk)
      <-[:MENTIONED_IN]-(e2:Entity)
WHERE e1 <> e2
WITH e2, COUNT(DISTINCT c) as cooccurrence_count
WHERE cooccurrence_count >= 3
RETURN e2.text, e2.type_full, cooccurrence_count
ORDER BY cooccurrence_count DESC
LIMIT 10;

// Find documents about a topic
MATCH (e:Entity {normalized: 'fastapi'})-[:MENTIONED_IN]->(c:Chunk)
      <-[:HAS_CHUNK]-(d:Document)
RETURN DISTINCT d.url, d.title, COUNT(c) as chunk_count
ORDER BY chunk_count DESC;

// View relationship distribution
MATCH ()-[r]->()
RETURN type(r) as relationship_type, COUNT(*) as count
ORDER BY count DESC;
```

## Troubleshooting

### Issue: Health check shows "degraded"

**Symptoms:**
```json
{
  "status": "degraded",
  "services": {
    "neo4j": "connected",
    "vllm": "error: Connection refused"
  }
}
```

**Solution:**
1. Check vLLM is running on configured port
2. Verify AUGMENT_LLM_URL in .env
3. Test vLLM directly: `curl http://localhost:8078/health`

### Issue: Workers not processing queue

**Symptoms:**
- Queue items stay in "pending" status
- No log output from workers

**Diagnosis:**
```bash
# Check worker logs
docker compose logs robaikg | grep "KG worker"

# Should see:
# ✓ KG worker started (poll_interval=5.0s)
```

**Solutions:**
1. Verify KG_NUM_WORKERS > 0 in environment
2. Check OPENAI_API_KEY is set (required for authentication)
3. Restart container: `docker compose restart robaikg`

### Issue: "Database not initialized" error

**Symptoms:**
```json
{
  "success": false,
  "error": "Database not initialized"
}
```

**Solution:**
This means queue endpoints were called before the database instance was registered.

1. Wait 10-15 seconds after container startup
2. Check logs for "✓ Database initialized for workers"
3. If persistent, restart: `docker compose restart robaikg`

### Issue: Neo4j connection refused

**Symptoms:**
```
Failed to connect to Neo4j
neo4j: error: Connection refused
```

**Solution:**
1. Ensure Neo4j container is running: `docker compose ps robaineo4j`
2. Check Neo4j logs: `docker compose logs robaineo4j`
3. Wait for Neo4j startup (can take 30-60 seconds)
4. Verify NEO4J_URI in .env matches Neo4j host/port

### Issue: Extraction timeout

**Symptoms:**
```
Processing failed: vLLM request timeout after 1800 seconds
```

**Solution:**
1. Document is very large (> 100K characters)
2. Increase VLLM_TIMEOUT in .env (default 1800 = 30 minutes)
3. Or split large documents before processing

### Issue: High memory usage

**Symptoms:**
- Neo4j container using > 16GB RAM
- System becomes slow

**Solution:**
1. Adjust NEO4J_HEAP_MAX_SIZE in .env
2. Reduce NEO4J_PAGECACHE_SIZE
3. Restart Neo4j: `docker compose restart robaineo4j`

**Recommended settings by system RAM:**
- 8GB system: HEAP_MAX=2G, PAGECACHE=1G
- 16GB system: HEAP_MAX=8G, PAGECACHE=2G
- 32GB+ system: HEAP_MAX=16G, PAGECACHE=4G

## Next Steps

1. **Architecture Deep Dive:** See [Architecture](architecture.md) for internal pipeline details
2. **Configuration Tuning:** Review [Configuration](configuration.md) for performance optimization
3. **API Integration:** Check [API Reference](api-reference.md) for complete endpoint documentation
4. **Production Deployment:** Review deployment best practices and monitoring setup

## Quick Reference

**Service Ports:**
- kg-service API: 8088
- Neo4j Browser: 7474
- Neo4j Bolt: 7687
- KG Dashboard: 8090

**Key Endpoints:**
- POST /api/v1/ingest - Process document
- GET /health - Health check
- POST /api/v1/search/entities - Search entities
- POST /api/v1/expand/entities - Expand via graph
- GET /api/v1/queue/stats - Queue statistics

**Default Credentials:**
- Neo4j: neo4j / knowledge_graph_2024
- API: Bearer token from OPENAI_API_KEY

**Log Locations:**
- kg-service: `docker compose logs robaikg`
- Neo4j: `docker compose logs robaineo4j`
- Dashboard: http://localhost:8090

**SQLite Tables:**
- kg_processing_queue - Processing queue
- chunk_entities - Entity appearances
- chunk_relationships - Relationships
- crawled_content - Document metadata (kg_processed flag)
