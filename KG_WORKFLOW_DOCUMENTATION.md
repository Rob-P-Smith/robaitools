# Knowledge Graph (KG) Workflow - Complete Documentation

## Executive Summary

The KG workflow is an **end-to-end pipeline** that transforms crawled web content into a queryable knowledge graph. It extracts entities (people, places, technologies) and relationships (uses, competes with, located in) from documents, stores them in Neo4j, and maintains bidirectional links with the original SQLite database for hybrid RAG+KG search.

---

## Workflow Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER API REQUEST                             │
│                   POST /api/v1/crawl/store                          │
│                   {url: "https://..."}                              │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 1: CRAWL & STORE IN SQLITE                                   │
│ ─────────────────────────────────────────────────────────────────  │
│ • Fetch content via Crawl4AI                                        │
│ • Clean & validate (language check, quality filter)                 │
│ • Store in crawled_content table                                    │
│ • Generate content_hash (SHA256)                                    │
│                                                                     │
│ Database: crawled_content                                           │
│   - id (content_id), url, title, content, markdown                  │
│   - kg_processed=0 (flag: not yet processed)                        │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 2: EMBEDDING & CHUNK METADATA                                │
│ ─────────────────────────────────────────────────────────────────  │
│ • Chunk content (~1000 chars each, no overlap)                      │
│ • Generate embeddings (SentenceTransformer: 384-dim vectors)        │
│ • Store vectors in content_vectors (sqlite-vec)                     │
│ • Calculate chunk boundaries (char_start, char_end in markdown)     │
│ • Store metadata in content_chunks                                  │
│                                                                     │
│ Database: content_vectors, content_chunks                           │
│   - vector_rowid, chunk_index, chunk_text, positions                │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 3: QUEUE FOR KG PROCESSING                                   │
│ ─────────────────────────────────────────────────────────────────  │
│ • Check if KG service is enabled (KG_SERVICE_ENABLED=true)          │
│ • Insert into kg_processing_queue                                   │
│ • Status: 'pending', Priority: 1                                    │
│                                                                     │
│ Database: kg_processing_queue                                       │
│   - id, content_id, status='pending', queued_at                     │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ↓ (Background worker polls every 5 seconds)
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 4: KG WORKER PROCESSING                                      │
│ ─────────────────────────────────────────────────────────────────  │
│ • Worker polls queue (batch_size=5)                                 │
│ • SELECT pending items (ORDER BY priority DESC)                     │
│ • Mark as 'processing' (with timestamp)                             │
│ • Fetch full markdown + chunk metadata                              │
│ • Build payload with chunks + boundaries                            │
│ • POST to kg-service /api/v1/ingest                                 │
│                                                                     │
│ HTTP Request:                                                       │
│   POST http://localhost:8088/api/v1/ingest                          │
│   Body: {content_id, url, title, markdown, chunks[], metadata}      │
│   Timeout: 1800 seconds (30 minutes)                                │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 5: KG SERVICE PROCESSING (Neo4j)                             │
│ ─────────────────────────────────────────────────────────────────  │
│ 5a. ENTITY EXTRACTION                                               │
│     • GLiNER (300+ entity types) OR vLLM (LLM-based)                │
│     • Extract: FastAPI (Framework::Backend::Python, conf=0.95)      │
│                                                                     │
│ 5b. RELATIONSHIP EXTRACTION                                         │
│     • vLLM relationship extractor                                   │
│     • Extract: FastAPI -[uses]-> Pydantic (conf=0.88)               │
│                                                                     │
│ 5c. CHUNK MAPPING                                                   │
│     • Map entities to chunks (by text search)                       │
│     • Map relationships to chunks (via entity positions)            │
│     • Store offset_start/offset_end within chunks                   │
│                                                                     │
│ 5d. NEO4J STORAGE                                                   │
│     • CREATE Document node (url, title, metadata)                   │
│     • CREATE Chunk nodes (vector_rowid, index, positions)           │
│     • CREATE Entity nodes (text, type, confidence)                  │
│     • CREATE Relationships: Document -[CONTAINS]-> Chunk            │
│     •                      Chunk -[HAS_ENTITY]-> Entity             │
│     •                      Entity -[USES]-> Entity                  │
│                                                                     │
│ Neo4j Structure:                                                    │
│   Document { content_id: 123, url, title }                          │
│     └─[CONTAINS]→ Chunk { vector_rowid: 45001, index: 0 }          │
│         └─[HAS_ENTITY]→ Entity { text: "FastAPI", type: "Framework"}│
│             └─[uses]→ Entity { text: "Pydantic" }                   │
│                                                                     │
│ 5e. RETURN RESPONSE                                                 │
│     • IngestResponse: {success, neo4j_document_id, entities[],      │
│                        relationships[], processing_time_ms}         │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 6: WRITE RESULTS BACK TO SQLITE                              │
│ ─────────────────────────────────────────────────────────────────  │
│ 6a. UPDATE crawled_content                                          │
│     • kg_processed = 1                                              │
│     • kg_entity_count = 87                                          │
│     • kg_relationship_count = 43                                    │
│     • kg_document_id = "4:doc:456" (Neo4j ID)                       │
│     • kg_processed_at = CURRENT_TIMESTAMP                           │
│                                                                     │
│ 6b. INSERT chunk_entities (for each entity appearance)              │
│     • chunk_rowid, entity_text, entity_type, confidence             │
│     • offset_start, offset_end (position in chunk)                  │
│     • neo4j_node_id (link to Neo4j)                                 │
│                                                                     │
│ 6c. INSERT chunk_relationships (for each relationship)              │
│     • subject_entity, predicate, object_entity                      │
│     • confidence, context (full sentence)                           │
│     • chunk_rowids (JSON array: [45001])                            │
│     • neo4j_relationship_id (link to Neo4j)                         │
│                                                                     │
│ 6d. UPDATE content_chunks                                           │
│     • kg_processed = 1 (mark all chunks as processed)               │
│                                                                     │
│ 6e. UPDATE kg_processing_queue                                      │
│     • status = 'completed'                                          │
│     • processed_at = CURRENT_TIMESTAMP                              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Database Schema

