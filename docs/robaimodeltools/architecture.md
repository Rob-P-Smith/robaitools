---
layout: default
title: Architecture
parent: robaimodeltools
nav_order: 4
---

# Architecture

Detailed architecture documentation for robaimodeltools.

## System Overview

robaimodeltools is a **7,786-line Python library** implementing a 3-layer architecture with a 5-phase RAG pipeline.

### High-Level Design

```
External Consumers (robairagapi, robaitragmcp)
    ↓ Direct Python Imports
┌─────────────────────────────────────────────────────────────┐
│                     OPERATIONS LAYER                        │
│  Orchestration, validation, business logic coordination     │
│  ├─ crawler.py (facade orchestrator)                       │
│  ├─ crawl_operations.py, deep_crawl.py                     │
│  ├─ search_operations.py, domain_management.py             │
│  └─ queue_managers.py, validation.py                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                      SEARCH LAYER                           │
│  5-phase RAG pipeline with KG enhancement                   │
│  ├─ Phase 1: query_parser.py (GLiNER extraction)          │
│  ├─ Phase 2: vector_retriever.py + graph_retriever.py     │
│  ├─ Phase 3: entity_expander.py                            │
│  ├─ Phase 4: advanced_ranker.py                            │
│  └─ Phase 5: response_formatter.py                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                       DATA LAYER                            │
│  Persistence, security, content processing                  │
│  ├─ storage.py (RAGDatabase + GLOBAL_DB)                   │
│  ├─ sync_manager.py (differential sync)                    │
│  ├─ content_cleaner.py (quality filtering)                 │
│  └─ dbdefense.py (SQL injection prevention)                │
└────────────┬────────────────────────────────────────────────┘
             │
             ├──→ Crawl4AI Service (port 11235)
             ├──→ SQLite Database (crawl4ai_rag.db)
             ├──→ KG Service (port 8088)
             └──→ Neo4j Graph DB (port 7687)
```

## Layer Architecture

### Operations Layer (1,436 lines)

**Purpose**: Orchestration, validation, and business logic coordination

**Key Pattern**: Facade Orchestrator with delegating modules

**Components**:

| Module | Lines | Purpose |
|--------|-------|---------|
| `crawler.py` | 250 | Facade orchestrator (zero business logic) |
| `crawl_operations.py` | ~300 | Single & batch crawling |
| `deep_crawl.py` | ~250 | BFS recursive crawling |
| `search_operations.py` | ~200 | Semantic search operations |
| `domain_management.py` | ~150 | Blocklist operations |
| `queue_managers.py` | ~150 | Session & queue tracking |
| `validation.py` | ~136 | Input sanitization |

**Design Principles**:
- Single entry point (Crawl4AIRAG)
- Clear delegation to specialized modules
- Minimal coupling between operation types
- Standardized return dictionaries

### Search Layer (3,856 lines)

**Purpose**: 5-phase knowledge graph-enhanced RAG pipeline

**Key Pattern**: Progressive Enrichment Pipeline

**5-Phase Flow**:

```
Phase 1: Query Understanding
    ├─ query_parser.py (~400 lines)
    ├─ GLiNER entity extraction (119 types)
    ├─ Intent detection
    └─ Query normalization & variants
    ↓
Phase 2: Parallel Retrieval
    ├─ vector_retriever.py (~350 lines)
    │   └─ SQLite-vec cosine similarity
    ├─ graph_retriever.py (~250 lines)
    │   └─ Neo4j entity retrieval
    └─ hybrid_retriever.py (~400 lines)
        └─ Concurrent execution with merging
    ↓
Phase 3: Knowledge Graph Expansion
    ├─ entity_expander.py (~300 lines)
    │   └─ Relationship traversal
    └─ expanded_retriever.py (~350 lines)
        └─ Dual retrieval (original + expanded)
    ↓
Phase 4: Multi-Signal Ranking
    └─ advanced_ranker.py (~600 lines)
        ├─ Vector similarity (35%)
        ├─ Graph relevance (25%)
        ├─ BM25 text match (20%)
        ├─ Document recency (10%)
        └─ Title matching (10%)
    ↓
Phase 5: Response Formatting
    └─ response_formatter.py (~400 lines)
        ├─ Structured JSON response
        ├─ Score breakdowns
        ├─ Suggested queries
        └─ Related entities
```

