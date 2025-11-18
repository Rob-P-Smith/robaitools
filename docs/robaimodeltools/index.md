---
layout: default
title: robaimodeltools
nav_order: 4
has_children: true
---

# robaimodeltools

**Version:** 1.0.0

A sophisticated, production-grade shared library implementing a complete Retrieval-Augmented Generation (RAG) system with integrated knowledge graph processing, semantic search, web crawling, and data persistence.

## Overview

**robaimodeltools** is a 7,786-line Python library that serves as the core business logic backbone for both the REST API ([robairagapi](../robairagapi)) and MCP server ([robaitragmcp](../robaitragmcp)) in the robaitools ecosystem.

### Key Characteristics

- **Knowledge graph-enhanced semantic search** with entity extraction
- **Parallel vector and graph retrieval** with intelligent merging
- **Multi-signal ranking** (vector similarity, graph relevance, BM25, recency, title matching)
- **Recursive web crawling** with language detection and content quality filtering
- **Thread-safe operations** with concurrent execution support
- **Comprehensive domain blocking** and content safety features

## What It Does

- **Dual-mode database**: RAM with differential sync or traditional disk-based operation
- **5-phase search pipeline**: Query parsing → Parallel retrieval → Entity expansion → Multi-signal ranking → Response formatting
- **Comprehensive security**: SQL injection defense, input validation, and content safety filtering
- **Production-ready**: Error handling, graceful degradation, async/sync support, and monitoring

## Quick Start

```python
from robaimodeltools.operations.crawler import Crawl4AIRAG

# Initialize
crawler = Crawl4AIRAG()

# Simple search
results = crawler.search_knowledge(
    query="How to use FastAPI with SQLAlchemy?",
    top_k=10,
    tags="python"
)

# Crawl and store
result = crawler.crawl_and_store(
    url="https://example.com/article",
    retention_policy="permanent",
    tags="python,tutorial"
)
```

## Key Features

### Search Capabilities

- **Vector Similarity Search**: 384-dimensional semantic search using SQLite-vec
- **Knowledge Graph Search**: Entity-based retrieval via Neo4j relationship traversal
- **Hybrid Search**: Parallel vector+graph execution with score combination
- **Entity Expansion**: Related concept discovery through knowledge graph relationships
- **Multi-Signal Ranking**: 5-weighted signals (35% vector, 25% graph, 20% BM25, 10% recency, 10% title)
- **Context Extraction**: Sentence-level relevance scoring for result previews
- **Query Intelligence**: Intent detection and entity extraction with GLiNER

### Crawling Capabilities

- **Single URL Crawling**: Stateless content extraction via Crawl4AI service
- **Crawl & Store**: Automatic embedding generation and knowledge graph queue population
- **Deep Crawling**: Breadth-first search with configurable depth (1-5) and page limits (1-250)
- **Language Filtering**: Keyword-based English content detection
- **Domain Blocking**: Wildcard, substring, and exact pattern matching
- **Rate Limiting**: 0.5-second delays between requests
- **Error Detection**: Multi-signal error page identification

### Data Management

- **Dual-Mode Database**: RAM mode with differential sync or disk-only mode
- **Content Cleaning**: Navigation/boilerplate removal to improve embedding quality
- **Chunking**: Character-based (default 1000 chars) with quality filtering
- **Embedding Generation**: Automatic via SentenceTransformer (all-MiniLM-L6-v2)
- **Retention Policies**: `permanent`, `session_only`, `30_days`
- **Tag-Based Organization**: Flexible content categorization and filtering
- **SQL Injection Defense**: Comprehensive input sanitization

## Architecture Overview

### 3-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     OPERATIONS LAYER                        │
│  Orchestration, validation, business logic coordination     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                      SEARCH LAYER                           │
│  5-phase RAG pipeline with KG enhancement                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                       DATA LAYER                            │
│  Persistence, security, content processing                  │
└─────────────────────────────────────────────────────────────┘
```

### 5-Phase RAG Pipeline

1. **Phase 1: Query Understanding** - GLiNER entity extraction + query embedding
2. **Phase 2: Parallel Retrieval** - Concurrent vector + Neo4j graph search
3. **Phase 3: Knowledge Graph Expansion** - Related entity discovery
4. **Phase 4: Multi-Signal Ranking** - 5 signals weighted combination
5. **Phase 5: Response Formatting** - Structured API response generation

## Statistics

- **Total Lines**: 7,786 lines of Python code
- **Main Layers**: 3 (Data, Operations, Search)
- **Entity Types**: 119 across 11 categories
- **Database Tables**: 8 core tables + virtual table
- **Dependencies**: 7 direct Python packages
- **Search Types**: Vector, graph, hybrid, entity-expanded, ranked

## Next Steps

- [Getting Started](getting-started.html) - Installation and basic usage
- [Architecture](architecture.html) - Detailed architecture documentation
- [API Reference](api-reference.html) - Complete API documentation
- [Configuration](configuration.html) - Configuration options and settings

## Related Components

- [robairagapi](../robairagapi/) - REST API that uses robaimodeltools
- [robaitragmcp](../robaitragmcp/) - MCP server that uses robaimodeltools
- [robaikg](../robaikg/) - Knowledge graph service for entity extraction
