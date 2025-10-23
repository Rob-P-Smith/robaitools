---
layout: default
title: Getting Started
parent: robaikg
nav_order: 1
---

# Getting Started with robaikg

Complete installation and setup guide for the Knowledge Graph Extraction and Management Service.

## Prerequisites

Before installing robaikg, ensure you have:

- **Python 3.11+** installed
- **Docker** running (for Neo4j)
- **GPU** (optional, but recommended for GLiNER - CPU mode supported)
- **vLLM backend** running on port 8078 (for relationship extraction)
- **At least 8GB RAM** (4GB Neo4j, 2GB GLiNER, 2GB kg-service)

## Installation

### Step 1: Navigate to Directory

```bash
cd /path/to/robaitools/robaikg
```

### Step 2: Install Dependencies

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python packages
pip install -r requirements.txt
```

**Key Dependencies**:
- FastAPI 0.115+ - Web framework
- neo4j 5.13+ - Graph database driver
- torch - Deep learning framework (CPU or GPU)
- transformers - Hugging Face models
- pydantic - Data validation
- httpx - Async HTTP client
- python-dotenv - Environment configuration

### Step 3: Configure Environment

Create a `.env` file with your configuration:

```bash
# Copy the example configuration
cp .env.example .env

# Edit with your settings
nano .env
```

**Minimum Required Configuration**:

```bash
# Service Configuration
SERVICE_NAME=kg-service
API_HOST=0.0.0.0
API_PORT=8088
DEBUG=false
LOG_LEVEL=INFO

# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=knowledge_graph_2024
NEO4J_DATABASE=neo4j

# vLLM Configuration (for relationship extraction)
VLLM_BASE_URL=http://localhost:8078
VLLM_TIMEOUT=1800

# GLiNER Configuration (entity extraction)
GLINER_MODEL=urchade/gliner_large-v2.1
GLINER_THRESHOLD=0.45
```

See [Configuration](configuration.html) for all available options.

### Step 4: Start Neo4j Database

**Docker Deployment** (Recommended):

```bash
# Start Neo4j with docker-compose
cd /path/to/robaitools/robaikg
docker compose up -d neo4j
```

**Verify Neo4j is running**:

```bash
# Check container status
docker ps | grep neo4j

# Access Neo4j Browser
open http://localhost:7474

# Login with username: neo4j, password: knowledge_graph_2024
```

**Local Installation** (Advanced):

If running Neo4j locally without Docker:
- Download from [neo4j.com](https://neo4j.com/download/)
- Configure BOLT protocol on port 7687
- Set `NEO4J_URI=bolt://localhost:7687` in .env

### Step 5: Verify Dependencies

Ensure all dependent services are running:

```bash
# Check vLLM is running
curl http://localhost:8078/v1/models

# Check Neo4j is running
curl http://localhost:7474

# Test Neo4j connection
python3 -c "from neo4j import AsyncDriver; print('Neo4j driver available')"
```

Expected containers:
- `neo4j-kg` - Neo4j graph database

### Step 6: Start kg-service

**Development Mode** (with auto-reload):

```bash
python3 kg-service/main.py
```

The service will start on `http://localhost:8088`

**Production Mode** (with Uvicorn):

```bash
uvicorn kg-service.main:app --host 0.0.0.0 --port 8088 --workers 4
```

**Background Mode**:

```bash
nohup python3 kg-service/main.py > kg-service.log 2>&1 &
```

### Step 7: Verify Installation

Check that the service is running and healthy:

```bash
# Health check
curl http://localhost:8088/health

# Service statistics
curl http://localhost:8088/stats

# Model information
curl http://localhost:8088/api/v1/model-info
```

Expected health response:

```json
{
  "status": "healthy",
  "service": "kg-service",
  "version": "1.0.0",
  "services": {
    "neo4j": "connected",
    "vllm": "available",
    "gliner": "loaded"
  }
}
```

## Basic Usage

### Using Python

#### 1. Install Client Library

```bash
# Use the included client or curl
pip install httpx
```

#### 2. Extract Entities from Document

