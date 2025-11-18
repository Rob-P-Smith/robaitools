---
layout: default
title: API Reference
parent: robaikg
nav_order: 3
---

# API Reference

Complete documentation of all robaikg REST API endpoints with examples.

## Base URL

```
http://localhost:8088
```

All endpoints require `Content-Type: application/json` for POST requests.

## Endpoints Overview

| Endpoint | Method | Purpose | Response Time |
|----------|--------|---------|-----------------|
| `/api/v1/ingest` | POST | Process document for entity/relationship extraction | 8-15s |
| `/api/v1/search/entities` | POST | Search entities by text | <100ms |
| `/api/v1/search/chunks` | POST | Get chunks containing entities | <200ms |
| `/api/v1/expand/entities` | POST | Discover related entities | <500ms |
| `/health` | GET | Service health + dependencies | <50ms |
| `/stats` | GET | Processing statistics | <100ms |
| `/api/v1/model-info` | GET | Model information | <10ms |
| `/` | GET | Service information | <10ms |

## Document Ingestion

### POST /api/v1/ingest

Process document for entity and relationship extraction.

**Request**:

```json
{
  "content_id": 123,
  "url": "https://docs.example.com/page",
  "title": "Example Documentation",
  "markdown": "# Title\n\nContent with entities...",
  "chunks": [
    {
      "vector_rowid": 45001,
      "chunk_index": 0,
      "char_start": 0,
      "char_end": 2500,
      "text": "# Title\n\nFirst chunk text..."
    }
  ],
  "metadata": {
    "tags": "python,api",
    "timestamp": "2025-10-17T12:00:00Z"
  }
}
```

**Request Fields**:
- `content_id` (integer, required) - Source content ID
- `url` (string, required) - Document URL (http/https)
- `title` (string, required) - Document title
- `markdown` (string, required) - Full markdown content (50-1000000 chars)
- `chunks` (array, required) - Text chunks with vector indices
  - `vector_rowid` (integer) - SQLite content_vectors rowid
  - `chunk_index` (integer) - Sequential chunk number
  - `char_start` (integer) - Character start position
  - `char_end` (integer) - Character end position
  - `text` (string) - Chunk text
- `metadata` (object, optional) - Custom metadata key-value pairs

**Response** (200 OK):

```json
{
  "success": true,
  "content_id": 123,
  "neo4j_document_id": "4:abc123:456",
  "entities_extracted": 42,
  "relationships_extracted": 18,
  "processing_time_ms": 8543,
  "entities": [
    {
      "text": "FastAPI",
      "normalized": "fastapi",
      "type_primary": "Framework",
      "type_sub1": "Backend",
      "type_sub2": "Python",
      "type_sub3": null,
      "type_full": "Framework::Backend::Python",
      "confidence": 0.95,
      "neo4j_node_id": "4:def789:789",
      "context_before": "modern web ",
      "context_after": " for building",
      "sentence": "FastAPI is a modern web framework for building APIs.",
      "chunk_appearances": [
        {
          "vector_rowid": 45001,
          "chunk_index": 0,
          "offset_start": 120,
          "offset_end": 127
        }
      ],
      "spans_multiple_chunks": false
    }
  ],
  "relationships": [
    {
      "subject_text": "FastAPI",
      "subject_neo4j_id": "4:def789:789",
      "predicate": "uses",
      "object_text": "Pydantic",
      "object_neo4j_id": "4:def789:790",
      "confidence": 0.88,
      "context": "FastAPI uses Pydantic for data validation",
      "neo4j_relationship_id": "5:rel123:101",
      "spans_chunks": false,
      "chunk_rowids": [45001]
    }
  ],
  "summary": {
    "entities_by_type": {
      "Framework": 8,
      "Library": 12,
      "Language": 3
    },
    "relationships_by_predicate": {
      "uses": 10,
      "implements": 5,
      "based_on": 3
    },
    "chunks_with_entities": 15,
    "avg_entities_per_chunk": 2.8
  }
}
```

**Error Responses**:
- 422 Unprocessable Entity - Validation error
- 503 Service Unavailable - KG processor not ready
- 500 Internal Server Error - Processing failure

**Example with cURL**:

```bash
curl -X POST http://localhost:8088/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "content_id": 1,
    "url": "https://example.com/docs",
    "title": "Documentation",
    "markdown": "# FastAPI\n\nFastAPI is a modern Python web framework.",
    "chunks": [{
      "vector_rowid": 1,
      "chunk_index": 0,
      "char_start": 0,
      "char_end": 50,
      "text": "# FastAPI\n\nFastAPI is a modern Python"
    }]
  }'
```

## Entity Search

### POST /api/v1/search/entities

Search for entities by text matching.

**Request**:

```json
{
  "entity_terms": ["python", "fastapi"],
  "limit": 50,
  "min_mentions": 2
}
```

