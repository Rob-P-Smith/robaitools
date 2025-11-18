---
layout: default
title: Architecture
parent: robaitragmcp
nav_order: 4
---

# Architecture

System design and architecture of robaitragmcp MCP Server.

## System Overview

```
┌─────────────────────────────────────────────────────┐
│         Claude Desktop / LM-Studio / API            │
│          (MCP Client via stdio/HTTP)                │
└────────────────────┬────────────────────────────────┘
                     │ JSON-RPC 2.0
┌────────────────────▼────────────────────────────────┐
│           MCP Server (robaitragmcp)                │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │         MCP Tools (15+ operations)         │    │
│  │ ├─ crawl_url (Crawl4AI)                   │    │
│  │ ├─ search (Full-text)                    │    │
│  │ ├─ vector_search (Semantic)              │    │
│  │ ├─ Content management (CRUD)             │    │
│  │ └─ Tag management                        │    │
│  └────────────────────────────────────────────┘    │
│                     ↓                                │
│  ┌────────────────────────────────────────────┐    │
│  │      Processing & Pipeline Manager        │    │
│  │ ├─ Crawl4AI client (web extraction)      │    │
│  │ ├─ Embedding generator (vector search)   │    │
│  │ └─ Neo4j connector (optional KG)         │    │
│  └────────────────────────────────────────────┘    │
│                     ↓                                │
│  ┌────────────────────────────────────────────┐    │
│  │        Database Layer (Storage)            │    │
│  │ ├─ SQLite (disk/RAM mode)                 │    │
│  │ ├─ sqlite-vec (vector indexing)           │    │
│  │ └─ Full-text search (FTS5)                │    │
│  └────────────────────────────────────────────┘    │
│                                                      │
└──────────────────────────────────────────────────────┘
```

## Core Components

### 1. MCP Server (server.py)

**Purpose**: JSON-RPC 2.0 protocol handler for AI assistants

**Key Features**:
- Stdio-based communication (Claude Desktop)
- HTTP endpoint support (LM-Studio)
- Tool definition and routing
- Request validation
- Error handling

**Lifecycle**:
```
Initialize
  ↓
Load tools
  ↓
Connect database
  ↓
Listen for JSON-RPC requests
  ↓
Route to appropriate tool
  ↓
Execute and return result
  ↓
On shutdown: Close database connections
```

### 2. Database Manager (database.py)

**Purpose**: SQLite storage with dual-mode operation

**Dual Modes**:

**Disk Mode**:
- SQLite database file on disk
- Full persistence
- Survives process restart
- Automatic backups

**RAM Mode**:
- In-memory SQLite
- 10-50x faster
- Differential sync to disk
- Lost on restart (without sync)

**Key Operations**:
- Store crawled content with metadata
- Index for full-text search (FTS5)
- Manage embeddings (sqlite-vec)
- Handle tags and sessions
- Automatic retention policy enforcement

### 3. Crawl4AI Client (crawl4ai_client.py)

**Purpose**: Web content extraction interface

**Integration**:
- HTTP client to Crawl4AI service
- Async/await for non-blocking I/O
- Timeout handling
- Error recovery
- Content cleaning and markdown conversion

**Process**:
```
URL → [Crawl4AI Service] → HTML
                           ↓
                    [Clean & Parse]
                           ↓
                    [Convert to Markdown]
                           ↓
                    [Extract Metadata]
                           ↓
                    Return (title, content, metadata)
```

### 4. Embedding Generator (embeddings.py)

**Purpose**: Generate vector embeddings for semantic search

**Model**: all-MiniLM-L6-v2 (384-dimensional vectors)

**Process**:
```
Text Input
   ↓
[Chunk text if > max_length]
   ↓
[Generate embeddings via transformer]
   ↓
[Store in sqlite-vec]
   ↓
[Enable vector similarity search]
```

**Features**:
- Lazy loading (first use)
- Efficient batch processing
- Vector similarity search
- Distance-based ranking

### 5. Neo4j Connector (neo4j_connector.py)

**Purpose**: Optional knowledge graph integration

**Features** (when enabled):
- Entity extraction from crawled content
- Relationship mapping
- Graph-based search
- Semantic expansion

**Connection Pool**:
- Async Neo4j driver
- Connection pooling
- Graceful error handling

### 6. Tool Implementations (tools/)

**Tool Categories**:

**Web Operations** (crawl_url):
- Extract page content
- Wait for dynamic elements
- Handle authentication
- Parse and clean HTML

**Search** (search, vector_search):
- Full-text search via FTS5
- Semantic similarity via embeddings
- Tag filtering
- Result ranking

**Memory** (get_memory, update_memory, delete_memory):
- CRUD operations on stored content
- Metadata management
- Retention policy enforcement

**Tags** (create_tag, list_tags):
- Hierarchical tagging
- Content organization
- Filtering support

**Admin** (export_content, clear_memory):
- Data export (markdown, JSON, HTML)
- Bulk operations
- Database cleanup

## Data Flow

### Content Ingestion

