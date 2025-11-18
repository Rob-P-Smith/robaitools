---
layout: default
title: Architecture
parent: robaikg
nav_order: 4
---

# Architecture

Technical deep-dive into robaikg's internal design, components, and data flow.

## System Overview

robaikg implements a multi-stage knowledge graph extraction pipeline:

```
Document Input (Markdown + Chunks)
           ↓
┌──────────────────────────────────┐
│  Step 1-2: LLM Extraction        │
│  ├─ Unified entity extraction    │
│  ├─ Relationship extraction      │
│  └─ ~110 entity types detected   │
└─────────────┬────────────────────┘
              ↓
┌──────────────────────────────────┐
│  Step 3: Chunk Mapping           │
│  ├─ Map entities to chunks       │
│  ├─ Calculate offsets            │
│  └─ Detect multi-chunk spans     │
└─────────────┬────────────────────┘
              ↓
┌──────────────────────────────────┐
│  Step 4: Neo4j Storage           │
│  ├─ Document/Chunk nodes         │
│  ├─ Entity nodes                 │
│  ├─ MENTIONED_IN relationships   │
│  └─ Semantic relationships       │
└──────────────────────────────────┘
```

## Core Components

### 1. FastAPI Server (api/server.py)

**Purpose:** HTTP API server orchestrating the entire pipeline.

**Startup Sequence:**
```
1. Validate configuration
   ├─ Check Neo4j URI, vLLM URL
   └─ Verify confidence thresholds

2. Initialize KG Processor
   ├─ Connect to Neo4j
   ├─ Create constraints/indexes
   └─ Verify vLLM availability

3. Initialize RAGDatabase
   ├─ Connect to SQLite at DB_PATH
   └─ Register with API endpoints

4. Start background workers
   ├─ Launch N worker tasks
   ├─ Initialize dashboard (port 8090)
   └─ Begin queue polling

5. Server ready (port 8088)
```

**Shutdown Sequence:**
```
1. Stop dashboard task
2. Cancel worker tasks
3. Close database connection
4. Close Neo4j driver
5. Close vLLM client
```

**Key Endpoints Registered:**
- `/api/v1/ingest` - Main processing endpoint
- `/api/v1/search/*` - Entity/chunk search
- `/api/v1/expand/*` - Entity expansion
- `/api/v1/queue/*` - Queue management
- `/api/v1/db/*` - Vector database access
- `/api/v1/dashboard/*` - Dashboard API
- `/health` - Health monitoring
- `/stats` - Service statistics

**Request Middleware:**
- Logs all requests (excludes successful /health checks)
- Adds X-Process-Time header
- CORS handling (configurable origins)

**Error Handling:**
- HTTPException handler returns ErrorResponse model
- General exception handler logs stack trace
- Returns 500 with error details

### 2. KG Processor (pipeline/processor.py)

**Purpose:** Orchestrates the 4-step extraction pipeline.

**Component Initialization:**
```python
KGProcessor()
  ├─ KGExtractor (unified LLM extraction)
  ├─ RelationExtractor (vLLM relationships)
  ├─ ChunkMapper (entity-to-chunk mapping)
  └─ Neo4jClient (graph storage)
```

**Processing Flow:**

**Step 1-2: Unified LLM Extraction**
```
Input: Full markdown + chunk boundaries
Process:
  1. KGExtractor.extract_kg(markdown, chunks, content_id)
  2. LLM analyzes full document in batches (if > 100K chars)
  3. Extracts entities with hierarchical types
  4. Extracts relationships between entities
  5. Returns: (entities[], relationships[])

Output:
  - Entity: {text, normalized, type_primary, type_sub1, type_sub2,
             type_sub3, type_full, confidence, context_before,
             context_after, sentence}
  - Relationship: {subject_text, predicate, object_text, confidence, context}
```

**Step 3: Chunk Mapping**
```
Input: entities[], relationships[], chunks[]
Process:
  1. ChunkMapper.map_entities_to_chunks(entities, chunks)
     ├─ For each entity, find character position in markdown
     ├─ Determine which chunk(s) contain entity
     ├─ Calculate offset_start/offset_end within chunk
     └─ Mark spans_multiple_chunks flag

  2. ChunkMapper.map_relationships_to_chunks(relationships, entities, chunks)
     ├─ Find chunks for subject entity
     ├─ Find chunks for object entity
     ├─ Mark spans_chunks if entities in different chunks
     └─ Collect all chunk_rowids involved

Output:
  - Mapped entities with chunk_appearances[]
  - Mapped relationships with chunk_rowids[]
```

