---
layout: default
title: API Reference
parent: robaikg
nav_order: 5
---

# API Reference

Complete API documentation for robaikg knowledge graph service endpoints.

## Base URL

```
http://localhost:8088
```

All POST/PUT endpoints require `Content-Type: application/json` header.

## Authentication

Queue management endpoints require Bearer token authentication:

```bash
Authorization: Bearer ${OPENAI_API_KEY}
```

## Endpoint Categories

- [Core Processing](#core-processing) - Document ingestion and extraction
- [Search Operations](#search-operations) - Entity/chunk search and expansion
- [Queue Management](#queue-management) - Background processing queue
- [Database Access](#database-access) - Vector database queries
- [Monitoring](#monitoring) - Health checks and statistics

---

## Core Processing

### POST /api/v1/ingest

Process document for entity and relationship extraction.

**Request:**
```json
{
  "content_id": 123,
  "url": "https://docs.fastapi.com",
  "title": "FastAPI Documentation",
  "markdown": "# FastAPI\n\nFastAPI is a modern...",
  "chunks": [
    {
      "vector_rowid": 45001,
      "chunk_index": 0,
      "char_start": 0,
      "char_end": 2500,
      "text": "# FastAPI\n\nFastAPI is..."
    }
  ],
  "metadata": {
    "tags": "python,api",
    "timestamp": "2025-11-18T12:00:00Z"
  }
}
```

**Response (200 OK):**
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
      "type_sub3": null,
      "type_full": "Framework::Backend::Python",
      "confidence": 0.95,
      "neo4j_node_id": "4:entity:789",
      "context_before": "modern web ",
      "context_after": " for building",
      "sentence": "FastAPI is a modern web framework",
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
      "subject_normalized": "fastapi",
      "predicate": "uses",
      "object_text": "Pydantic",
      "object_normalized": "pydantic",
      "confidence": 0.88,
      "context": "FastAPI uses Pydantic for data validation",
      "neo4j_relationship_id": "5:rel:101",
      "spans_chunks": false,
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

**Error (500):**
```json
{
  "success": false,
  "error": "Processing failed: vLLM timeout",
  "error_type": "ProcessingError",
  "timestamp": "2025-11-18T12:00:00Z"
}
```

**Processing Steps:**
1. LLM extracts entities and relationships from markdown
2. Entities mapped to chunks using character offsets
3. Graph data stored in Neo4j
4. Results returned for SQLite storage

**Performance:**
- Small docs (< 5K words): 2-4 seconds
- Medium docs (5-20K words): 4-8 seconds
- Large docs (> 20K words): 10-30 seconds

---

## Search Operations

### POST /api/v1/search/entities

Search for entities by text matching.

**Request:**
```json
{
  "entity_terms": ["FastAPI", "Python"],
  "limit": 50,
  "min_mentions": 1
}
```

**Response (200 OK):**
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
    }
  ],
  "total_found": 1
}
```

**Parameters:**
- `entity_terms`: Array of search terms (case-insensitive)
- `limit`: Max results per term (1-500, default 50)
- `min_mentions`: Minimum mention count (default 1)

**Use Cases:**
- Find entities matching query keywords
- Get entity mention counts
- Filter by mention frequency

---

### POST /api/v1/search/chunks

Find chunks containing specified entities.

**Request:**
```json
{
  "entity_names": ["FastAPI", "Pydantic"],
  "limit": 100,
  "include_document_info": true
}
```

**Alternative (by entity IDs):**
```json
{
  "entity_ids": ["4:entity:789", "4:entity:790"],
  "limit": 100,
  "include_document_info": true
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "chunks": [
    {
      "chunk_id": "4:chunk:12345",
      "vector_rowid": 45001,
      "chunk_index": 0,
      "entity_count": 2,
      "matched_entities": ["FastAPI", "Pydantic"],
      "document_url": "https://docs.fastapi.com",
      "document_title": "FastAPI Documentation"
    }
  ],
  "total_found": 1
}
```

**Parameters:**
- `entity_names` OR `entity_ids`: Entities to search for
- `limit`: Max chunks to return (1-1000, default 100)
- `include_document_info`: Include URL/title (default true)

**Use Cases:**
- Graph-powered retrieval for RAG
- Find documents containing specific entities
- Combine with vector search for hybrid retrieval

---

### POST /api/v1/expand/entities

Discover related entities through graph relationships.

**Request:**
```json
{
  "entity_names": ["FastAPI"],
  "max_expansions": 10,
  "min_confidence": 0.3,
  "expansion_depth": 1
}
```

**Response (200 OK):**
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
    }
  ],
  "total_discovered": 1
}
```

**Parameters:**
- `entity_names`: Starting entities for expansion
- `max_expansions`: Max related entities to return (1-100, default 10)
- `min_confidence`: Minimum relationship confidence (0.0-1.0, default 0.3)
- `expansion_depth`: Traversal depth (1-3, default 1)

**Relationship Confidence:**
- `cooccurrence_count >= 5`: 0.9 (very strong)
- `cooccurrence_count >= 3`: 0.7 (strong)
- `cooccurrence_count >= 2`: 0.5 (moderate)

**Use Cases:**
- Query expansion for RAG
- Discover semantically related concepts
- Build entity recommendation systems

---

## Queue Management

**Authentication Required:** All queue endpoints require Bearer token.

### POST /api/v1/queue/claim-items

Atomically claim pending queue items for processing.

**Request:**
```json
{
  "batch_size": 5,
  "worker_id": "worker-1"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "items": [
    {
      "queue_id": 456,
      "content_id": 123,
      "priority": 0,
      "url": "https://example.com",
      "title": "Example Document",
      "markdown": "# Example...",
      "metadata": {}
    }
  ],
  "claimed_count": 1
}
```

**Parameters:**
- `batch_size`: Max items to claim (1-50, default 5)
- `worker_id`: Unique worker identifier

---

### GET /api/v1/queue/chunks/{content_id}

Get chunk metadata for content.

**Response (200 OK):**
```json
{
  "success": true,
  "content_id": 123,
  "chunks": [
    {
      "vector_rowid": 45001,
      "chunk_index": 0,
      "char_start": 0,
      "char_end": 2500,
      "text": "# Example...",
      "word_count": 450
    }
  ]
}
```

**Note:** `vector_rowid` equals `content_chunks.rowid` in SQLite.

---

### POST /api/v1/queue/write-results

Write KG processing results back to database.

**Request:**
```json
{
  "content_id": 123,
  "entities_extracted": 87,
  "relationships_extracted": 43,
  "neo4j_document_id": "4:doc:456",
  "entities": [...],
  "relationships": [...]
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Successfully wrote KG results for content 123"
}
```

**Database Updates:**
1. `crawled_content`: Sets `kg_processed=1`, entity/relationship counts
2. `chunk_entities`: Inserts all entity appearances
3. `chunk_relationships`: Inserts all relationships
4. `content_chunks`: Sets `kg_processed=1`

---

### POST /api/v1/queue/mark-completed

Mark queue item as completed.

**Request:**
```json
{
  "queue_id": 456
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Queue item 456 marked as completed"
}
```

---

### POST /api/v1/queue/mark-failed

Mark queue item as failed with retry logic.

**Request:**
```json
{
  "queue_id": 456,
  "error_message": "vLLM timeout after 1800 seconds",
  "max_retries": 3
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "retry_count": 1,
  "new_priority": 1,
  "new_status": "pending",
  "message": "Marked item as pending (retry 1/3)"
}
```

**Retry Logic:**
- If `retry_count < max_retries`: Re-queue with increased priority
- Otherwise: Move to `dead_letter` status

---

### POST /api/v1/queue/mark-stale

Mark stale processing items as long_running.

**Request:**
```json
{
  "stale_minutes": 60
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "marked_count": 2,
  "message": "Marked 2 stale items as long_running"
}
```

---

### GET /api/v1/queue/stats

Get queue statistics by status.

**Response (200 OK):**
```json
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

---

### GET /api/v1/queue/long-running

Get items processing longer than threshold.

**Query Parameters:**
- `minutes_threshold`: Minutes threshold (default 60)

**Response (200 OK):**
```json
{
  "success": true,
  "items": [
    {
      "queue_id": 789,
      "content_id": 145,
      "url": "https://example.com/long-doc",
      "processing_started_at": "2025-11-18T10:30:00Z",
      "minutes_elapsed": 75.3
    }
  ],
  "count": 1
}
```

---

## Database Access

### GET /api/v1/db/stats

Get vector database statistics.

**Authentication Required**

**Response (200 OK):**
```json
{
  "success": true,
  "total_documents": 523,
  "total_chunks": 12456,
  "total_vectors": 12456,
  "database_size_mb": 450.2,
  "avg_chunks_per_doc": 23.8
}
```

---

## Monitoring

### GET /health

Service health check.

**Response (200 OK - Healthy):**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-18T12:00:00Z",
  "services": {
    "neo4j": "connected",
    "vllm": "connected (Qwen/Qwen2.5-7B-Instruct)",
    "llm_extraction": "available"
  },
  "version": "1.0.0",
  "uptime_seconds": 3600.5
}
```

**Response (200 OK - Degraded):**
```json
{
  "status": "degraded",
  "services": {
    "neo4j": "connected",
    "vllm": "error: Connection refused",
    "llm_extraction": "unavailable"
  }
}
```

**Status Values:**
- `healthy`: All services operational
- `degraded`: Some services unavailable
- `unhealthy`: Critical services down

---

### GET /stats

Service processing statistics.

**Response (200 OK):**
```json
{
  "total_documents_processed": 523,
  "total_entities_extracted": 45234,
  "total_relationships_extracted": 12456,
  "avg_processing_time_ms": 2341.5,
  "last_processed_at": "2025-11-18T11:55:00Z",
  "queue_size": 0,
  "failed_count": 2
}
```

---

### GET /api/v1/extraction/status

Get vLLM extraction pipeline status.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "active_extractions": 2,
  "total_queued": 1234,
  "total_completed": 1200,
  "total_failed": 12,
  "max_concurrent": 4,
  "slots_available": 2,
  "timestamp": "2025-11-18T12:00:00Z"
}
```

**Status Values:**
- `healthy`: `active_extractions < max_concurrent`
- `at_capacity`: All slots in use

---

### GET /api/v1/model-info

Get loaded model information.

**Response (200 OK):**
```json
{
  "extraction_method": "llm_unified",
  "entity_min_confidence": 0.4,
  "augmentation_llm": {
    "base_url": "http://localhost:8078",
    "model_name": "Qwen/Qwen2.5-7B-Instruct",
    "status": "connected"
  }
}
```

---

## Data Models

### Entity

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
  "neo4j_node_id": "4:entity:789",
  "context_before": "modern web ",
  "context_after": " for building",
  "sentence": "FastAPI is a modern web framework",
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
```

### Relationship

```json
{
  "subject_text": "FastAPI",
  "subject_normalized": "fastapi",
  "predicate": "uses",
  "object_text": "Pydantic",
  "object_normalized": "pydantic",
  "confidence": 0.88,
  "context": "FastAPI uses Pydantic for data validation",
  "neo4j_relationship_id": "5:rel:101",
  "spans_chunks": false,
  "chunk_rowids": [45001]
}
```

### Chunk Metadata

```json
{
  "vector_rowid": 45001,
  "chunk_index": 0,
  "char_start": 0,
  "char_end": 2500,
  "text": "# FastAPI\n\nFastAPI is a modern...",
  "word_count": 450
}
```

---

## Error Handling

All endpoints return consistent error responses:

**Error Response:**
```json
{
  "success": false,
  "error": "Error message description",
  "error_type": "HTTPException",
  "content_id": 123,
  "timestamp": "2025-11-18T12:00:00Z"
}
```

**Common Status Codes:**
- `200 OK`: Request succeeded
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Missing or invalid API key
- `500 Internal Server Error`: Processing failure
- `503 Service Unavailable`: Dependent service down

---

## Rate Limiting

**Queue Endpoints:**
- Authentication required via Bearer token
- No explicit rate limiting (controlled by worker batch size)

**Public Endpoints:**
- No rate limiting currently implemented
- Consider implementing for production

---

## Integration Examples

### Python

```python
import httpx

# Ingest document
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8088/api/v1/ingest",
        json={
            "content_id": 123,
            "url": "https://example.com",
            "title": "Example",
            "markdown": "# Example...",
            "chunks": [...]
        }
    )
    result = response.json()
    print(f"Extracted {result['entities_extracted']} entities")
```

### JavaScript

```javascript
// Search entities
const response = await fetch('http://localhost:8088/api/v1/search/entities', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    entity_terms: ['FastAPI'],
    limit: 50
  })
});

const data = await response.json();
console.log(`Found ${data.total_found} entities`);
```

### cURL

```bash
# Check health
curl http://localhost:8088/health

# Get queue stats (with auth)
curl http://localhost:8088/api/v1/queue/stats \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

---

## Performance Tips

1. **Batch Processing:** Use queue system for high throughput
2. **Parallel Requests:** Search/expand endpoints are fast and can run concurrently
3. **Timeouts:** Set appropriate client timeouts for large documents (30-60s)
4. **Monitoring:** Use `/api/v1/extraction/status` to avoid overwhelming vLLM

---

## Next Steps

- **Getting Started:** See [Getting Started](getting-started.md) for usage examples
- **Architecture:** Review [Architecture](architecture.md) for pipeline details
- **Configuration:** Check [Configuration](configuration.md) for tuning parameters