**Integration**:
- `final_retriever.py` - End-to-end orchestration
- `search_handler.py` - High-level interface (singleton)
- `simple_search.py` - Baseline vector-only fallback

### Data Layer (2,494 lines)

**Purpose**: Database operations, persistence, content processing, security

**Key Pattern**: Dual-Mode Database with Defense-in-Depth

**Components**:

| Module | Lines | Purpose |
|--------|-------|---------|
| `storage.py` | ~800 | Core database abstraction |
| `sync_manager.py` | ~400 | RAM/Disk differential sync |
| `content_cleaner.py` | ~500 | Post-crawl processing |
| `dbdefense.py` | ~400 | SQL injection prevention |
| `dbDump.py` | ~200 | Database inspection utility |

**Database Modes**:

```
Disk-Only Mode:
    Direct SQLite file operations
    ↓
    No sync overhead
    ↓
    Traditional persistence

RAM Mode:
    In-Memory SQLite
    ↓
    Trigger-based change tracking (_sync_tracker table)
    ↓
    Differential Sync (idle 5s or periodic 5m)
    ↓
    Disk SQLite (durability)
```

## 5-Phase RAG Pipeline

### Phase 1: Query Understanding

**Purpose**: Extract structured information from natural language queries

**Process**:
1. Load entity taxonomy (119 types from entities.yaml)
2. Extract entities using GLiNER (threshold 0.1)
3. Detect intent (transactional/navigational/informational)
4. Normalize query (lowercase, special char removal)
5. Generate variants (original, entity-emphasized, entity-only)
6. Calculate confidence score

**Output**:
```python
{
    "original_query": str,
    "normalized_query": str,
    "entities": [{"text": str, "type": str, "confidence": float}],
    "intent": str,
    "confidence": float,
    "variants": [str]
}
```

### Phase 2: Parallel Retrieval

**Purpose**: Concurrent vector and graph search

**Vector Retrieval**:
- SQLite-vec cosine similarity
- 384-dimensional embeddings
- Distance-to-similarity: `1 - (distance / 2)`
- Tag filtering with ANY-match semantics
- URL deduplication (keeps highest similarity)

**Graph Retrieval**:
- HTTP communication with kg-service
- Two-step: entity matching → chunk retrieval
- Returns `vector_rowid` references
- Graceful degradation on service unavailability

**Hybrid Merging**:
- Parallel execution via `asyncio.gather`
- Thread pool for SQLite sync operations
- URL-based deduplication with score combination
- Configurable weights (normalized to 1.0)
- Fallback hierarchy: hybrid → vector-only → secondary vector

### Phase 3: Knowledge Graph Expansion

**Purpose**: Discover related entities through relationships

**Process**:
1. POST entities to kg-service `/api/v1/expand/entities`
2. Traverse relationships (USES, DEPENDS_ON edges)
3. Analyze co-occurrence patterns
4. Filter by confidence threshold
5. Deduplicate and rank

**Expanded Retrieval**:
- Original entities: Full weight (100%)
- Expanded entities: Reduced weight (70%)
- URL-based merging with confidence boosting
- Statistics tracking

### Phase 4: Multi-Signal Ranking

**Purpose**: Combine 5 signals for final ranking

**Signals** (normalized to [0,1]):

| Signal | Weight | Purpose |
|--------|--------|---------|
| Vector similarity | 35% | Semantic similarity from embeddings |
| Graph relevance | 25% | Entity-based relevance from KG |
| BM25 text match | 20% | Term frequency matching (simplified) |
| Document recency | 10% | Tiered decay based on age |
| Title matching | 10% | Substring, entity, term overlap |

**Recency Scoring**:
- < 7 days: 1.0
- < 30 days: 0.8
- < 90 days: 0.6
- < 180 days: 0.4
- < 365 days: 0.3
- > 365 days: 0.2

**Context Extraction**:
- Sentence-level scoring
- Query term + entity matching
- Positional bias (earlier = better)
- Word-boundary truncation

### Phase 5: Response Formatting

**Purpose**: Generate structured API response