**Step 4: Neo4j Storage**
```
Input: content_id, url, title, chunks[], entities[], relationships[]
Process:
  1. Delete old document (by content_id)
     ├─ Find existing Document node
     ├─ Delete connected Chunks, Entities, Relationships
     └─ Enables clean re-processing

  2. Create Document node
     ├─ Properties: content_id, url, title, metadata
     └─ Returns: neo4j_document_id

  3. Create Chunk nodes
     ├─ For each chunk: vector_rowid, chunk_index, char_start, char_end
     ├─ Link: (Document)-[:HAS_CHUNK]->(Chunk)
     └─ Store content_id for fast lookups

  4. Create Entity nodes (deduplication)
     ├─ Match existing by normalized text
     ├─ Merge: increment mention_count, update avg_confidence
     └─ Returns: neo4j_node_id

  5. Link entities to chunks
     ├─ For each entity.chunk_appearances
     ├─ Create: (Entity)-[:MENTIONED_IN]->(Chunk)
     └─ Properties: offset_start, offset_end, confidence, context

  6. Create semantic relationships
     ├─ Match entities by normalized text
     ├─ Create: (Entity1)-[:predicate]->(Entity2)
     └─ Properties: confidence, context

Output:
  - neo4j_document_id
  - Entity/relationship counts
  - Neo4j node/relationship IDs (for SQLite storage)
```

### 3. LLM-Based Extractors

#### KGExtractor (extractors/kg_extractor.py)

**Purpose:** Unified entity and relationship extraction using vLLM.

**Extraction Process:**
```
1. Document batching
   ├─ If markdown > 100K chars, split by chunks
   ├─ Otherwise, process full document
   └─ Batch size: up to 10 chunks or 100K chars

2. LLM prompting
   ├─ System prompt: Define entity types, relationship types
   ├─ User prompt: Provide markdown section
   └─ Request structured JSON output

3. Parse LLM response
   ├─ Extract entities array
   ├─ Extract relationships array
   ├─ Validate structure
   └─ Apply confidence thresholds

4. Deduplication
   ├─ Merge duplicate entities (by normalized text)
   ├─ Keep highest confidence
   └─ Combine contexts

5. Return results
   └─ (entities[], relationships[])
```

**Entity Type Hierarchy:**
```
Primary type examples:
- Framework
  └─ Backend
      └─ Python
          └─ "FastAPI"

- Language
  └─ Programming
      └─ "Python"

- Concept
  └─ Design Pattern
      └─ "Dependency Injection"
```

**Relationship Types (~50):**
- uses, implements, extends, depends_on
- part_of, belongs_to, contains
- competes_with, alternative_to
- supports, enables, requires
- created_by, developed_by, maintained_by

#### RelationExtractor (extractors/relation_extractor.py)

**Purpose:** Fallback/supplementary relationship extraction.

**Note:** Current pipeline uses KGExtractor for unified extraction. RelationExtractor is available for separate relationship-only workflows.

**Extraction Logic:**
```
1. Receive entities and markdown
2. Prompt vLLM to find relationships
3. Filter by min_confidence threshold
4. Return relationship triples
```

### 4. Chunk Mapper (pipeline/chunk_mapper.py)

**Purpose:** Map extracted entities to specific document chunks.

**Entity-to-Chunk Mapping Algorithm:**
```
For each entity:
  1. Find entity.text in full markdown (case-sensitive)
  2. Get character position: pos_start, pos_end

  3. For each chunk:
     ├─ Check if chunk.char_start <= pos_start < chunk.char_end
     ├─ OR chunk.char_start < pos_end <= chunk.char_end
     └─ OR entity spans across chunk boundary

  4. If match found:
     ├─ Calculate offset_start = pos_start - chunk.char_start
     ├─ Calculate offset_end = pos_end - chunk.char_start
     └─ Add to entity.chunk_appearances[]

  5. Set entity.spans_multiple_chunks flag
     └─ True if len(chunk_appearances) > 1
```

