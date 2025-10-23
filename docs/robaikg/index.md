---
layout: default
title: robaikg
nav_order: 4
has_children: true
---

# robaikg

**Knowledge Graph Extraction and Management Service**

A semantic understanding layer that transforms unstructured documents into structured knowledge graphs using AI/ML models. Extracts entities, discovers relationships, and stores them in Neo4j for graph-enhanced search and retrieval.

## Overview

robaikg is the intelligence layer of the RobAI ecosystem. It analyzes markdown documents to:

- **Extract Entities** (300+ types): People, places, technologies, concepts with confidence scoring
- **Discover Relationships** (50+ types): Semantic connections between entities (uses, competes_with, located_in, etc.)
- **Map Document Structure**: Chunk-level attribution for precise retrieval and highlighting
- **Build Knowledge Graph**: Interconnected graph stored in Neo4j for relationship-based search

### What It Does

1. **Entity Extraction**
   - GLiNER-based entity recognition (300+ entity types)
   - Hierarchical type system (primary/sub1/sub2/sub3)
   - Confidence scoring (0.0-1.0)
   - Context preservation with position tracking
   - Performance: ~2-3 seconds per document

2. **Relationship Extraction**
   - vLLM-powered semantic relationship discovery
   - 50+ relationship types with validation
   - JSON-guided generation for structured output
   - Bidirectional relationship mapping
   - Performance: ~5-10 seconds per document

3. **Chunk Mapping**
   - Maps entities to specific document chunks
   - Precise character position tracking
   - Enables highlighting and context retrieval
   - Supports cross-chunk relationships

4. **Graph Storage**
   - Neo4j database with optimized schema
   - Document → Chunk → Entity hierarchy
   - Dynamic semantic relationships
   - Bidirectional links to SQLite

## Key Features

### Core Capabilities

- **300+ Entity Types**: Person, Organization, Technology, Location, Concept, and more
- **50+ Relationship Types**: Uses, Competes_with, Located_in, Depends_on, etc.
- **Async Processing**: Non-blocking queue-based extraction
- **Bidirectional Links**: SQLite ↔ Neo4j integration
- **Context Preservation**: Full text extraction with position mapping
- **Hierarchical Entities**: Multi-level entity classification
- **FastAPI Service**: HTTP/JSON REST API for integration

### Security & Performance

- **Defense-in-Depth**: Input validation, rate limiting, error handling
- **Graceful Degradation**: Falls back to vector search if KG unavailable
- **Optimized Schema**: Indexed Neo4j graph for fast traversal
- **Batch Processing**: Efficient bulk entity/relationship processing
- **Auto-cleanup**: Expired session cleanup every hour

## System Architecture

```
Raw Documents
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

## Components

### kg-service (FastAPI)

Main service providing REST API endpoints for entity/relationship extraction, search, and graph querying.

**Endpoints** (8 total):
- Entity extraction
- Relationship extraction
- Graph search
- Entity expansion
- Status monitoring

### Storage

**Neo4j Graph Database**:
- Entity nodes with metadata
- Relationship edges with types
- Document/chunk hierarchy
- Full-text search indexes

**SQLite Integration**:
- Bidirectional links (content_id, vector_rowid)
- Chunk position mapping
- Content relationships

## Statistics

- **Total Lines**: ~2,500 lines of Python code
- **REST Endpoints**: 8 main endpoints
- **Entity Types**: 300+ supported types
- **Relationship Types**: 50+ semantic relationship types
- **Database**: Neo4j graph + SQLite links
- **Response Times**: 2-10 seconds per document (depends on size)

## Quick Start

### Docker Deployment (Recommended)

```bash
cd robaikg
cp .env.example .env
docker compose up -d
```

### Local Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

### Verify Installation

```bash
curl http://localhost:8088/health
```

## Use Cases

**Extracted Knowledge Graph**:
- Find all technologies mentioned in documents
- Discover relationships between concepts
- Highlight where entities appear in text
- Power graph-based search and recommendations
- Enable relationship-based document filtering

**Integration Points**:
- robaitragmcp uses KG for hybrid search
- robairagapi uses KG for entity expansion
- robaimodeltools integrates KG results into RAG pipeline

## Next Steps

- [Getting Started](getting-started.html) - Installation and setup
- [Configuration](configuration.html) - Environment configuration
- [API Reference](api-reference.html) - Complete endpoint documentation
- [Architecture](architecture.html) - System design and patterns
