---
layout: default
title: Getting Started
parent: robaimodeltools
nav_order: 1
---

# Getting Started with robaimodeltools

This guide will help you get started with robaimodeltools, the core RAG library for the robaitools ecosystem.

## Installation

### Prerequisites

- Python 3.9+
- SQLite3 with `sqlite-vec` extension
- Access to Crawl4AI service (default: `http://localhost:11235`)
- Access to KG service (default: `http://kg-service:8088`)

### Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# Install PyTorch (CPU version)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### Verify SQLite-vec Extension

```python
import sqlite3
import sqlite_vec

conn = sqlite3.connect(":memory:")
conn.enable_load_extension(True)
sqlite_vec.load(conn)

# Test vector extension
print(conn.execute("SELECT vec_version()").fetchone())
```

## Configuration

Create a `.env` file or set environment variables:

```bash
# Database Configuration
DB_PATH=/path/to/database/rag_database.db
USE_MEMORY_DB=true                    # Enable RAM mode with differential sync

# Service Endpoints
CRAWL4AI_URL=http://localhost:11235   # Crawl4AI service
KG_SERVICE_URL=http://kg-service:8088 # Knowledge graph service

# Model Configuration (optional, uses defaults if not set)
SENTENCE_TRANSFORMER_MODEL=all-MiniLM-L6-v2
GLINER_MODEL=urchade/gliner_small-v2.1
```

## Basic Usage

### Initialize the RAG System

```python
from robaimodeltools.operations.crawler import Crawl4AIRAG

# Initialize with default configuration
crawler = Crawl4AIRAG()
```

### Simple Search

```python
# Vector similarity search
results = crawler.search_knowledge(
    query="How to use FastAPI with SQLAlchemy?",
    top_k=10,
    tags="python"
)

print(f"Found {len(results)} results")
for result in results:
    print(f"- {result['title']} ({result['similarity']:.2f})")
    print(f"  {result['url']}")
```

### Crawl and Store Content

```python
# Crawl a single URL
result = crawler.crawl_and_store(
    url="https://example.com/article",
    retention_policy="permanent",
    tags="python,tutorial"
)

print(f"Stored: {result['url']}")
print(f"Chunks created: {result['chunk_count']}")
```

### Deep Crawl

```python
# Crawl multiple pages from a domain
session_id = crawler.deep_crawl_and_store(
    starting_url="https://fastapi.tiangolo.com",
    max_depth=2,
    max_pages=20,
    retention_policy="permanent",
    tags="fastapi,documentation"
)

# Check progress
status = crawler.get_crawl_status(session_id)
print(f"Progress: {status['pages_crawled']} / {status['max_pages']}")
print(f"Stored: {status['pages_stored']}")
```

### Advanced Search with KG Enhancement

```python
from robaimodeltools.search.search_handler import SearchHandler
from robaimodeltools.data.storage import GLOBAL_DB
import os

# Initialize search handler
handler = SearchHandler(
    db=GLOBAL_DB,
    kg_service_url=os.getenv("KG_SERVICE_URL"),
    crawl4ai_url=os.getenv("CRAWL4AI_URL")
)

# Full 5-phase pipeline search
response = handler.search(
    query="FastAPI microservices architecture",
    top_k=10
)

# Inspect results
print(f"Query: {response['query']['original']}")
print(f"Entities: {response['query']['entities']}")
print(f"Expanded entities: {response['exploration']['discovered_entities']}")

for result in response['results']:
    print(f"\n{result['rank']}. {result['title']}")
    print(f"   Score: {result['score']:.2f}")
    print(f"   Breakdown: {result['score_breakdown']}")
```

## Common Operations

### Database Statistics

```python
# Get comprehensive stats
stats = crawler.get_database_stats()

print(f"Total records: {stats['total_records']}")
print(f"Unique domains: {stats['unique_domains']}")
print(f"Database size: {stats['database_size_mb']} MB")
```

### Domain Management

```python
# Block domains
crawler.add_blocked_domain("*.spam.com")
crawler.add_blocked_domain("*malicious*")

# List blocked domains
blocked = crawler.list_blocked_domains()
print(f"Blocked domains: {len(blocked)}")

# Remove block (requires authorization)
crawler.remove_blocked_domain("*.spam.com")
```

### Memory Management

```python
# List stored content
content = GLOBAL_DB.list_memory(retention_policy="permanent", limit=50)
for item in content:
    print(f"{item['title']} - {item['word_count']} words")

# Delete specific content
GLOBAL_DB.forget("https://example.com/old-article")

# Clear temporary content
GLOBAL_DB.clear_temp_content()
```

## Next Steps

- [Architecture](architecture.html) - Learn about the system architecture
- [API Reference](api-reference.html) - Explore all available methods
- [Configuration](configuration.html) - Advanced configuration options

## Troubleshooting

### Common Issues

**SQLite-vec Extension Not Found:**
```bash
# Install sqlite-vec
pip install sqlite-vec
```

**Model Download Failures:**
```python
# Models are downloaded automatically on first use
# Ensure internet connection for initial download
# Models cached in ~/.cache/huggingface/
```

**Crawl4AI Service Connection:**
```bash
# Verify Crawl4AI is running
curl http://localhost:11235/health

# Check logs
docker logs crawl4ai
```

**KG Service Connection:**
```bash
# Verify KG service is running
curl http://kg-service:8088/health

# Check Neo4j connection
docker logs kg-service
```

## Examples

For more comprehensive examples, see the [main README](https://github.com/yourusername/robaitools/tree/main/robaimodeltools) in the repository.