**Relationship-to-Chunk Mapping:**
```
For each relationship:
  1. Find subject entity in mapped_entities
  2. Find object entity in mapped_entities

  3. Collect all chunk_rowids from both entities
     └─ chunk_rowids = subject.chunks + object.chunks (deduplicated)

  4. Set relationship.spans_chunks flag
     └─ True if subject and object in different chunks
```

**Summary Generation:**
```
Generate statistics:
  ├─ entities_by_type: {type_primary: count}
  ├─ relationships_by_predicate: {predicate: count}
  ├─ chunks_with_entities: count(unique chunks)
  └─ avg_entities_per_chunk: entities / chunks
```

### 5. Neo4j Client (storage/neo4j_client.py)

**Purpose:** Graph database operations and schema management.

**Connection Management:**
```
Startup:
  1. Create async Neo4j driver
  2. Verify connectivity
  3. Initialize schema (constraints + indexes)

Health checks:
  ├─ driver.verify_connectivity()
  └─ Periodic ping queries

Shutdown:
  └─ await driver.close()
```

**Schema Initialization:**
```
Constraints created:
  ├─ CONSTRAINT ON (d:Document) ASSERT d.content_id IS UNIQUE
  ├─ CONSTRAINT ON (e:Entity) ASSERT e.normalized IS UNIQUE
  └─ CONSTRAINT ON (c:Chunk) ASSERT c.vector_rowid IS UNIQUE

Indexes created:
  ├─ INDEX ON :Document(url)
  ├─ INDEX ON :Entity(text)
  ├─ INDEX ON :Entity(type_primary)
  ├─ INDEX ON :Entity(mention_count)
  └─ INDEX ON :Chunk(content_id)
```

**Key Operations:**

**create_document(content_id, url, title, metadata)**
```cypher
MERGE (d:Document {content_id: $content_id})
ON CREATE SET d.url = $url, d.title = $title, d.created_at = timestamp()
ON MATCH SET d.url = $url, d.title = $title, d.updated_at = timestamp()
RETURN elementId(d)
```

**create_entity(text, normalized, type_*, confidence)**
```cypher
MERGE (e:Entity {normalized: $normalized})
ON CREATE SET
  e.text = $text,
  e.type_primary = $type_primary,
  e.type_full = $type_full,
  e.mention_count = 1,
  e.avg_confidence = $confidence
ON MATCH SET
  e.mention_count = e.mention_count + 1,
  e.avg_confidence = (e.avg_confidence * (e.mention_count - 1) + $confidence) / e.mention_count
RETURN elementId(e)
```

**link_entity_to_chunk(entity_id, chunk_id, offset_*, confidence, context)**
```cypher
MATCH (e:Entity), (c:Chunk)
WHERE elementId(e) = $entity_id AND elementId(c) = $chunk_id
CREATE (e)-[:MENTIONED_IN {
  offset_start: $offset_start,
  offset_end: $offset_end,
  confidence: $confidence,
  context_before: $context_before,
  context_after: $context_after,
  sentence: $sentence
}]->(c)
```

**delete_document_by_content_id(content_id)**
```cypher
MATCH (d:Document {content_id: $content_id})-[:HAS_CHUNK]->(c:Chunk)
OPTIONAL MATCH (e:Entity)-[r:MENTIONED_IN]->(c)
WHERE NOT (e)-[:MENTIONED_IN]->(:Chunk)<-[:HAS_CHUNK]-(:Document)<>(d)
DETACH DELETE e  -- Delete entities only mentioned in this document
DETACH DELETE c  -- Delete chunks
DETACH DELETE d  -- Delete document
```

### 6. Background Workers (coordinator/)

#### KGWorker (coordinator/kg_worker.py)

**Purpose:** Automated queue processing in background.

**Worker Loop:**
```
Every poll_interval (default 5s):
  1. Call /api/v1/queue/claim-items (batch_size=5)
     ├─ Atomically claim pending items
     └─ Receive: [QueueItem, QueueItem, ...]

  2. For each claimed item:
     a. Fetch chunk metadata
        └─ GET /api/v1/queue/chunks/{content_id}

     b. Call KG processor
        └─ POST /api/v1/ingest with full document

     c. Write results back
        └─ POST /api/v1/queue/write-results

     d. Mark completed
        └─ POST /api/v1/queue/mark-completed

  3. On error:
     └─ POST /api/v1/queue/mark-failed (with retry logic)

Every 20 iterations (~100s):
  ├─ POST /api/v1/queue/mark-stale
  └─ Mark processing > 60min as 'long_running'
```