**Request Fields**:
- `entity_terms` (array, required) - Terms to search for
- `limit` (integer, default: 50) - Max results per term (1-500)
- `min_mentions` (integer, default: 1) - Minimum mention count

**Response** (200 OK):

```json
{
  "success": true,
  "entities": [
    {
      "entity_id": "4:abc:123",
      "text": "Python",
      "normalized": "python",
      "type_primary": "Language",
      "type_full": "Programming::Language",
      "mention_count": 147,
      "confidence": 0.92
    },
    {
      "entity_id": "4:abc:124",
      "text": "FastAPI",
      "normalized": "fastapi",
      "type_primary": "Framework",
      "type_full": "Framework::Backend::Python",
      "mention_count": 89,
      "confidence": 0.94
    }
  ],
  "total_found": 2
}
```

**Example**:

```bash
curl -X POST http://localhost:8088/api/v1/search/entities \
  -H "Content-Type: application/json" \
  -d '{
    "entity_terms": ["FastAPI"],
    "limit": 10
  }'
```

## Chunk Retrieval

### POST /api/v1/search/chunks

Retrieve chunks containing specified entities.

**Request**:

```json
{
  "entity_names": ["Python", "FastAPI"],
  "limit": 100,
  "include_document_info": true
}
```

**Request Fields**:
- `entity_names` (array, optional) - Entity text names
- `entity_ids` (array, optional) - Neo4j element IDs
- `limit` (integer, default: 100) - Max chunks (1-1000)
- `include_document_info` (boolean, default: true) - Include URL/title

**Response** (200 OK):

```json
{
  "success": true,
  "chunks": [
    {
      "chunk_id": "4:chunk:567",
      "vector_rowid": 45123,
      "chunk_index": 3,
      "entity_count": 2,
      "matched_entities": ["Python", "FastAPI"],
      "document_url": "https://docs.example.com/page",
      "document_title": "Example Documentation"
    }
  ],
  "total_found": 1
}
```

**Example**:

```bash
curl -X POST http://localhost:8088/api/v1/search/chunks \
  -H "Content-Type: application/json" \
  -d '{
    "entity_names": ["FastAPI"],
    "limit": 50
  }'
```

## Entity Expansion

### POST /api/v1/expand/entities

Discover related entities via graph traversal.

**Request**:

```json
{
  "entity_names": ["FastAPI"],
  "max_expansions": 10,
  "min_confidence": 0.5,
  "expansion_depth": 1
}
```

**Request Fields**:
- `entity_names` (array, required) - Starting entities
- `max_expansions` (integer, default: 10) - Max related entities (1-100)
- `min_confidence` (float, default: 0.3) - Relationship confidence threshold (0.0-1.0)
- `expansion_depth` (integer, default: 1) - Traversal depth (1-3)

**Response** (200 OK):

```json
{
  "success": true,
  "original_entities": ["FastAPI"],
  "expanded_entities": [
    {
      "entity_id": "4:abc:125",
      "text": "Pydantic",
      "normalized": "pydantic",
      "type_primary": "Library",
      "type_full": "Programming::Library",
      "mention_count": 78,
      "relationship_type": "uses",
      "relationship_confidence": 0.9,
      "path_distance": 1
    },
    {
      "entity_id": "4:abc:126",
      "text": "Uvicorn",
      "normalized": "uvicorn",
      "type_primary": "Server",
      "type_full": "Web::Server",
      "mention_count": 45,
      "relationship_type": "uses",
      "relationship_confidence": 0.7,
      "path_distance": 1
    }
  ],
  "total_discovered": 2
}
```

**Example**:

```bash
curl -X POST http://localhost:8088/api/v1/expand/entities \
  -H "Content-Type: application/json" \
  -d '{
    "entity_names": ["FastAPI"],
    "max_expansions": 5,
    "expansion_depth": 1
  }'
```

## Health & Monitoring

### GET /health

Check service health and dependency status.

**Response** (200 OK):

```json
{
  "status": "healthy",
  "timestamp": "2025-10-17T14:32:18.234Z",
  "services": {
    "neo4j": "connected",
    "vllm": "available (meta-llama/Llama-3.1-70B-Instruct)",
    "gliner": "loaded"
  },
  "version": "1.0.0",
  "uptime_seconds": 3600.5
}
```

**Status Values**:
- `healthy` - All services operational
- `degraded` - Some non-critical services unavailable
- `unhealthy` - Critical service unavailable

**Example**:

```bash
curl http://localhost:8088/health | jq
```

### GET /stats

Retrieve processing statistics.

**Response** (200 OK):

```json
{
  "total_documents_processed": 523,
  "total_entities_extracted": 45234,
  "total_relationships_extracted": 12456,
  "avg_processing_time_ms": 8234.5,
  "last_processed_at": "2025-10-17T14:30:00.000Z",
  "queue_size": 0,
  "failed_count": 7
}
```

**Example**:

```bash
curl http://localhost:8088/stats | jq
```

### GET /api/v1/model-info

Get information about loaded ML models.