```python
import httpx
import json

async def extract_entities():
    client = httpx.AsyncClient()

    document = {
        "content_id": 1,
        "url": "https://example.com/page",
        "title": "Example Documentation",
        "markdown": """# FastAPI Documentation

FastAPI is a modern web framework for building APIs using Python.
It uses Pydantic for data validation and Uvicorn as ASGI server.
FastAPI is built on top of Starlette for the web components.
""",
        "chunks": [
            {
                "vector_rowid": 45001,
                "chunk_index": 0,
                "char_start": 0,
                "char_end": 250,
                "text": "# FastAPI Documentation\n\nFastAPI is a modern web framework..."
            }
        ]
    }

    response = await client.post(
        "http://localhost:8088/api/v1/ingest",
        json=document
    )

    result = response.json()
    print(f"Extracted {result['entities_extracted']} entities")
    print(f"Extracted {result['relationships_extracted']} relationships")

    for entity in result['entities'][:3]:
        print(f"- {entity['text']} ({entity['type_primary']})")

# Run async function
import asyncio
asyncio.run(extract_entities())
```

#### 3. Search Entities

```python
import httpx

async def search_entities():
    client = httpx.AsyncClient()

    response = await client.post(
        "http://localhost:8088/api/v1/search/entities",
        json={
            "entity_terms": ["FastAPI", "Python"],
            "limit": 10
        }
    )

    entities = response.json()['entities']
    for entity in entities:
        print(f"{entity['text']}: {entity['mention_count']} mentions")

asyncio.run(search_entities())
```

#### 4. Expand Related Entities

```python
import httpx

async def expand_entities():
    client = httpx.AsyncClient()

    response = await client.post(
        "http://localhost:8088/api/v1/expand/entities",
        json={
            "entity_names": ["FastAPI"],
            "max_expansions": 5,
            "expansion_depth": 1
        }
    )

    expanded = response.json()['expanded_entities']
    print(f"Found {len(expanded)} related entities:")
    for entity in expanded:
        print(f"- {entity['text']} ({entity['relationship_type']})")

asyncio.run(expand_entities())
```

### Using cURL

#### Extract Entities

```bash
curl -X POST http://localhost:8088/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "content_id": 1,
    "url": "https://example.com/page",
    "title": "Example",
    "markdown": "FastAPI is a web framework using Pydantic and Uvicorn.",
    "chunks": [{
      "vector_rowid": 45001,
      "chunk_index": 0,
      "char_start": 0,
      "char_end": 60,
      "text": "FastAPI is a web framework using Pydantic and Uvicorn."
    }]
  }'
```

#### Search Entities

```bash
curl -X POST http://localhost:8088/api/v1/search/entities \
  -H "Content-Type: application/json" \
  -d '{
    "entity_terms": ["FastAPI"],
    "limit": 10
  }'
```

#### Expand Entities

```bash
curl -X POST http://localhost:8088/api/v1/expand/entities \
  -H "Content-Type: application/json" \
  -d '{
    "entity_names": ["FastAPI"],
    "max_expansions": 5
  }'
```

## Understanding Entity Types

robaikg extracts **300+ entity types** organized hierarchically. Some common examples:

### Technology Entities

```
Framework::Backend::Python
- Framework (primary)
- Backend (sub1)
- Python (sub2)

Library::Validation::Python
- Library (primary)
- Validation (sub1)
- Python (sub2)
```

### Common Entity Types

- **Framework**: Backend, Frontend, Full-Stack, Web
- **Library**: Validation, ORM, Testing, Async
- **Language**: Python, JavaScript, Java, Go
- **Database**: SQL, NoSQL, Graph, Cache
- **Tool**: Build, Deploy, Monitor, Test
- **Concept**: Pattern, Algorithm, Protocol, Standard
- **Organization**: Company, Team, Project, Community
- **Person**: Developer, Author, Contributor, Maintainer
- **Location**: City, Region, Country, Continent

## Understanding Relationships

robaikg extracts **50+ relationship types**:

### Common Relationship Types

**Technical**:
- `uses` - Entity A uses Entity B
- `depends_on` - Requires or depends on
- `implements` - Implements or provides
- `extends` - Extends or inherits from
- `integrates_with` - Integrates or compatible with