**Retry Logic:**
```
If processing fails:
  1. Increment retry_count
  2. If retry_count < max_retries (default 3):
     ├─ Increase priority
     ├─ Set status = 'pending'
     └─ Item re-queued automatically
  3. Else:
     └─ Set status = 'dead_letter' (manual intervention needed)
```

#### KGDashboard (coordinator/kg_dashboard.py)

**Purpose:** Web-based monitoring interface.

**Server:** Runs on port 8090 (separate from main API).

**Pages Served:**
- `/` - Queue statistics and charts
- `/api/stats` - JSON statistics endpoint
- Real-time updates via polling

**Metrics Displayed:**
- Queue status distribution (pending, processing, completed, failed, dead_letter, long_running)
- Processing throughput (docs/hour)
- Success/failure rates
- Long-running items alert
- Recent activity log

### 7. Queue Management (api/queue_endpoints.py)

**Purpose:** Unified queue API for all coordinator components.

**Design Pattern:** All workers access queue via HTTP API (not direct SQL).

**Key Endpoints:**

**POST /api/v1/queue/claim-items**
```
Atomically claims items:
  1. BEGIN TRANSACTION
  2. UPDATE status='processing' for first N pending items
     └─ Temporarily stores worker_id in error_message field
  3. SELECT claimed items WHERE error_message = worker_id
  4. Clear error_message marker
  5. COMMIT
  6. Return claimed items with full document data
```

**GET /api/v1/queue/chunks/{content_id}**
```
Returns chunk metadata:
  SELECT rowid, chunk_index, char_start, char_end, chunk_text, word_count
  FROM content_chunks
  WHERE content_id = ?
  ORDER BY chunk_index

Note: rowid here equals vector_rowid (Bug #1 fix)
```

**POST /api/v1/queue/write-results**
```
Atomic write transaction:
  1. UPDATE crawled_content SET kg_processed=1, kg_entity_count, kg_relationship_count
  2. INSERT INTO chunk_entities (for each entity.chunk_appearances)
  3. INSERT INTO chunk_relationships (for each relationship)
  4. UPDATE content_chunks SET kg_processed=1
  5. COMMIT
```

**POST /api/v1/queue/mark-stale**
```
Find stale items:
  SELECT * FROM kg_processing_queue
  WHERE status='processing'
  AND processing_started_at < NOW() - stale_minutes

Mark as long_running:
  UPDATE status='long_running', error_message='Processing exceeded N minutes'
```

### 8. Search Endpoints (api/search_endpoints.py)

**Purpose:** Graph-powered search for RAG pipeline.

**POST /api/v1/search/entities**
```cypher
For each entity_term:
  MATCH (e:Entity)
  WHERE toLower(e.text) CONTAINS toLower($term)
     OR toLower(e.normalized) CONTAINS toLower($term)
  AND e.mention_count >= $min_mentions
  RETURN e.*, elementId(e)
  ORDER BY e.mention_count DESC
  LIMIT $limit
```

**POST /api/v1/search/chunks**
```cypher
MATCH (e:Entity)-[:MENTIONED_IN]->(c:Chunk)
WHERE e.text IN $entity_names OR e.normalized IN $entity_names
WITH c, COLLECT(DISTINCT e.text) as matched_entities, COUNT(DISTINCT e) as entity_count
OPTIONAL MATCH (d:Document)-[:HAS_CHUNK]->(c)
RETURN c.vector_rowid, c.chunk_index, entity_count, matched_entities, d.url, d.title
ORDER BY entity_count DESC
LIMIT $limit
```

**POST /api/v1/expand/entities**
```cypher
-- Find co-occurring entities
MATCH (e1:Entity)-[:MENTIONED_IN]->(c:Chunk)<-[:MENTIONED_IN]-(e2:Entity)
WHERE (e1.text IN $entity_names OR e1.normalized IN $entity_names)
  AND e2 <> e1
WITH e2, COUNT(DISTINCT c) as cooccurrence_count
WHERE cooccurrence_count >= 2
RETURN e2.*, cooccurrence_count,
  CASE
    WHEN cooccurrence_count >= 5 THEN 0.9
    WHEN cooccurrence_count >= 3 THEN 0.7
    ELSE 0.5
  END as relationship_confidence
ORDER BY cooccurrence_count DESC
LIMIT $max_expansions
```