**Response** (200 OK):

```json
{
  "gliner": {
    "model": "urchade/gliner_large-v2.1",
    "threshold": 0.4,
    "status": "loaded",
    "entity_types_count": 300
  },
  "vllm": {
    "base_url": "http://localhost:8078",
    "model_name": "meta-llama/Llama-3.1-70B-Instruct",
    "status": "connected"
  }
}
```

**Example**:

```bash
curl http://localhost:8088/api/v1/model-info | jq
```

### GET /

Service information endpoint.

**Response** (200 OK):

```json
{
  "service": "kg-service",
  "version": "1.0.0",
  "status": "running",
  "docs": "/docs",
  "health": "/health"
}
```

## Error Handling

### Validation Errors (422)

Returned when request validation fails:

```json
{
  "detail": [
    {
      "loc": ["body", "chunks", 0, "char_end"],
      "msg": "char_end must be greater than char_start",
      "type": "value_error"
    }
  ]
}
```

### Service Errors (500)

Returned when processing fails:

```json
{
  "success": false,
  "error": "Processing failed: vLLM request timeout",
  "error_type": "ModelUnavailableError",
  "content_id": 123,
  "timestamp": "2025-10-17T14:32:18.234Z"
}
```

### Service Unavailable (503)

Returned when KG processor not initialized:

```json
{
  "success": false,
  "error": "KG processor not initialized",
  "error_type": "ServiceUnavailableError",
  "timestamp": "2025-10-17T14:32:18.234Z"
}
```

## Response Models

### Entity Object

```json
{
  "text": "FastAPI",
  "normalized": "fastapi",
  "type_primary": "Framework",
  "type_sub1": "Backend",
  "type_sub2": "Python",
  "type_sub3": null,
  "type_full": "Framework::Backend::Python",
  "confidence": 0.95,
  "neo4j_node_id": "4:def789:789",
  "context_before": "modern ",
  "context_after": " for building",
  "sentence": "FastAPI is a modern framework for building APIs.",
  "chunk_appearances": [
    {
      "vector_rowid": 45001,
      "chunk_index": 0,
      "offset_start": 120,
      "offset_end": 127
    }
  ],
  "spans_multiple_chunks": false
}
```

### Relationship Object

```json
{
  "subject_text": "FastAPI",
  "subject_neo4j_id": "4:def789:789",
  "predicate": "uses",
  "object_text": "Pydantic",
  "object_neo4j_id": "4:def789:790",
  "confidence": 0.88,
  "context": "FastAPI uses Pydantic for data validation",
  "neo4j_relationship_id": "5:rel123:101",
  "spans_chunks": false,
  "chunk_rowids": [45001]
}
```

## Common Entity Types

- `Framework::Backend::Python` - Python web frameworks
- `Library::Validation::Python` - Python validation libraries
- `Language` - Programming languages
- `Database` - Database systems
- `Tool` - Development tools
- `Concept` - Abstract concepts
- `Organization` - Companies/teams
- `Person` - People
- `Location` - Geographical locations

## Common Relationship Types

- `uses` - Entity A uses Entity B
- `depends_on` - Requires or depends on
- `implements` - Implements or provides
- `extends` - Extends or inherits from
- `competes_with` - Competes in same space
- `part_of` - Component of larger system
- `located_in` - Geographical location
- `CO_OCCURS_WITH` - Appears together in documents

## Python Client Examples

### Basic Entity Extraction

```python
import httpx
import asyncio

async def extract_entities():
    client = httpx.AsyncClient()

    response = await client.post(
        "http://localhost:8088/api/v1/ingest",
        json={
            "content_id": 1,
            "url": "https://example.com",
            "title": "Test",
            "markdown": "FastAPI is a web framework using Python.",
            "chunks": [{
                "vector_rowid": 1,
                "chunk_index": 0,
                "char_start": 0,
                "char_end": 50,
                "text": "FastAPI is a web framework using Python."
            }]
        }
    )

    result = response.json()
    print(f"Entities: {result['entities_extracted']}")
    return result

asyncio.run(extract_entities())
```

### Search and Expand

```python
async def search_and_expand():
    client = httpx.AsyncClient()

    # Search entities
    search_resp = await client.post(
        "http://localhost:8088/api/v1/search/entities",
        json={"entity_terms": ["FastAPI"], "limit": 10}
    )
    entities = search_resp.json()['entities']

    # Expand related
    expand_resp = await client.post(
        "http://localhost:8088/api/v1/expand/entities",
        json={"entity_names": ["FastAPI"], "max_expansions": 5}
    )
    expanded = expand_resp.json()['expanded_entities']

    print(f"Found {len(entities)} entities")
    print(f"Expanded to {len(expanded)} related entities")

asyncio.run(search_and_expand())
```

## Next Steps

- [Getting Started](getting-started.html) - Installation and usage
- [Configuration](configuration.html) - Configuration options
- [Architecture](architecture.html) - System design