### SQLite Tables

#### 1. crawled_content (Main Document Store)
```sql
CREATE TABLE crawled_content (
    id INTEGER PRIMARY KEY AUTOINCREMENT,    -- content_id
    url TEXT UNIQUE NOT NULL,
    title TEXT,
    content TEXT,                            -- Full HTML/text
    markdown TEXT,                           -- Cleaned markdown
    content_hash TEXT UNIQUE,                -- SHA256 hash
    retention_policy TEXT DEFAULT 'permanent',
    tags TEXT,
    metadata TEXT,                           -- JSON metadata

    -- KG Status Fields
    kg_processed BOOLEAN DEFAULT 0,          -- 0 = not processed, 1 = processed
    kg_entity_count INTEGER,                 -- Number of entities extracted
    kg_relationship_count INTEGER,           -- Number of relationships extracted
    kg_document_id TEXT,                     -- Neo4j Document node ID
    kg_processed_at DATETIME,                -- When KG processing completed

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. content_vectors (Vector Embeddings)
```sql
CREATE VIRTUAL TABLE content_vectors USING vec0(
    embedding FLOAT[384],                    -- 384-dimensional float32 vector
    content_id INTEGER                       -- FK to crawled_content.id
);
-- rowid is auto-generated primary key (vector_rowid)
```

#### 3. content_chunks (Chunk Metadata)
```sql
CREATE TABLE content_chunks (
    rowid INTEGER PRIMARY KEY,               -- SAME as content_vectors.rowid
    content_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,            -- 0, 1, 2, ... (sequential)
    chunk_text TEXT NOT NULL,                -- Full chunk text (~1000 chars)
    char_start INTEGER NOT NULL,             -- Position in original markdown
    char_end INTEGER NOT NULL,
    word_count INTEGER,
    kg_processed BOOLEAN DEFAULT 0,          -- Sent to KG service?
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (content_id) REFERENCES crawled_content(id)
);

CREATE INDEX idx_chunks_content ON content_chunks(content_id, chunk_index);
```

#### 4. kg_processing_queue (Job Queue)
```sql
CREATE TABLE kg_processing_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',           -- pending | processing | completed | failed | skipped
    priority INTEGER DEFAULT 1,              -- Higher = process first
    queued_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    processing_started_at DATETIME,
    processed_at DATETIME,
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    result_summary TEXT,                     -- JSON: {entities: 87, relationships: 43}
    skipped_reason TEXT,                     -- e.g., 'kg_service_unavailable'

    FOREIGN KEY (content_id) REFERENCES crawled_content(id),
    UNIQUE(content_id)                       -- One queue entry per document
);