## Data Flow

### Full Processing Pipeline

```
1. Document arrives via POST /api/v1/ingest
   ├─ Validate: content_id, url, title, markdown, chunks[]
   └─ Pass to KGProcessor.process_document()

2. KGProcessor extracts entities/relationships
   ├─ KGExtractor.extract_kg(markdown, chunks)
   ├─ Returns: ~87 entities, ~43 relationships (typical)
   └─ Processing time: 2-5 seconds for medium documents

3. Chunk mapping
   ├─ ChunkMapper.map_entities_to_chunks()
   ├─ Calculates offsets for each entity in each chunk
   └─ Average: 4.8 entities per chunk

4. Neo4j storage
   ├─ Create/update Document node
   ├─ Create Chunk nodes (linked to Document)
   ├─ Create/merge Entity nodes
   ├─ Link entities to chunks (MENTIONED_IN relationships)
   └─ Create semantic relationships between entities

5. Return results to caller
   ├─ Response: IngestResponse model
   ├─ Contains: entities[], relationships[], neo4j_document_id
   └─ Caller (worker) writes to SQLite
```

### Queue-Based Processing

```
1. Document added to kg_processing_queue
   └─ status='pending', priority=0

2. KGWorker claims item
   ├─ Atomically updates status='processing'
   └─ Stores processing_started_at timestamp

3. Worker fetches chunk metadata
   └─ GET /api/v1/queue/chunks/{content_id}

4. Worker calls ingest endpoint
   └─ POST /api/v1/ingest (full pipeline above)

5. Worker writes results to SQLite
   ├─ POST /api/v1/queue/write-results
   ├─ Updates: crawled_content, chunk_entities, chunk_relationships
   └─ Marks chunks as kg_processed=1

6. Worker marks queue item completed
   ├─ POST /api/v1/queue/mark-completed
   └─ status='completed'

7. On error:
   ├─ POST /api/v1/queue/mark-failed
   ├─ Retry if retry_count < max_retries
   └─ Otherwise move to dead_letter
```

## Integration Patterns

### Integration with robaimodeltools

robaimodeltools RAG pipeline uses kg-service for entity expansion:

```
1. User query: "How does FastAPI handle async?"

2. QueryParser extracts entities (robaimodeltools/search/query_parser.py)
   └─ Entities: ["FastAPI", "async"]

3. GraphRetriever searches Neo4j (robaimodeltools/search/hybrid_retriever.py)
   a. POST /api/v1/search/entities
      └─ Find "FastAPI" and "async" entities

   b. POST /api/v1/expand/entities
      └─ Discover related: ["Pydantic", "Starlette", "ASGI"]

   c. POST /api/v1/search/chunks
      └─ Get chunks containing these entities

4. Vector search combines with graph results
   ├─ Graph chunks: 15 chunks (high entity relevance)
   ├─ Vector chunks: 20 chunks (semantic similarity)
   └─ Hybrid merge: Top 10 chunks

5. Advanced ranking
   ├─ Graph signal: 25% weight
   ├─ Vector signal: 35% weight
   └─ Final ranking includes graph boost
```

### Integration with Coordinator

Background processing workflow:

```
1. robaimodeltools crawls URL
   ├─ Stores in crawled_content
   ├─ Creates chunks in content_chunks
   └─ Generates embeddings in content_vectors

2. robaimodeltools queues for KG processing
   └─ INSERT INTO kg_processing_queue (content_id, status='pending')

3. kg-service worker picks up item
   ├─ Claims via /api/v1/queue/claim-items
   ├─ Fetches chunks via /api/v1/queue/chunks/{id}
   └─ Calls /api/v1/ingest

4. kg-service processes and stores in Neo4j
   └─ Returns entities, relationships, neo4j_document_id

5. Worker writes back to SQLite
   ├─ POST /api/v1/queue/write-results
   ├─ chunk_entities table populated
   ├─ chunk_relationships table populated
   └─ crawled_content.kg_processed = 1

6. Future queries benefit from graph
   └─ Both Neo4j and SQLite have full KG data
```