**Comparative**:
- `competes_with` - Competes in same space
- `similar_to` - Similar functionality or purpose
- `different_from` - Different approach or paradigm
- `alternative_to` - Alternative option

**Hierarchical**:
- `part_of` - Component of larger system
- `contains` - Contains or includes
- `belongs_to` - Belongs to category
- `located_in` - Geographical location

**Temporal**:
- `precedes` - Comes before in time
- `follows` - Comes after in time
- `replaces` - Replacement for
- `updates` - Updated version of

## Database Concepts

### Entity Extraction Pipeline

```
Raw Document (Markdown)
        ↓
[Tokenize & Chunk]
        ↓
[GLiNER Model Inference]
        ↓
[Confidence Filtering]
        ↓
[Deduplication]
        ↓
[Neo4j Storage]
```

**Performance**: 2-3 seconds per document

### Relationship Extraction Pipeline

```
Document + Extracted Entities
        ↓
[Build Prompt]
        ↓
[vLLM Inference]
        ↓
[JSON Parsing]
        ↓
[Validation]
        ↓
[Neo4j Storage]
```

**Performance**: 5-10 seconds per document

### Neo4j Graph Structure

The knowledge graph stores:

**Nodes**:
- `Document` - Crawled/ingested documents
- `Chunk` - Text chunks with vector indices
- `Entity` - Extracted named entities

**Relationships**:
- `Document -[:HAS_CHUNK]-> Chunk`
- `Entity -[:MENTIONED_IN {offset}]-> Chunk`
- `Entity -[:USES|DEPENDS_ON|...]-> Entity` (semantic)
- `Entity -[:CO_OCCURS_WITH]-> Entity` (co-occurrence)

## Testing Your Installation

### Test 1: Health Check

```bash
curl http://localhost:8088/health | jq
```

Should return status "healthy" with all services connected.

### Test 2: Extract Entities

```bash
# Test entity extraction with sample document
curl -X POST http://localhost:8088/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d @- <<'EOF'
{
  "content_id": 1,
  "url": "https://test.example.com",
  "title": "Test Document",
  "markdown": "Python is a programming language. FastAPI is a web framework. Pydantic provides data validation.",
  "chunks": [{
    "vector_rowid": 1,
    "chunk_index": 0,
    "char_start": 0,
    "char_end": 120,
    "text": "Python is a programming language. FastAPI is a web framework. Pydantic provides data validation."
  }]
}
EOF
```

Expected output: Extracted entities with types and confidence scores.

### Test 3: Search and Expand

```bash
# Search for extracted entities
curl -X POST http://localhost:8088/api/v1/search/entities \
  -H "Content-Type: application/json" \
  -d '{"entity_terms": ["FastAPI"], "limit": 5}'

# Expand related entities
curl -X POST http://localhost:8088/api/v1/expand/entities \
  -H "Content-Type: application/json" \
  -d '{"entity_names": ["FastAPI"], "max_expansions": 5}'
```

## Neo4j Browser Exploration

