---
layout: default
title: Configuration
parent: robaimodeltools
nav_order: 2
---

# Configuration

Comprehensive configuration guide for robaimodeltools.

## Environment Variables

### Database Configuration

```bash
# Database File Path
DB_PATH=/path/to/database/rag_database.db

# Database Mode
USE_MEMORY_DB=true              # Enable RAM mode with differential sync
                                # false = traditional disk-based operation

# Sync Configuration (RAM mode only)
SYNC_IDLE_SECONDS=5            # Idle time before sync (default: 5)
SYNC_PERIODIC_MINUTES=5         # Max time between syncs (default: 5)
```

### Service Endpoints

```bash
# Crawl4AI Service
CRAWL4AI_URL=http://localhost:11235

# Knowledge Graph Service
KG_SERVICE_URL=http://kg-service:8088

# Neo4j Database (used by KG Service)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

### Model Configuration

```bash
# SentenceTransformer Model (embeddings)
SENTENCE_TRANSFORMER_MODEL=all-MiniLM-L6-v2

# GLiNER Model (entity extraction)
GLINER_MODEL=urchade/gliner_small-v2.1

# Model Cache Directory
HF_HOME=~/.cache/huggingface/
```

## Configuration Modes

### Disk-Only Mode

Traditional file-based database operation.

```bash
USE_MEMORY_DB=false
DB_PATH=/data/rag_database.db
```

**Best For:**
- Smaller deployments
- Persistent-only workloads
- Limited RAM availability

### RAM Mode with Differential Sync

In-memory database with automatic syncing to disk.

```bash
USE_MEMORY_DB=true
DB_PATH=/data/rag_database.db
SYNC_IDLE_SECONDS=5
SYNC_PERIODIC_MINUTES=5
```

**Best For:**
- High-throughput production deployments
- Fast read/write operations
- Dual trigger strategy: idle (5s) + periodic (5m)

**Sync Strategy:**
- Only changed records synchronized (not entire DB)
- Trigger-based change tracking
- Automatic recovery on restart

## Database Schema

### Core Tables

```sql
-- Content storage
crawled_content (url, title, content, markdown, hash, session_id, retention_policy, tags, metadata)

-- Vector embeddings (virtual table)
content_vectors (embedding float[384])

-- Content chunks
content_chunks (chunk_id, content_rowid, chunk_index, start_pos, end_pos, vector_rowid)

-- Extracted entities
chunk_entities (entity_id, chunk_id, entity_text, entity_type, confidence)

-- Relationships
chunk_relationships (rel_id, chunk_id, subject, predicate, object, confidence)

-- KG processing queue
kg_processing_queue (queue_id, content_rowid, status, created_at, error_message)

-- Sessions
sessions (session_id, created_at)

-- Domain blocking
blocked_domains (pattern, added_at)
```

## Retention Policies

### Available Policies

| Policy | Behavior | Use Case |
|--------|----------|----------|
| `permanent` | Never expires | Knowledge base content |
| `session_only` | Deleted on session end (24h) | Temporary research |
| `30_days` | Auto-deleted after 30 days | Time-sensitive content |

### Setting Retention Policy

```python
# During crawl
crawler.crawl_and_store(
    url="https://example.com",
    retention_policy="permanent"
)

# Query by retention policy
content = GLOBAL_DB.list_memory(retention_policy="permanent")
```

## Chunking Configuration

### Default Settings

```python
# Character-based chunking
CHUNK_SIZE = 1000              # Characters per chunk
CHUNK_OVERLAP = 0              # No overlap (simple stepping)

# Quality filtering
MIN_CHUNK_SIZE = 50            # Minimum characters
MAX_NAVIGATION_DENSITY = 0.4   # Max 40% navigation lines
MAX_LINK_RATIO = 0.3           # Max link-to-word ratio
```

### Custom Chunking

```python
from robaimodeltools.data.storage import RAGDatabase

db = RAGDatabase(chunk_size=1500)  # Custom chunk size
```

## Search Configuration

### Vector Search Weights

```python
# Production weights for multi-signal ranking
VECTOR_WEIGHT = 0.35      # 35% vector similarity
GRAPH_WEIGHT = 0.25       # 25% graph relevance
BM25_WEIGHT = 0.20        # 20% BM25 text matching
RECENCY_WEIGHT = 0.10     # 10% document recency
TITLE_WEIGHT = 0.10       # 10% title matching
```

### Entity Extraction

```python
# GLiNER configuration
ENTITY_CONFIDENCE_THRESHOLD = 0.1    # High recall
ENTITY_TYPES = 119                   # From entities.yaml
```

## Advanced Configuration

### Sync Manager

```python
from robaimodeltools.data.sync_manager import SyncManager

sync_manager = SyncManager(
    memory_db=memory_conn,
    disk_db_path="/path/to/disk.db",
    idle_seconds=5,
    periodic_minutes=5
)

# Get sync metrics
metrics = sync_manager.get_metrics()
```

### Content Cleaner

```python
from robaimodeltools.data.content_cleaner import ContentCleaner

cleaner = ContentCleaner()

# Clean content
cleaned = cleaner.clean_content(raw_content)

# Get quality metrics
metrics = cleaner.get_cleaning_metrics(cleaned)
```

### Search Handler

```python
from robaimodeltools.search.search_handler import SearchHandler

handler = SearchHandler(
    db=GLOBAL_DB,
    kg_service_url="http://kg-service:8088",
    vector_weight=0.35,
    graph_weight=0.25,
    bm25_weight=0.20,
    recency_weight=0.10,
    title_weight=0.10
)
```

## Performance Tuning

### Database Optimization

```bash
# RAM mode for performance
USE_MEMORY_DB=true

# Adjust sync intervals
SYNC_IDLE_SECONDS=10        # Less frequent sync
SYNC_PERIODIC_MINUTES=10     # Higher throughput
```

### Crawling Performance

```python
# Concurrent operations
max_depth=2                  # Limit depth
max_pages=50                 # Limit pages
rate_limit=0.5              # Seconds between requests
```

### Search Performance

```python
# Fast vector-only search
results = crawler.search_knowledge(query, top_k=10)

# Slower but more comprehensive
response = search_handler.search(query, top_k=10)
```

## Security Configuration

### SQL Injection Prevention

Built-in validation layers (no configuration needed):
- Whitelist-based validation
- SQL keyword detection
- NULL byte filtering
- Length enforcement

### URL Validation

Built-in security (no configuration needed):
- Blocks localhost, private IPs
- Blocks cloud metadata endpoints
- Blocks .local, .internal, .corp domains

### Domain Blocking

```python
# Add patterns
crawler.add_blocked_domain("*.malicious.com")
crawler.add_blocked_domain("*spam*")
```

## Logging

```python
import logging

# Set log level
logging.basicConfig(level=logging.INFO)

# Component-specific logging
logger = logging.getLogger("robaimodeltools")
logger.setLevel(logging.DEBUG)
```

## Configuration Best Practices

1. **Use RAM mode for production** - Better performance with minimal risk
2. **Configure retention policies appropriately** - Balance storage with data freshness
3. **Monitor sync metrics** - Ensure differential sync is working correctly
4. **Adjust chunk size based on content** - Larger chunks for technical docs
5. **Tune search weights** - Based on your specific use case
6. **Enable domain blocking** - Proactive security measure

## Next Steps

- [Architecture](architecture.html) - Understand the system design
- [API Reference](api-reference.html) - Complete API documentation
- [Getting Started](getting-started.html) - Basic usage examples