## Performance Characteristics

### Processing Speed

**Typical document (5000 words, 20 chunks):**
- LLM extraction: 1500-2500ms
- Chunk mapping: 50-100ms
- Neo4j storage: 300-500ms
- **Total: 2000-3500ms**

**Large document (20K words, 80 chunks):**
- LLM extraction (batched): 6000-10000ms
- Chunk mapping: 200-300ms
- Neo4j storage: 1000-1500ms
- **Total: 7000-12000ms**

**Very large document (100K chars):**
- LLM extraction (batched): 15000-25000ms
- May timeout if VLLM_TIMEOUT too low
- Consider increasing timeout or splitting document

### Throughput

**Worker configuration:**
- 1 worker: ~150-200 docs/hour
- 2 workers: ~300-350 docs/hour
- 4 workers: ~500-600 docs/hour

**Bottlenecks:**
1. vLLM inference time (largest factor)
2. Neo4j write operations
3. Database lock contention (if > 4 workers)

**Optimization:**
- Batch processing: Workers claim 5 items at once
- Async operations: All I/O is non-blocking
- Connection pooling: Neo4j driver manages pool

### Memory Usage

**kg-service container:**
- Base: ~300MB
- Per request: +50-100MB (released after response)
- Peak: ~800MB with 4 concurrent requests

**Neo4j container:**
- Heap: Configured by NEO4J_HEAP_MAX_SIZE (default 16G)
- Pagecache: Configured by NEO4J_PAGECACHE_SIZE (default 2G)
- Minimum recommended: 4GB total (2G heap + 1G pagecache)

### Storage Growth

**Per 1000 documents (average):**
- Neo4j disk: +100-200MB
- Entity nodes: ~50K entities (deduped)
- Chunk nodes: ~20K chunks
- Relationships: ~200K total (MENTIONED_IN + semantic)

**SQLite growth:**
- chunk_entities: ~400KB per 1000 documents
- chunk_relationships: ~200KB per 1000 documents

## Failure Handling

### Neo4j Connection Failure

```
Startup:
  ├─ Retry connection 3 times (5s delay)
  ├─ If fails: log error, service starts degraded
  └─ Health endpoint reports: "neo4j": "error: ..."

Runtime:
  ├─ Each query wrapped in try/except
  ├─ Return 503 Service Unavailable
  └─ Log error for monitoring
```

### vLLM Timeout

```
Request:
  ├─ httpx timeout set to VLLM_TIMEOUT (default 1800s)
  ├─ If timeout: raise HTTPException 500
  └─ Worker marks item as failed (retries)

Mitigation:
  ├─ Increase VLLM_TIMEOUT for large docs
  ├─ Or enable document batching (automatic for > 100K chars)
  └─ Monitor /api/v1/extraction/status for capacity
```

### Queue Processing Failure

```
Worker error:
  1. Log exception with stack trace
  2. POST /api/v1/queue/mark-failed
     ├─ Increment retry_count
     ├─ Increase priority
     └─ Set status='pending' (if retries remaining)
  3. If retry_count >= max_retries:
     └─ Move to status='dead_letter'

Stale items:
  ├─ Every ~100s, worker checks for stale items
  ├─ Items processing > 60min marked 'long_running'
  └─ Dashboard alerts operator
```

### Concurrent Processing Conflicts

**SQLite write conflicts:**
```
db_lock prevents concurrent writes
  ├─ Queue claim operation is atomic
  ├─ Write results operation is transactional
  └─ COMMIT/ROLLBACK on error
```

**Neo4j concurrent writes:**
```
MERGE operations are atomic
  ├─ Entity deduplication handled by MERGE
  ├─ Concurrent creates → single entity node
  └─ mention_count and avg_confidence updated atomically
```

## Monitoring & Observability

### Health Checks

**GET /health:**
```
Returns:
  ├─ status: "healthy" | "degraded" | "unhealthy"
  ├─ neo4j: connection status
  ├─ vllm: connection status + model name
  ├─ llm_extraction: "available" | "unavailable"
  ├─ uptime_seconds: service uptime
  └─ version: service version
```

**GET /stats:**
```
Returns:
  ├─ total_documents_processed: lifetime count
  ├─ total_entities_extracted: lifetime count
  ├─ total_relationships_extracted: lifetime count
  ├─ avg_processing_time_ms: average per document
  ├─ last_processed_at: timestamp
  └─ failed_count: lifetime failures
```

