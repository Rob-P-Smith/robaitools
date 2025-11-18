---
layout: default
title: robaikg
nav_order: 4
has_children: true
---

# robaikg

Knowledge Graph extraction service that transforms unstructured documents into structured knowledge graphs using AI-powered entity and relationship extraction.

## Overview

robaikg is the **semantic understanding layer** of robaitools. It analyzes markdown documents to extract entities, discover relationships, map them to document chunks, and store everything in Neo4j for graph-enhanced search and retrieval.

**Key Capabilities:**
- **Entity Extraction** - Identifies people, places, technologies, concepts (~110 entity types)
- **Relationship Extraction** - Discovers semantic connections between entities (~50 relationship types)
- **Chunk Mapping** - Maps entities/relationships to precise document locations
- **Graph Storage** - Stores structured knowledge in Neo4j graph database
- **Hybrid Search** - Combines vector search with knowledge graph traversal

## Architecture Position

robaikg sits at **Level 2** in the service stack as the knowledge graph processing layer:

```
┌──────────────────────────────────────────┐
│  LEVEL 0: Content Acquisition            │
│  robaicrawler (Port 11235)               │
│  - Web crawling                          │
│  - Content extraction                    │
└────────────────┬─────────────────────────┘
                 ↓
┌──────────────────────────────────────────┐
│  LEVEL 1: Data Storage                   │
│  robaidata (SQLite DB)                   │
│  - Document storage                      │
│  - Vector embeddings                     │
│  - Queue management                      │
└────────────────┬─────────────────────────┘
                 ↓
┌──────────────────────────────────────────┐
│  LEVEL 2: Knowledge Graph (robaikg)      │
│  ← YOU ARE HERE                          │
│  ┌─────────────────────────────────────┐ │
│  │ kg-service (Port 8088)              │ │
│  │ - Entity extraction (LLM)           │ │
│  │ - Relationship extraction (vLLM)    │ │
│  │ - Chunk mapping                     │ │
│  └─────────────────────────────────────┘ │
│  ┌─────────────────────────────────────┐ │
│  │ Neo4j (Ports 7474, 7687)            │ │
│  │ - Graph storage                     │ │
│  │ - Entity/relationship nodes         │ │
│  └─────────────────────────────────────┘ │
└────────────────┬─────────────────────────┘
                 ↓
┌──────────────────────────────────────────┐
│  LEVEL 3: Search & Retrieval             │
│  robaitragmcp, robairagapi               │
│  - Hybrid RAG + KG search                │
│  - Entity expansion                      │
└──────────────────────────────────────────┘
```

**Dependencies:**
- **Requires:** Neo4j (graph DB), vLLM (optional for relationships)
- **Used By:** robaitragmcp (hybrid search), robairagapi (entity expansion)
- **Failure Impact:** Graceful degradation to vector-only search

## What's Inside

### Components

#### 1. kg-service (FastAPI Service)
**Container:** `robaikg`
**Port:** 8088
**Purpose:** HTTP API for entity/relationship extraction and graph operations

**Key Features:**
- LLM-based entity extraction
- vLLM-powered relationship discovery
- Chunk-level attribution
- Neo4j graph storage
- Search and expansion endpoints

#### 2. Neo4j Graph Database
**Container:** `robaineo4j`
**Ports:** 7474 (HTTP Browser), 7687 (Bolt Driver)
**Purpose:** Stores knowledge graph with entities, relationships, and document hierarchy

**Schema:**
- **Nodes:** Document, Chunk, Entity
- **Relationships:** HAS_CHUNK, MENTIONED_IN, semantic relationships (USES, COMPETES_WITH, etc.)
- **Plugins:** APOC (graph algorithms)

#### 3. Background Workers (Coordinator)
**Location:** `robaikg/coordinator/`
**Purpose:** Queue-based background processing

**Components:**
- `KGWorker` - Single worker for queue processing
- `KGWorkerManager` - Worker pool orchestration
- `KGServiceConfig` - Circuit breaker and health checks
- `KGDashboard` - Web-based monitoring UI

### Processing Pipeline

```
1. Document arrives from robaidata queue
   ↓
2. Entity Extraction (LLM)
   - Extracts ~110 entity types
   - Hierarchical classification (Framework::Backend::Python)
   - Confidence scoring
   ↓
3. Relationship Extraction (vLLM)
   - Discovers ~50 relationship types
   - JSON-guided generation
   - Relationship validation
   ↓
4. Chunk Mapping
   - Maps entities to chunks by position
   - Tracks offsets within chunks
   ↓
5. Neo4j Storage
   - Create/update entity nodes
   - Create relationship edges
   - Link to document/chunk hierarchy
   ↓
6. Results written back to SQLite
   - Update crawled_content (kg_processed=1)
   - Insert chunk_entities
   - Insert chunk_relationships
```