**Response Structure**:
```python
{
    "success": bool,
    "query": {
        "original": str,
        "normalized": str,
        "entities": [...],
        "intent": str,
        "confidence": float
    },
    "exploration": {
        "original_entity_count": int,
        "expanded_entity_count": int,
        "expansion_relationships": [...],
        "discovered_entities": [...]
    },
    "results": [
        {
            "rank": int,
            "url": str,
            "title": str,
            "preview": str,
            "score": float,
            "score_breakdown": {...},
            "timestamp": str,
            "tags": [str],
            "source": str,
            "entity_mentions": [str]
        }
    ],
    "result_count": int,
    "total_time_ms": int,
    "suggested_queries": [str],
    "related_entities": [...]
}
```

## Design Patterns

### 1. Facade Orchestrator Pattern

**Location**: Operations layer

**Purpose**: Unified interface with specialized delegation

**Benefits**:
- Single entry point
- Isolated testing
- Independent evolution
- Minimal coupling

### 2. Progressive Enrichment Pipeline

**Location**: Search layer

**Purpose**: Build understanding through sequential phases

**Benefits**:
- Graceful degradation
- Transparent intermediate results
- Easy A/B testing
- Clear fallback logic

### 3. Temporal Embedding Separation

**Location**: Search layer (embeddings.py)

**Purpose**: Clear boundary between query-time and index-time embeddings

**Implementation**:
- Query embeddings: Generated on-demand, discarded after use
- Document embeddings: Persisted in SQLite-vec
- Security improvement (no query tracking)
- Storage optimization

### 4. Concurrent Execution with Thread Pools

**Location**: Search layer (hybrid_retriever.py)

**Purpose**: Parallel retrieval without blocking

**Implementation**:
```python
vector_results, graph_results = await asyncio.gather(
    run_in_executor(vector_retriever.retrieve, ...),
    graph_retriever.retrieve_async(...)
)
```

### 5. Dual-Mode Database Strategy

**Location**: Data layer

**Purpose**: Balance performance and durability

**Modes**:
- RAM: Full in-memory with differential sync
- Disk: Traditional file-based operation

**Sync Strategy**:
- Only changed records synchronized
- Dual trigger: idle-based (5s) + periodic (5m)
- Virtual table handling for sqlite-vec

### 6. Singleton Patterns

**Purpose**: Share expensive resources

**Global Singletons**:
- `GLOBAL_DB` - Single database instance
- `get_query_parser()` - Shared GLiNER model
- `get_query_embedder()` - Shared SentenceTransformer
- `get_response_formatter()` - Shared formatter

**Benefits**:
- Amortizes model loading overhead
- Consistent state across operations
- Memory efficiency

### 7. Defense-in-Depth Security

**Location**: Data layer (dbdefense.py, validation.py)

**Layers**:
1. Whitelist-based validation
2. SQL keyword detection
3. NULL byte filtering
4. Maximum length enforcement
5. Type-specific validators

### 8. Score Normalization

**Location**: Search layer (advanced_ranker.py)

**Purpose**: Fair combination of heterogeneous signals

**Process**:
1. Normalize each signal to [0,1]
2. Apply weights (sum to 1.0)
3. Combine linearly
4. Preserve individual scores for transparency

## Performance Characteristics

### Response Times (Typical)

| Operation | Time | Notes |
|-----------|------|-------|
| Vector search | 100-500ms | Simple similarity |
| Hybrid search | 500-2000ms | Includes graph query |
| Full 5-phase pipeline | 1-3s | Complete enrichment |
| Single crawl | 2-10s | Depends on page size |
| Deep crawl | 30-300s | Depends on max_pages |

### Throughput

- Search: ~100 queries/second (RAM mode)
- Crawl & store: ~20 pages/second (Crawl4AI limited)
- Database ops: ~1000 reads/sec, ~500 writes/sec

### Memory Usage

- Base: ~100-300MB (with database loaded)
- Per request: ~1-5MB
- Models: ~500MB (GLiNER + SentenceTransformer)

## Next Steps

- [Getting Started](getting-started.html) - Installation and basic usage
- [Configuration](configuration.html) - Configuration options
- [API Reference](api-reference.html) - Complete API documentation
