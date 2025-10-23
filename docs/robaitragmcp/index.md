---
layout: default
title: robaitragmcp
nav_order: 5
has_children: true
---

# robaitragmcp

**Model Context Protocol (MCP) Server for Retrieval-Augmented Generation**

A high-performance MCP server that provides AI assistants with powerful web crawling and knowledge retrieval capabilities. Integrates Crawl4AI for extraction, sqlite-vec for vector search, and optional Knowledge Graph enhancement via Neo4j.

## Overview

robaitragmcp bridges AI assistants (Claude, LM-Studio, etc.) with the RobAI RAG system through the Model Context Protocol. It provides seamless access to web crawling, semantic search, and relationship-based retrieval.

### What It Does

1. **Web Crawling**
   - Intelligent content extraction via Crawl4AI
   - Markdown formatting with structure preservation
   - Deep crawling with configurable depth and limits
   - Single or batch URL operations
   - Performance: 2-10 seconds per page

2. **Semantic Search**
   - Fast vector similarity via SQLite + sqlite-vec
   - Optional KG-enhanced hybrid search
   - Multi-signal ranking (5 signals)
   - Tag-based filtering and organization
   - Performance: 100-500ms (vector), 500-2000ms (KG)

3. **Knowledge Graph Integration**
   - Optional Neo4j for relationship discovery
   - Entity expansion via knowledge graph
   - Relationship-based search refinement
   - Graceful degradation if KG unavailable
   - Performance: Additional 100-500ms for KG ops

4. **Database Modes**
   - **RAM Mode**: 10-50x faster with in-memory operations
   - **Disk Mode**: Full persistence with SQLite
   - Automatic synchronization between modes
   - Configurable for different workloads

## Key Features

### MCP Integration

- **JSON-RPC 2.0 Protocol**: Over stdio for AI assistant integration
- **Tool-based API**: Crawl, search, memory management as tools
- **Status Endpoints**: Health checks and statistics
- **Error Handling**: Graceful fallbacks and detailed error messages

### Performance & Reliability

- **RAM Database Mode**: 10-50x faster queries with differential sync
- **Async Processing**: Non-blocking operations throughout
- **Graceful Degradation**: Works without KG if unavailable
- **Auto-cleanup**: Session management with 24-hour timeout
- **Domain Blocking**: Wildcard-based URL filtering for security

### Data Management

- **3 Retention Policies**: Permanent, session-only, 30-day
- **Tag Organization**: Flexible content categorization
- **Chunk Management**: Automatic text splitting and embedding
- **Bidirectional Links**: SQLite ↔ Neo4j integration

## System Architecture

```
AI Assistant (Claude/LM-Studio)
    ↓ MCP (JSON-RPC 2.0)
┌─────────────────────────────────┐
│ robaitragmcp (MCP Server)       │
│ ├─ Web Crawling Tools           │
│ ├─ Search Tools                 │
│ ├─ Memory Management            │
│ └─ Graph Tools                  │
└────────────┬────────────────────┘
             │
   ┌─────────┼─────────┐
   ↓         ↓         ↓
Crawl4AI  SQLite+    Neo4j
(11235)   sqlite-vec (7687)
(content) (vectors)  (graph)
```

## Components

### Core Modules

**rag_processor.py**: Main MCP server entry point
- Handles JSON-RPC communication
- Tool registration and execution
- Error handling and logging

**core/**: RAG pipeline implementation
- Crawlers and scrapers
- Vector operations
- Search handlers
- Graph integration

**models/**: Data structures
- Request/response models
- Entity and relationship models
- Search result models

### Storage

**SQLite Database**:
- Content storage with metadata
- Vector embeddings (sqlite-vec)
- Session management
- Full-text search indexes

**Neo4j Graph** (optional):
- Entity nodes with metadata
- Relationship edges with types
- Document hierarchy
- Full-text search capability

## Statistics

- **Total Lines**: ~3,500 lines of Python code
- **Core Modules**: 12+ main modules
- **MCP Tools**: 15+ tools available to AI assistants
- **Response Times**: 100ms-10s depending on operation
- **Database**: SQLite (required) + Neo4j (optional)
- **Memory Efficiency**: 10-50x faster with RAM mode

## Quick Start

### Docker Deployment (Recommended)

```bash
cd robaitragmcp
cp .env.example .env
docker compose up -d
```

### Local Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install torch --index-url https://download.pytorch.org/whl/cpu
python3 core/rag_processor.py
```

### Integration with Claude Desktop

```json
{
  "mcpServers": {
    "robai-rag": {
      "command": "/path/to/.venv/bin/python3",
      "args": ["/path/to/robaitragmcp/core/rag_processor.py"],
      "env": {
        "CRAWL4AI_URL": "http://localhost:11235",
        "KG_SERVICE_URL": "http://localhost:8088",
        "USE_MEMORY_DB": "true"
      }
    }
  }
}
```

## Use Cases

**AI-Powered Research**:
- Crawl documentation and build knowledge base
- Search across crawled content with semantic understanding
- Discover relationships between concepts
- Answer questions with cited sources

**Knowledge Management**:
- Build searchable document libraries
- Organize content with tags and retention policies
- Track where information appears in documents
- Power chatbots with current knowledge

**Integration Points**:
- Claude Desktop integration for AI workflows
- LM-Studio integration for local models
- Backend for robairagapi REST bridge
- Feeds into robaimodeltools RAG pipeline

## Next Steps

- [Getting Started](getting-started.html) - Installation and setup
- [Configuration](configuration.html) - Environment configuration
- [API Reference](api-reference.html) - MCP tools and usage
- [Architecture](architecture.html) - System design and patterns
