---
layout: default
title: Architecture
parent: robaikg
nav_order: 4
---

# Architecture

Detailed system design and architecture of robaikg Knowledge Graph service.

## System Overview

```
Raw Documents (Markdown)
        ↓
┌─────────────────────────────────┐
│  Entity Extraction (GLiNER)     │
│  ├─ 300+ entity types           │
│  └─ Confidence scoring          │
└────────────┬────────────────────┘
             ↓
┌─────────────────────────────────┐
│  Relationship Extraction (vLLM) │
│  ├─ 50+ relationship types      │
│  └─ Validation against entities │
└────────────┬────────────────────┘
             ↓
┌─────────────────────────────────┐
│  Chunk Mapping                  │
│  ├─ Entity → Chunk mapping      │
│  └─ Position tracking           │
└────────────┬────────────────────┘
             ↓
┌─────────────────────────────────┐
│  Graph Storage (Neo4j)          │
│  ├─ Entity nodes                │
│  ├─ Relationship edges          │
│  └─ Document hierarchy          │
└─────────────────────────────────┘
```

## Core Components

### 1. FastAPI Server (api/server.py)

**Purpose**: HTTP request handling, routing, and response formatting

**Key Responsibilities**:
- Lifespan management (startup/shutdown)
- CORS middleware configuration
- Exception handling and error responses
- Health check coordination
- Statistics tracking

**Key Features**:
- Async/await throughout
- Request validation via Pydantic
- OpenAPI documentation at `/docs`
- Graceful error handling

### 2. Entity Extractor (extractors/entity_extractor.py)

**Purpose**: GLiNER-based named entity recognition

**Model**: `urchade/gliner_large-v2.1` (300+ entity types)

**Process**:
```
Input: Markdown document
  ↓
[Tokenize to 384-token chunks]
  ↓
[Run GLiNER inference]
  ↓
[Parse hierarchical types (Framework::Backend::Python)]
  ↓
[Extract context windows]
  ↓
[Filter by confidence threshold]
  ↓
[Deduplicate identical entities]
  ↓
Output: Entity list with metadata
```

**Performance**: 2-3 seconds per document

**Entity Type Hierarchy**:
- Primary (Framework, Library, Language)
- Sub1 (Backend, Validation, Python)
- Sub2 (specific subcategories)
- Sub3 (granular classification)

### 3. Relationship Extractor (extractors/relation_extractor.py)

**Purpose**: vLLM-powered semantic relationship discovery

**Process**:
```
Input: Document + extracted entities
  ↓
[Build prompt with entity list]
  ↓
[Send to vLLM with JSON guidance]
  ↓
[Parse JSON response]
  ↓
[Validate against extracted entities]
  ↓
[Normalize predicate to snake_case]
  ↓
[Deduplicate relationships]
  ↓
Output: Relationship list with confidence
```

**Performance**: 5-10 seconds per document

**50+ Relationship Types**:
- Technical: uses, depends_on, implements, extends
- Comparative: competes_with, similar_to, different_from
- Hierarchical: part_of, contains, belongs_to
- Temporal: precedes, follows, replaces
- Spatial: located_in, near, connects_to

### 4. Chunk Mapper (pipeline/chunk_mapper.py)

**Purpose**: Map extracted entities and relationships to document chunks

**Process**:
1. Take extracted entities and chunk boundaries
2. Search for entity text matches within chunks
3. Calculate offset positions (char_start, char_end)
4. Create chunk_id to vector_rowid mappings
5. Track cross-chunk relationships

**Output**: Entity/relationship data with chunk attribution

### 5. KG Processor (pipeline/processor.py)

**Purpose**: Orchestrate entire extraction pipeline

**Pipeline Stages**:
```
1. Entity Extraction (GLiNER)
   ↓
2. Relationship Extraction (vLLM)
   ↓
3. Chunk Mapping
   ↓
4. Neo4j Storage
   ↓
5. Response Formatting
```

### 6. Neo4j Client (storage/neo4j_client.py)

**Purpose**: Graph database operations with async driver

**Key Operations**:
- Node creation: Document, Chunk, Entity
- Relationship creation: MENTIONED_IN, semantic relationships
- Schema validation on startup
- Batch operations for efficiency

**Schema**:
```cypher
// Nodes
(:Document {content_id, url, title, created_at})
(:Chunk {vector_rowid, chunk_index, char_start, char_end})
(:Entity {normalized, text, type_primary, type_sub1, mention_count})

// Relationships
(Document)-[:HAS_CHUNK]->(Chunk)
(Entity)-[:MENTIONED_IN {offset_start, offset_end, confidence}]->(Chunk)
(Entity)-[:USES|DEPENDS_ON|...]-(Entity)
(Entity)-[:CO_OCCURS_WITH {count}]->(Entity)
```

