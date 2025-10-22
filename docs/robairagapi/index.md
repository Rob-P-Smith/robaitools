---
layout: default
title: robairagapi
nav_order: 6
has_children: true
---

# robairagapi

**Lightweight FastAPI REST API Bridge for RobAI RAG System**

A production-ready REST API (~50MB Docker image) that provides HTTP/JSON access to the RobAI Retrieval-Augmented Generation (RAG) system through a clean RESTful interface.

## Overview

robairagapi is a lightweight FastAPI-based REST API that bridges HTTP clients to the RobAI RAG infrastructure. Unlike traditional MCP-based bridges, it uses direct Python imports from [robaimodeltools](../robaimodeltools) for minimal overhead and maximum performance.

### What It Does

- **Web Crawling**: Extract and store content from URLs (single or deep crawl)
- **Semantic Search**: Vector similarity search with optional knowledge graph enhancement
- **Memory Management**: Store, retrieve, and organize crawled content
- **Domain Blocking**: Pattern-based URL blocking for security
- **Knowledge Graph Integration**: Entity extraction and relationship-based search

### What Makes It Different

- **Lightweight**: ~50MB Docker image vs ~600MB for full stack alternatives
- **Direct Integration**: No external MCP dependency, uses robaimodeltools directly
- **Multi-Layer Security**: 5-layer validation with defense-in-depth architecture
- **Production-Ready**: Bearer token auth, rate limiting, session management
- **OpenAPI Compatible**: Auto-generated Swagger docs at `/docs`

## Key Features

### API Capabilities

- **23 REST Endpoints** across 6 categories
- **3 Search Modes**: Simple (vector), KG-enhanced (hybrid), Full pipeline (5-phase)
- **3 Retention Policies**: Permanent, session-only, 30-day
- **Bearer Token Authentication** with rate limiting (60 req/min default)
- **Session Management**: 24-hour sessions with auto-cleanup
- **CORS Support**: Configurable cross-origin requests

### Search Features

- **Simple Search**: Fast vector similarity (100-500ms)
- **KG Search**: Hybrid vector + knowledge graph (500-2000ms)
- **Enhanced Search**: Full 5-phase pipeline with entity expansion (1-3s)
- **Tag Filtering**: Organize and filter by custom tags
- **Entity Extraction**: GLiNER-based entity recognition
- **Multi-Signal Ranking**: 5 signals (similarity, connectivity, density, recency, tags)

### Security Features

- **URL Validation**: Blocks localhost, private IPs, cloud metadata endpoints
- **SQL Injection Prevention**: Multi-layer SQL keyword detection
- **Rate Limiting**: Configurable per-API-key sliding window
- **Input Sanitization**: Length limits, range validation, type checking
- **Domain Blocking**: Wildcard pattern matching for malicious domains

## Quick Start

### Installation

```bash
cd robairagapi

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Add API keys

# Start the service
python main.py
```

### Basic Usage

**Health Check:**
```bash
curl http://localhost:8080/health
```

**Crawl and Store:**
```bash
curl -X POST http://localhost:8080/api/v1/crawl/store \
  -H "Authorization: Bearer YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "tags": "example"}'
```

**Search:**
```bash
curl -X POST http://localhost:8080/api/v1/search \
  -H "Authorization: Bearer YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "your search query", "limit": 10}'
```

**API Documentation:**
```
http://localhost:8080/docs
```

## System Architecture

```
External Clients (OpenWebUI, curl, scripts)
    ↓ HTTP REST (port 8080)
┌─────────────────────────────────────────┐
│  robairagapi (FastAPI Bridge)           │
│  ├─ Authentication & Rate Limiting      │
│  ├─ Input Validation (5 layers)         │
│  ├─ REST Endpoints (23 endpoints)       │
│  └─ Response Formatting                 │
└────────────┬────────────────────────────┘
             │ Direct Python Imports
             ↓
┌─────────────────────────────────────────┐
│  robaimodeltools (Shared Library)       │
│  ├─ Crawl4AIRAG (crawler)               │
│  ├─ SearchHandler (KG search)           │
│  ├─ GLOBAL_DB (storage)                 │
│  └─ Domain Management                   │
└────────────┬────────────────────────────┘
             │
             ├──→ Crawl4AI (port 11235)
             ├──→ SQLite Database
             ├──→ KG Service (port 8088)
             └──→ Neo4j Graph DB (port 7687)
```

## API Endpoints

### Endpoint Categories

**Health & Status** (2 endpoints)
- `GET /health` - Health check
- `GET /api/v1/status` - Detailed system status

**Crawling** (4 endpoints)
- `POST /api/v1/crawl` - Crawl without storing
- `POST /api/v1/crawl/store` - Crawl and store permanently
- `POST /api/v1/crawl/temp` - Crawl and store temporarily
- `POST /api/v1/crawl/deep/store` - Deep crawl multiple pages