CREATE INDEX idx_kg_queue_status ON kg_processing_queue(status, priority, queued_at);
```

#### 5. chunk_entities (Entity Extractions)
```sql
CREATE TABLE chunk_entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chunk_rowid INTEGER NOT NULL,            -- FK to content_chunks.rowid
    content_id INTEGER NOT NULL,             -- FK to crawled_content.id

    -- Entity Information
    entity_text TEXT NOT NULL,               -- "FastAPI"
    entity_normalized TEXT,                  -- "fastapi" (lowercase)
    entity_type_primary TEXT,                -- "Framework"
    entity_type_sub1 TEXT,                   -- "Backend"
    entity_type_sub2 TEXT,                   -- "Python"
    entity_type_sub3 TEXT,                   -- Optional 4th level
    confidence REAL,                         -- 0.0 - 1.0

    -- Position in Chunk
    offset_start INTEGER,                    -- Start position within chunk text
    offset_end INTEGER,                      -- End position within chunk text

    -- Neo4j Link
    neo4j_node_id TEXT,                      -- Neo4j Entity node ID
    spans_multiple_chunks BOOLEAN DEFAULT 0, -- Entity appears in >1 chunk?

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (chunk_rowid) REFERENCES content_chunks(rowid),
    FOREIGN KEY (content_id) REFERENCES crawled_content(id)
);

CREATE INDEX idx_entities_chunk ON chunk_entities(chunk_rowid);
CREATE INDEX idx_entities_content ON chunk_entities(content_id);
CREATE INDEX idx_entities_type ON chunk_entities(entity_type_primary, entity_type_sub1);
```

#### 6. chunk_relationships (Relationship Extractions)
```sql
CREATE TABLE chunk_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id INTEGER NOT NULL,             -- FK to crawled_content.id

    -- Relationship Triple
    subject_entity TEXT NOT NULL,            -- "FastAPI"
    predicate TEXT NOT NULL,                 -- "uses"
    object_entity TEXT NOT NULL,             -- "Pydantic"

    confidence REAL,                         -- 0.0 - 1.0
    context TEXT,                            -- Full sentence where found

    -- Neo4j Link
    neo4j_relationship_id TEXT,              -- Neo4j relationship edge ID

    -- Chunk Attribution
    spans_chunks BOOLEAN DEFAULT 0,          -- Entities in different chunks?
    chunk_rowids TEXT,                       -- JSON array: "[45001, 45015]"

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (content_id) REFERENCES crawled_content(id)
);