```
1. User requests: crawl_url("https://example.com")
   ↓
2. MCP Server routes to crawl_url tool
   ↓
3. Crawl4AI Client extracts content
   {url, title, content, metadata}
   ↓
4. Database Manager stores:
   - Full content (content table)
   - Chunks (for vector search)
   - Metadata (tags, timestamps)
   ↓
5. Embedding Generator creates vectors
   ↓
6. sqlite-vec indexes embeddings
   ↓
7. Return success response
```

### Search Operations

```
User Query: "asyncio patterns"
   ↓
Full-Text Search:
  SELECT * FROM content_fts
  WHERE content MATCH "asyncio patterns"
  LIMIT 5
   ↓
Vector Search (parallel):
  [Generate embedding for query]
   ↓
  SELECT * FROM embeddings
  WHERE distance < threshold
  ORDER BY distance
  LIMIT 5
   ↓
Merge and rank results
   ↓
Return combined results
```

### Memory Management

**Retention Policy Enforcement**:
```
Every hour:
  IF retention_policy = "session":
    DELETE content WHERE session_id != current_session
      AND age > session_timeout

  IF retention_policy = "30day":
    DELETE content WHERE age > 30 days

  IF retention_policy = "permanent":
    Do nothing (manual deletion only)
```

**Session Tracking**:
- Session ID assigned on startup
- Auto-cleanup on timeout
- Configurable timeout (default: 24 hours)

## Design Patterns

### 1. Tool Factory Pattern

Register tools dynamically:

```python
@tool
def crawl_url(url: str, timeout: int = 30):
    """Extract web content"""
    return crawl4ai_client.extract(url, timeout)

# Tools registered automatically
```

### 2. Async/Await Throughout

All I/O operations non-blocking:

```python
async def search(query: str):
    # Parallel searches
    fulltext = await db.full_text_search(query)
    semantic = await embeddings.vector_search(query)
    return merge_results(fulltext, semantic)
```

### 3. Graceful Degradation

Service continues if optional components fail:

```python
try:
    kg_results = await neo4j.expand_entities(entities)
except Neo4jConnectionError:
    kg_results = []  # Continue without KG
```

### 4. Configuration Injection

Central config accessed throughout:

```python
class Database:
    def __init__(self, config: Config):
        self.mode = config.database_mode
        self.path = config.database_path
        self.max_size = config.max_ram_size
```

## Performance Characteristics

| Operation | Time | Mode | Notes |
|-----------|------|------|-------|
| crawl_url | 2-10s | Both | Depends on page size |
| search (FTS) | <100ms | Both | Indexed search |
| vector_search | 100-500ms | Both | Embedding + similarity |
| store content | 10-100ms | Disk | Write I/O |
| store content | <1ms | RAM | In-memory |
| startup | 1-5s | Both | Load config, init DB |

**Scalability**:
- RAM mode: Limited by available memory
- Disk mode: Unlimited growth (I/O limited)
- Concurrent requests: Limited by CPU cores
- Vector search: O(n) similarity computation

## Security Architecture

### Input Validation

1. **URL Validation**: Must start with http(s)
2. **Query Length**: Max 10,000 characters
3. **Rate Limiting**: Per-session per-tool limits
4. **Database Injection**: Parameterized queries only

### Data Protection

1. **Session Isolation**: Content scoped to sessions
2. **Retention Policies**: Auto-cleanup options
3. **Field Encryption**: Optional for sensitive data
4. **Access Control**: Future: per-tool permissions

### API Security

1. **Stdio-based (Claude)**: No network exposure
2. **HTTP Endpoint**: Localhost only (configure firewall)
3. **Error Messages**: Non-revealing to client
4. **Logging**: Sensitive data redacted

## Integration Points

### With Claude Desktop

```
Claude → stdio → MCP Server → Tools → Database
```

### With LM-Studio

```
LM-Studio → HTTP → MCP Server → Tools → Database
```

### With Anthropic API

```
Application → MCP Client → robaitragmcp → Tools
```

### With Neo4j (Optional)

```
robaitragmcp ←→ Neo4j
  - Extract entities from crawled content
  - Graph-based search
  - Relationship discovery
```

## Deployment Architectures

### Single Process (Default)

```
[Claude Desktop]
       ↓
  [MCP Server + Tools + DB]
       ↓
  [SQLite (disk/RAM)]
```

### Standalone Server

```
[LM-Studio]
       ↓
[HTTP Client]
       ↓
[MCP Server + Tools + DB]
       ↓
[SQLite (shared disk)]
```

### Distributed (Future)

```
[Multiple Claude instances]
           ↓
[Load Balancer]
           ↓
[MCP Server Pool]
           ↓
[Shared Database (SQLite + replication)]
```

## Future Enhancements

- Horizontal scaling with shared database
- GraphQL API layer
- Caching layer (Redis)
- Advanced retention policies
- Plugin system for custom tools
- Kubernetes deployment

## Next Steps

- [Getting Started](getting-started.html) - Installation and setup
- [Configuration](configuration.html) - Environment variables
- [API Reference](api-reference.html) - Complete tool documentation