Access the Neo4j Browser at [http://localhost:7474](http://localhost:7474)

### Useful Queries

**Count all entities**:

```cypher
MATCH (e:Entity) RETURN count(e) as total_entities
```

**Find top entities by mentions**:

```cypher
MATCH (e:Entity)
RETURN e.text, e.type_primary, e.mention_count
ORDER BY e.mention_count DESC
LIMIT 20
```

**Explore entity relationships**:

```cypher
MATCH (e1:Entity {text: "FastAPI"})-[r]->(e2:Entity)
RETURN e1.text, type(r), e2.text, r.confidence
ORDER BY r.confidence DESC
```

**Find documents by entity**:

```cypher
MATCH (e:Entity {text: "Python"})-[:MENTIONED_IN]->(c:Chunk)-[:PART_OF]->(d:Document)
RETURN DISTINCT d.title, d.url
LIMIT 10
```

## Troubleshooting

### Service Won't Start

**Problem**: `uvicorn` or `python` fails to start

**Solutions**:
1. Check Neo4j is running:
   ```bash
   docker ps | grep neo4j
   ```

2. Verify port 8088 is not in use:
   ```bash
   lsof -i :8088
   ```

3. Check configuration:
   ```bash
   cat .env
   ```

4. View detailed logs:
   ```bash
   python3 -c "from kg-service.main import app; print('Module loaded')"
   ```

### Health Check Shows "unhealthy"

**Problem**: `/health` endpoint shows degraded status

**Solutions**:
1. Verify Neo4j connection:
   ```bash
   docker exec neo4j-kg cypher-shell -u neo4j -p knowledge_graph_2024 "RETURN 1"
   ```

2. Check vLLM is running:
   ```bash
   curl http://localhost:8078/v1/models
   ```

3. Verify Neo4j credentials:
   ```bash
   grep NEO4J .env
   ```

### Entity Extraction Slow

**Problem**: Processing takes more than 10 seconds

**Possible causes**:
- Large documents (>10,000 chars)
- Low confidence threshold (many entities to extract)
- CPU bottleneck (GLiNER is CPU-intensive)

**Solutions**:
- Increase `GLINER_THRESHOLD` in .env (0.45 → 0.6)
- Reduce `CHUNK_SIZE` (2000 → 1000)
- Add more CPU cores if using container

### Relationship Extraction Failing

**Problem**: No relationships extracted, only entities

**Solutions**:
1. Verify vLLM is running:
   ```bash
   curl http://localhost:8078/v1/models
   ```

2. Check vLLM model is loaded:
   ```bash
   curl http://localhost:8078/v1/models | jq
   ```

3. Increase vLLM timeout in .env:
   ```bash
   VLLM_TIMEOUT=3600  # 1 hour
   ```

4. Check logs:
   ```bash
   tail -f kg-service.log
   ```

### "Connection refused" Errors

**Problem**: Cannot connect to Neo4j or vLLM

**Solutions**:
1. Verify services are running:
   ```bash
   docker ps
   ```

2. Check firewall:
   ```bash
   # Test Neo4j connection
   nc -zv localhost 7687

   # Test vLLM connection
   nc -zv localhost 8078
   ```

3. Update .env URLs if services on different hosts:
   ```bash
   NEO4J_URI=bolt://neo4j-host:7687
   VLLM_BASE_URL=http://vllm-host:8078
   ```

## Integration with RAG Pipeline

robaikg integrates with the larger RobAI RAG system:

1. **Content Source**: robaicrawler crawls URLs
2. **Storage**: robaimodeltools stores in SQLite
3. **Processing**: robaidata queues documents for KG extraction
4. **KG Extraction**: **robaikg** (this service) extracts entities/relationships
5. **Graph Storage**: Neo4j stores the knowledge graph
6. **Search**: robaitragmcp uses KG for hybrid search
7. **REST API**: robairagapi exposes KG operations

## Performance Tips

### 1. Tune GLiNER Threshold

For **more entities** (higher recall):
```bash
GLINER_THRESHOLD=0.3
```

For **fewer entities** (higher precision):
```bash
GLINER_THRESHOLD=0.6
```

### 2. Tune Relationship Confidence

For **more relationships**:
```bash
RELATION_MIN_CONFIDENCE=0.3
```

For **fewer relationships**:
```bash
RELATION_MIN_CONFIDENCE=0.7
```

### 3. Neo4j Memory Configuration

For large graphs, increase Neo4j memory:

```bash
# Edit docker-compose.yml or .env
NEO4J_HEAP_INITIAL_SIZE=4G
NEO4J_HEAP_MAX_SIZE=16G
NEO4J_PAGECACHE_SIZE=4G
```

### 4. Parallel Processing

Process multiple documents concurrently via robaidata workers:

```bash
KG_NUM_WORKERS=4  # Number of parallel workers
```

## Next Steps

- [Configuration](configuration.html) - Detailed configuration options
- [API Reference](api-reference.html) - Complete API documentation
- [Architecture](architecture.html) - Understanding the system design
- [KG_WORKFLOW_DOCUMENTATION.md](../KG_WORKFLOW_DOCUMENTATION.html) - Complete workflow guide