CREATE INDEX idx_relationships_content ON chunk_relationships(content_id);
CREATE INDEX idx_relationships_predicate ON chunk_relationships(predicate);
```

---

### Neo4j Graph Structure

#### Nodes

**Document**
```cypher
CREATE (d:Document {
    content_id: 123,
    url: "https://fastapi.tiangolo.com/",
    title: "FastAPI - Modern Web Framework",
    created_at: datetime()
})
```

**Chunk**
```cypher
CREATE (c:Chunk {
    vector_rowid: 45001,
    chunk_index: 0,
    char_start: 0,
    char_end: 2500,
    text_preview: "FastAPI is a modern, fast (high-performance)...",
    word_count: 487
})
```

**Entity**
```cypher
CREATE (e:Entity {
    text: "FastAPI",
    normalized: "fastapi",
    type_primary: "Framework",
    type_sub1: "Backend",
    type_sub2: "Python",
    type_full: "Framework::Backend::Python",
    confidence: 0.95
})
```

#### Relationships

**Document -[CONTAINS]-> Chunk**
```cypher
MATCH (d:Document {content_id: 123})
MATCH (c:Chunk {vector_rowid: 45001})
CREATE (d)-[:CONTAINS]->(c)
```

**Entity -[APPEARS_IN]-> Chunk**
```cypher
MATCH (e:Entity {text: "FastAPI"})
MATCH (c:Chunk {vector_rowid: 45001})
CREATE (e)-[:APPEARS_IN {
    offset_start: 342,
    offset_end: 349,
    confidence: 0.95,
    context_before: "modern web ",
    context_after: " for building"
}]->(c)
```

**Entity -[SEMANTIC_RELATIONSHIP]-> Entity**
```cypher
MATCH (e1:Entity {normalized: "fastapi"})
MATCH (e2:Entity {normalized: "pydantic"})
CREATE (e1)-[:uses {
    confidence: 0.88,
    context: "FastAPI uses Pydantic for data validation"
}]->(e2)
```

---

## Key Files & Functions

### Storage Layer (robaimodeltools/data/)

| File | Function | Lines | Purpose |
|------|----------|-------|---------|
| **storage.py** | `store_content()` | 271-392 | Store document in SQLite, hash, metadata |
| **storage.py** | `generate_embeddings()` | 394-468 | Chunk, embed, store vectors + metadata |
| **kg_queue.py** | `queue_for_kg_processing_sync()` | 203-246 | Insert into kg_processing_queue |
| **kg_queue.py** | `calculate_chunk_boundaries()` | 25-82 | Calculate char_start/char_end for chunks |
| **kg_queue.py** | `store_chunk_metadata()` | 84-129 | Insert into content_chunks |
| **kg_queue.py** | `get_chunk_metadata_for_content()` | 248-285 | Fetch chunks for content_id |
| **kg_queue.py** | `write_kg_results()` | 287-403 | Write entities/relationships to SQLite |

### Worker Layer (robaidata/kg_coordinator/)

| File | Function | Lines | Purpose |
|------|----------|-------|---------|
| **kg_worker.py** | `start()` | 44-78 | Start worker async loop |
| **kg_worker.py** | `_process_queue_batch()` | 137-260 | Poll queue, process items |
| **kg_worker.py** | `_reset_stale_processing_items()` | 85-135 | Recover stuck items |
| **kg_worker.py** | `_mark_failed()` | 261-269 | Mark queue item as failed |
| **kg_config.py** | `check_health()` | 56-139 | Check KG service health |
| **kg_config.py** | `send_to_kg_queue()` | 141-212 | POST to kg-service |
| **kg_manager.py** | `start_workers()` | 37-68 | Start worker pool |

### KG Service Layer (robaikg/kg-service/)

| File | Function | Lines | Purpose |
|------|----------|-------|---------|
| **api/server.py** | `ingest_document()` | 330-436 | Receive document, process, return results |
| **pipeline/processor.py** | `process_document()` | 84-197 | Orchestrate extraction pipeline |
| **pipeline/processor.py** | `_store_in_neo4j()` | 199-297 | Create Neo4j nodes/relationships |
| **extractors/entity_extractor.py** | `extract()` | N/A | GLiNER entity extraction |
| **extractors/relation_extractor.py** | `extract_relationships()` | N/A | vLLM relationship extraction |
| **pipeline/chunk_mapper.py** | `map_entities_to_chunks()` | N/A | Map entities to chunk positions |
| **pipeline/chunk_mapper.py** | `map_relationships_to_chunks()` | N/A | Map relationships to chunks |

---

## Configuration

### Environment Variables (.env)

```bash
# KG Service Configuration
KG_SERVICE_ENABLED=true                      # Enable/disable KG processing
KG_SERVICE_URL=http://localhost:8088         # KG service endpoint
KG_SERVICE_TIMEOUT=1800.0                    # Request timeout (seconds, 30 minutes)
KG_HEALTH_CHECK_INTERVAL=30.0                # Health check frequency (seconds)
KG_MAX_RETRIES=3                             # Max retries for failed requests

# Worker Configuration
KG_NUM_WORKERS=2                             # Number of concurrent workers
KG_POLL_INTERVAL=5.0                         # Queue poll interval (seconds)

# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=knowledge_graph_2024

# vLLM Configuration
VLLM_BASE_URL=http://localhost:8078
VLLM_TIMEOUT=1800