## Data Flow

### Document Processing Workflow

```
1. External system (robaidata) sends document via HTTP
   {content_id, url, title, markdown, chunks[]}
   ↓
2. FastAPI validates IngestRequest
   ↓
3. KGProcessor.process_document() starts
   ↓
4. EntityExtractor.extract()
   - GLiNER on markdown
   - Returns entities with type hierarchy
   ↓
5. RelationshipExtractor.extract()
   - vLLM inference
   - JSON parsing
   - Returns relationships
   ↓
6. ChunkMapper.map_entities_to_chunks()
   - Find entity text matches in chunks
   - Calculate offsets
   - Return chunk attribution
   ↓
7. Neo4jClient.store()
   - Create/update nodes
   - Create relationships
   - Return Neo4j element IDs
   ↓
8. Format IngestResponse
   - Include entities, relationships, summary
   - Return to caller
   ↓
9. External system stores in SQLite (chunk_entities, chunk_relationships)
```

### Search Workflow

```
User Query: "Find all Python frameworks"
   ↓
API receives POST /api/v1/search/entities
   {entity_terms: ["Python", "framework"]}
   ↓
Neo4j Query:
   MATCH (e:Entity)
   WHERE toLower(e.text) CONTAINS "python"
      OR toLower(e.text) CONTAINS "framework"
   RETURN e
   ↓
Filter and deduplicate
   ↓
Return EntitySearchResponse
   {success: true, entities: [...], total_found: N}
```

### Entity Expansion Workflow

```
User Query: "Find technologies related to FastAPI"
   ↓
API receives POST /api/v1/expand/entities
   {entity_names: ["FastAPI"], expansion_depth: 1}
   ↓
Neo4j Query (co-occurrence):
   MATCH (e1:Entity {text: "FastAPI"})-[:MENTIONED_IN]->(c:Chunk)<-[:MENTIONED_IN]-(e2:Entity)
   WHERE e1 != e2
   WITH e2, count(DISTINCT c) as co_count
   ORDER BY co_count DESC
   RETURN e2 as related_entity
   ↓
Convert to confidence scores based on co-occurrence counts
   ↓
Return EntityExpansionResponse
   {expanded_entities: [...], total_discovered: N}
```

## Configuration Management

### Configuration Sources (Priority Order)

1. System environment variables
2. .env file in working directory
3. Default values in config.py

### Critical Configuration

**Required for Operation**:
- `NEO4J_URI` - Neo4j connection
- `NEO4J_PASSWORD` - Database authentication

**Performance Tuning**:
- `GLINER_THRESHOLD` - Entity confidence (0.3-0.6)
- `RELATION_MIN_CONFIDENCE` - Relationship confidence (0.3-0.7)
- `VLLM_TIMEOUT` - LLM processing timeout (300-3600 seconds)
- `NEO4J_MAX_CONNECTION_POOL_SIZE` - Database connections (10-100)

## Design Patterns

### 1. Async/Await Throughout

All I/O operations (Neo4j, vLLM) use async patterns:

```python
async def process_document(request: IngestRequest) -> IngestResponse:
    entities = await entity_extractor.extract(request.markdown)
    relationships = await relationship_extractor.extract(request.markdown, entities)
    mapped = await chunk_mapper.map(entities, relationships, request.chunks)
    stored = await neo4j_client.store(mapped)
    return IngestResponse(...stored...)
```

### 2. Pydantic Models for Validation

Type-safe request/response contracts:

```python
class IngestRequest(BaseModel):
    content_id: int
    url: str
    title: str
    markdown: str = Field(..., min_length=50, max_length=1000000)
    chunks: List[ChunkMetadata]

    @field_validator("url")
    def validate_url(cls, v):
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v
```

### 3. Singleton Pattern for Services

```python
# Global instance initialized on startup
kg_processor: Optional[KGProcessor] = None
neo4j_client: Optional[Neo4jClient] = None

@app.on_event("startup")
async def startup():
    global kg_processor, neo4j_client
    neo4j_client = await Neo4jClient.create()
    kg_processor = KGProcessor(neo4j_client)
```

### 4. Exception Handling Hierarchy

```python
# Custom exceptions
class KGServiceException(Exception):
    """Base exception"""

class ModelUnavailableError(KGServiceException):
    """vLLM model not available"""

class Neo4jException(KGServiceException):
    """Graph database error"""

# Handler middleware
@app.exception_handler(KGServiceException)
async def handle_kg_exception(request, exc):
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": str(exc), "error_type": type(exc).__name__}
    )
```