**Search** (3 endpoints)
- `POST /api/v1/search` - Simple vector search
- `POST /api/v1/search/kg` - Hybrid vector + graph search
- `POST /api/v1/search/enhanced` - Full 5-phase pipeline

**Memory Management** (3 endpoints)
- `GET /api/v1/memory` - List stored content
- `DELETE /api/v1/memory` - Remove specific URL
- `DELETE /api/v1/memory/temp` - Clear temporary content

**Statistics** (1 endpoint)
- `GET /api/v1/stats` - Database statistics

**Domain Management** (3 endpoints)
- `GET /api/v1/blocked-domains` - List blocked domains
- `POST /api/v1/blocked-domains` - Add domain block
- `DELETE /api/v1/blocked-domains` - Remove domain block

**Help** (1 endpoint)
- `GET /api/v1/help` - Tool documentation

## Search Modes Comparison

| Feature | Simple | KG Search | Enhanced |
|---------|--------|-----------|----------|
| **Speed** | ~100-500ms | ~500-2000ms | ~1-3s |
| **Vector Search** | ✓ | ✓ | ✓ |
| **Knowledge Graph** | ✗ | ✓ | ✓ |
| **Entity Expansion** | ✗ | Optional | Always |
| **Full Markdown** | ✗ | ✗ | ✓ |
| **Multi-Signal Ranking** | ✗ | ✓ | ✓ (5 signals) |
| **Configurable Limits** | ✓ | ✓ | ✗ (fixed) |
| **Best For** | Quick lookups | Research | Deep analysis |

## Security Architecture

### 5-Layer Validation

1. **Layer 1 - Pydantic Models**: Type validation, required fields, length limits
2. **Layer 2 - URL Validation**: Blocks localhost, private IPs, metadata endpoints
3. **Layer 3 - SQL Injection Prevention**: Multi-layer keyword detection
4. **Layer 4 - Operation Validation**: Business logic in robaimodeltools
5. **Layer 5 - Response Validation**: HTTP status, JSON serialization

### Authentication

- **Bearer Token**: Required for all endpoints except `/health` and `/help`
- **Multiple Keys**: Supports up to 2 API keys for rotation
- **Rate Limiting**: 60 requests/minute per key (configurable)

## Docker Deployment

**Build Image:**
```bash
docker build -t robairagapi:latest -f robairagapi/Dockerfile .
```

**Run Container:**
```bash
docker run -d \
  --name robairagapi \
  --network host \
  -e LOCAL_API_KEY=your-secret-key \
  robairagapi:latest
```

**Check Status:**
```bash
docker logs -f robairagapi
curl http://localhost:8080/health
```

## Performance Characteristics

### Response Times (Typical)

| Endpoint | Time | Notes |
|----------|------|-------|
| `/health` | 1ms | Simple response |
| `/api/v1/crawl` | 2-10s | Depends on page size |
| `/api/v1/search` | 100-500ms | Vector similarity |
| `/api/v1/search/kg` | 500-2000ms | Includes graph query |
| `/api/v1/search/enhanced` | 1-3s | Full 5-phase pipeline |
| `/api/v1/crawl/deep/store` | 30-300s | Depends on max_pages |

### Resource Usage

- **Docker Image**: ~50MB
- **RAM Usage**: 100-300MB (with database loaded)
- **Rate Limit**: 60 requests/minute/key (default)
- **Concurrent Connections**: Limited by Uvicorn workers

## Statistics

- **Total Lines**: ~1,200 lines of application code
- **API Endpoints**: 23 across 6 categories
- **Public Endpoints**: 2 (/health, /help)
- **Authenticated Endpoints**: 21
- **Python Dependencies**: 7 direct packages
- **Required Services**: 2 (Crawl4AI, SQLite)
- **Optional Services**: 2 (KG Service, Neo4j)

## Integration Examples

### Python with requests

```python
import requests

url = "http://localhost:8080/api/v1/crawl/store"
headers = {
    "Authorization": "Bearer your-api-key",
    "Content-Type": "application/json"
}
data = {
    "url": "https://example.com/article",
    "tags": "python,tutorial",
    "retention_policy": "permanent"
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

### OpenWebUI Integration

**Configuration:**
- Base URL: `http://your-server:8080`
- Auth Type: Bearer Token
- API Key: `your-api-key-here`
- Name: RobAI RAG API

**Supported Operations:**
- Crawl URLs
- Store and search content
- View stored content
- Manage blocked domains

## Next Steps

- [Getting Started](getting-started.html) - Installation and basic usage
- [Configuration](configuration.html) - Configuration options and environment variables
- [API Reference](api-reference.html) - Complete API documentation
- [Architecture](architecture.html) - Detailed architecture and design patterns