# GLiNER Configuration
GLINER_MODEL=urchade/gliner_large-v2.1
GLINER_THRESHOLD=0.45
USE_GLINER_ENTITIES=true
```

### Tuning Parameters

| Parameter | Low-End | Mid-Range | High-End | Notes |
|-----------|---------|-----------|----------|-------|
| **KG_NUM_WORKERS** | 1 | 2 | 4 | More workers = higher throughput |
| **KG_POLL_INTERVAL** | 10.0s | 5.0s | 3.0s | Lower = more responsive |
| **Chunk Size** | 800 | 1000 | 1200 | Characters per chunk |
| **Batch Size** | 3 | 5 | 10 | Items per worker iteration |

---

## Error Handling & Recovery

### 1. Stale Item Recovery
**When**: Items stuck in 'processing' for > 60 minutes
**Action**: Reset to 'pending', increment retry_count
**Frequency**: Every 20 poll iterations (~100 seconds)

### 2. Failed Processing
**When**: KG service returns error or times out
**Action**: Mark as 'failed' with error_message
**Retry**: Manual retry or restart worker

### 3. Service Unavailable
**When**: KG service health check fails
**Action**: Mark queue items as 'skipped' with reason
**Recovery**: Automatically resume when service returns

### 4. Partial Failures
**When**: Entity extraction succeeds but Neo4j storage fails
**Action**: Transaction rollback, mark as 'failed'
**Data**: No partial writes - atomic success/failure

---

## Monitoring & Debugging

### Check Queue Status

```bash
# Via Python
python3 -c "
from robaidata.kg_coordinator import get_worker_stats
import json
print(json.dumps(get_worker_stats(), indent=2))
"
```

**Output**:
```json
{
  "total_workers": 2,
  "total_processed": 145,
  "total_success": 142,
  "total_failed": 3,
  "queue_size": {
    "total": 150,
    "pending": 5,
    "processing": 2,
    "completed": 140,
    "failed": 3
  }
}
```

### Check Worker Logs

```bash
# For robaikg container
docker logs robaikg --tail 100 -f | grep -i "kg worker\|queue\|processing"

# Look for:
# ✓ KG workers started
# Processing 5 items from KG queue
# ✓ Completed KG processing for content_id=123: 87 entities, 43 relationships
```

### Query SQLite Directly

```sql
-- Queue status summary
SELECT status, COUNT(*) as count
FROM kg_processing_queue
GROUP BY status;

-- Recent completions
SELECT c.url, c.kg_entity_count, c.kg_relationship_count, c.kg_processed_at
FROM crawled_content c
WHERE c.kg_processed = 1
ORDER BY c.kg_processed_at DESC
LIMIT 10;

-- Failed items with errors
SELECT content_id, error_message, retry_count
FROM kg_processing_queue
WHERE status = 'failed';
```

### Query Neo4j Directly

```cypher
-- Total documents, chunks, entities
MATCH (d:Document) RETURN count(d) as documents;
MATCH (c:Chunk) RETURN count(c) as chunks;
MATCH (e:Entity) RETURN count(e) as entities;

-- Entities by type
MATCH (e:Entity)
RETURN e.type_primary, count(*) as count
ORDER BY count DESC;

-- Most connected entities
MATCH (e:Entity)-[r]-()
RETURN e.text, e.type_full, count(r) as connections
ORDER BY connections DESC
LIMIT 20;
```

---

## Performance Metrics

### Typical Processing Times

| Stage | Time | Notes |
|-------|------|-------|
| **Crawl + Store** | 1-3s | Depends on Crawl4AI response |
| **Embedding** | 0.5-2s | Depends on chunk count |
| **Queue Insert** | <10ms | SQLite write |
| **KG Processing** | 5-30s | Entity/relationship extraction |
| **Neo4j Storage** | 1-3s | Graph writes |
| **SQLite Write** | 0.2-0.5s | Results storage |
| **Total End-to-End** | 8-40s | From crawl to KG complete |

### Throughput

- **Single Worker**: ~5-10 documents/minute
- **2 Workers**: ~10-15 documents/minute
- **4 Workers**: ~15-25 documents/minute

*Throughput depends on document size, entity density, and system resources*

---

## Summary

The KG workflow is a **production-ready, fault-tolerant pipeline** that:

✅ **Automatically queues** all crawled content for KG processing
✅ **Runs continuously** via background workers (auto-start with kg-service)
✅ **Recovers gracefully** from failures (stale item reset, retry logic)
✅ **Maintains bidirectional links** between SQLite and Neo4j
✅ **Provides precise attribution** via chunk mapping and offset tracking
✅ **Scales horizontally** with configurable worker pool
✅ **Monitors health** with cached health checks and graceful degradation

The result is a **hybrid RAG+KG system** where vector search provides initial recall, and knowledge graph provides structured relationships and entity-centric queries.