### 5. Graceful Degradation

Service continues even if optional components fail:

```python
# vLLM relationship extraction optional
try:
    relationships = await relationship_extractor.extract(...)
except ModelUnavailableError:
    relationships = []  # Continue with entities only
    logger.warning("Relationship extraction failed, continuing with entities")
```

## Performance Characteristics

### Response Times

| Operation | Time | Notes |
|-----------|------|-------|
| Entity extraction | 2-3s | GLiNER inference on markdown |
| Relationship extraction | 5-10s | vLLM inference with JSON parsing |
| Chunk mapping | <100ms | Text search in chunks |
| Neo4j storage | 500ms-2s | Node/relationship creation |
| Entity search | <100ms | Neo4j index lookup |
| Entity expansion | <500ms | Graph traversal |
| Health check | <50ms | Service connectivity |

### Scalability

**Vertical Scaling**:
- Increase `NEO4J_MAX_CONNECTION_POOL_SIZE` for more concurrent requests
- Increase `VLLM_TIMEOUT` for larger documents
- Add more CPU cores for GLiNER (CPU-bound)

**Horizontal Scaling** (via robaidata workers):
- Multiple workers process queue items concurrently
- Each worker independent (stateless)
- Neo4j handles concurrent connections
- vLLM handles concurrent inference requests

## Security Architecture

### Input Validation

1. **URL Validation**: Must start with http:// or https://
2. **Markdown Size**: 50-1000000 characters
3. **Chunk Boundaries**: char_end > char_start, ordered
4. **Entity Terms**: Non-empty string arrays

### Neo4j Security

1. **Authentication**: Username/password or Kerberos
2. **Authorization**: Per-database access control
3. **Encryption**: TLS support via bolt+s:// protocol
4. **Connection Pooling**: Limited connections prevent resource exhaustion

### API Security

1. **CORS**: Configurable origins (currently wildcard)
2. **Rate Limiting**: Placeholder for future implementation
3. **Input Sanitization**: Pydantic validation
4. **Error Handling**: Detailed errors logged, minimal client exposure

## Monitoring & Observability

### Health Checks

```python
GET /health
{
  "status": "healthy|degraded|unhealthy",
  "services": {
    "neo4j": "connected|disconnected",
    "vllm": "available|unavailable",
    "gliner": "loaded|unloaded"
  },
  "uptime_seconds": 3600.5
}
```

### Statistics Tracking

```python
GET /stats
{
  "total_documents_processed": 523,
  "total_entities_extracted": 45234,
  "total_relationships_extracted": 12456,
  "avg_processing_time_ms": 8234.5,
  "last_processed_at": "2025-10-17T14:30:00Z",
  "failed_count": 7
}
```

### Logging

**Levels**:
- DEBUG: Detailed operation flow
- INFO: Key milestones
- WARNING: Degraded functionality
- ERROR: Processing failures

**Outputs**:
- Console (human-readable)
- File (detailed with line numbers)

## Integration Points

### With robaidata (Queue)

robaidata polls KG worker queue and sends documents to kg-service:

```
robaidata: SELECT from kg_processing_queue (status='pending')
        ↓
kg-service: POST /api/v1/ingest
        ↓
robaidata: UPDATE queue (status='completed'), store results in SQLite
```

### With robaitragmcp (Hybrid Search)

robaitragmcp uses kg-service for entity expansion in RAG:

```
robaitragmcp: User query "python frameworks"
           ↓
[Vector search in SQLite] (fast)
           ↓
kg-service: POST /api/v1/expand/entities
           ↓
[Graph traversal] (related entities)
           ↓
[Combined ranking]
           ↓
Return top chunks
```

### With robairagapi (REST Bridge)

robairagapi exposes kg-service operations via REST:

```
External client: GET /search/entities?q=fastapi
             ↓
robairagapi: POST http://kg-service:8088/api/v1/search/entities
             ↓
kg-service: [Neo4j query], return entities
             ↓
robairagapi: Format + return to client
```

## Deployment Architectures

### Single Machine

```
[kg-service]
    ↓
[Neo4j Container]
    ↓
[Local Disk Storage]
```

### Distributed

```
[kg-service Pod 1] ─┐
[kg-service Pod 2] ─┼─→ [Neo4j Cluster] ─→ [Shared Storage]
[kg-service Pod 3] ─┘
    ↑
[Kubernetes Ingress]
```

## Next Steps

- [Getting Started](getting-started.html) - Installation guide
- [Configuration](configuration.html) - Environment variables
- [API Reference](api-reference.html) - Complete endpoint documentation