**GET /api/v1/extraction/status:**
```
Returns:
  ├─ active_extractions: current concurrent extractions
  ├─ total_queued: lifetime requests queued
  ├─ total_completed: lifetime successful
  ├─ total_failed: lifetime failures
  ├─ max_concurrent: concurrency limit
  └─ slots_available: available slots
```

### Logging

**Log levels:**
- INFO: Startup, shutdown, successful processing
- WARNING: Retries, stale items, degraded services
- ERROR: Failures, exceptions with stack traces

**Key log events:**
```
Startup:
  "✓ KG Processor initialized successfully"
  "✓ KG workers started"
  "✓ KG Dashboard started on http://0.0.0.0:8090"

Processing:
  "📥 RECEIVED DOCUMENT from mcpragcrawl4ai"
  "🤖 Step 1-2: Using LLM for unified entity and relationship extraction..."
  "✅ KG EXTRACTED: 87 entities, 43 relationships found"
  "💾 Step 4: Storing in Neo4j..."
  "📤 RETURNING TO mcpragcrawl4ai"

Errors:
  "✗ Processing failed: {exception}"
  "Failed to connect to Neo4j"
  "vLLM request timeout after 1800 seconds"
```

### Dashboard Metrics

**Queue visualization (http://localhost:8090):**
- Pie chart: Status distribution
- Bar chart: Processing timeline
- Table: Recent activity
- Alerts: Long-running items
- Refresh: Auto-updates every 30s

## Security Considerations

### Authentication

**API Key requirement:**
- Queue endpoints require Bearer token
- Token from OPENAI_API_KEY environment variable
- Validates on each protected request

### Input Validation

**Pydantic models enforce:**
- URL format validation (must start with http:// or https://)
- Content ID > 0
- Chunk ordering validation
- Text length limits (1M chars max)

### Neo4j Security

**Credentials:**
- Username/password from environment
- Bolt protocol encryption (if configured)
- Network isolation (internal Docker network or localhost)

### Rate Limiting

**Worker batch size:**
- Configurable via KG_POLL_INTERVAL
- Default: 5 items per poll
- Prevents overwhelming downstream services

## Design Decisions

### Why LLM-based extraction?

**Rationale:** Flexibility and accuracy for diverse entity types.

**Alternative considered:** GLiNER model (pattern-matching NER)
- Pro: Faster (500ms vs 2000ms)
- Con: Limited to predefined patterns
- Con: Less accurate for domain-specific entities

**Decision:** Use vLLM for unified extraction, achieving better accuracy at acceptable speed.

### Why unified entity+relationship extraction?

**Rationale:** Single LLM call reduces latency and improves consistency.

**Alternative:** Separate entity extraction → relationship extraction
- Would require 2x LLM calls
- Relationships might reference entities not extracted

**Decision:** Unified extraction ensures relationships always reference extracted entities.

### Why queue-based processing?

**Rationale:** Decouple crawling from KG processing.

**Benefits:**
- Asynchronous: Don't block crawler on slow KG extraction
- Retry logic: Failed items automatically retried
- Monitoring: Dashboard shows queue health
- Scalability: Multiple workers for throughput

### Why API-based queue access?

**Rationale:** Centralized database access through HTTP API.

**Alternative:** Direct SQLite access from workers
- Pro: Slightly faster (no HTTP overhead)
- Con: Multiple processes writing to SQLite
- Con: Database lock contention
- Con: No centralized monitoring

**Decision:** API-based access provides better isolation and monitoring.

### Why store in both Neo4j and SQLite?

**Rationale:** Each database optimized for different query patterns.

**Neo4j strengths:**
- Graph traversal (entity expansion, co-occurrence)
- Relationship queries
- Entity deduplication

**SQLite strengths:**
- Vector search (embedding similarity)
- Chunk retrieval by rowid
- Joins with crawled_content

**Decision:** Dual storage enables hybrid search (graph + vector).

## Next Steps

- **Configuration Guide:** See [Configuration](configuration.md) for tuning parameters
- **API Reference:** Review [API Reference](api-reference.md) for complete endpoint specs
- **Deployment:** Consider production settings (workers, memory, timeouts)