## Key Features

**Entity Types (~110 types):**
- **Technology:** Framework, Library, Language, Database, Tool, Platform
- **Concept:** Algorithm, Pattern, Practice, Principle, Methodology
- **Organization:** Company, Team, Project, Institution
- **Person:** Developer, Author, Contributor
- **Location:** Region, Country, City
- **Data:** Database, Warehouse, Lake, Pipeline
- **AI:** Model, LLM, Framework, Algorithm
- **And 90+ more**

**Relationship Types (~50 types):**
- **Technical:** uses, depends_on, implements, extends, integrates_with
- **Comparative:** competes_with, similar_to, different_from, alternative_to
- **Hierarchical:** part_of, contains, belongs_to, category_of
- **Temporal:** precedes, follows, replaces, supersedes
- **Functional:** processes, generates, transforms, analyzes
- **And 35+ more**

**Performance:**
- Entity extraction: ~2-3 seconds per document
- Relationship extraction: ~5-10 seconds per document
- Total pipeline: ~8-15 seconds per document
- Entity search: <100ms
- Entity expansion: <500ms (1-2 hop traversal)

## Data Flow

**Document Processing:**
```
1. User crawls URL → robaicrawler extracts content
2. robaimodeltools stores in SQLite (crawled_content, content_chunks, content_vectors)
3. Queue item created (kg_processing_queue, status='pending')
4. Background worker polls queue (every 5s)
5. Worker fetches markdown + chunks from SQLite
6. Worker POSTs to kg-service /api/v1/ingest
7. kg-service extracts entities + relationships (8-15s)
8. kg-service stores in Neo4j
9. Worker writes results back to SQLite
10. Queue item updated (status='completed')
```

**Hybrid Search:**
```
1. Vector search finds top-k chunks (SQLite-vec)
2. Neo4j expands with related entities (1-2 hop traversal)
3. Retrieve chunks containing expanded entities
4. Merge and rank by entity density
5. Return combined results (RAG + KG)
```

## Use Cases

**Knowledge Graph Exploration:**
- Find all technologies mentioned in documents
- Discover relationships between concepts
- Map technology ecosystems (what uses what)
- Identify competing or alternative technologies

**Enhanced Search:**
- Expand queries with related entities
- Filter by entity types
- Rank by entity density
- Highlight entity mentions in chunks

**Integration:**
- robaitragmcp uses KG for hybrid search
- robairagapi exposes entity search endpoints
- robaimodeltools integrates KG results into RAG pipeline

## Quick Links

- [Getting Started](getting-started.md) - Installation, setup, first extraction
- [Architecture](architecture.md) - Technical deep dive, pipeline details
- [Configuration](configuration.md) - Environment variables, tuning
- [API Reference](api-reference.md) - Endpoints, models, integration

## Technology Stack

- **API Framework:** FastAPI (async/await)
- **Language:** Python 3.11
- **Graph Database:** Neo4j 5.25 Community Edition
- **Entity Extraction:** LLM-based (via vLLM)
- **Relationship Extraction:** vLLM (Qwen or custom model)
- **Graph Driver:** neo4j-driver (async)
- **Data Validation:** Pydantic v2

## Resource Requirements

**Minimum:**
- CPU: 2 cores
- Memory: 4GB (2GB Neo4j + 1GB kg-service + 1GB overhead)
- Disk: 5GB (Neo4j data + model cache)

**Recommended:**
- CPU: 4 cores
- Memory: 18GB (16GB Neo4j + 2GB kg-service)
- Disk: 20GB (for growth)

**Current Usage (4,105 documents):**
- Neo4j data: ~2GB
- Model cache: ~500MB
- Total: ~2.5GB

## Related Components

**Upstream Dependencies:**
- robaicrawler - Web content source
- robaidata - Queue management and storage

**Downstream Consumers:**
- robaitragmcp - Hybrid RAG+KG search
- robairagapi - Entity search REST API

**Shared Libraries:**
- robaimodeltools - Core RAG operations and database access

## Next Steps

1. **New Users:** Start with [Getting Started](getting-started.md) for installation
2. **Developers:** Review [Architecture](architecture.md) for implementation details
3. **Operators:** Check [Configuration](configuration.md) for tuning options
4. **Integrators:** See [API Reference](api-reference.md) for endpoint documentation
