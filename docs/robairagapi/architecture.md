---
layout: default
title: Architecture
parent: robairagapi
nav_order: 4
---

# Architecture

System design and architecture of robairagapi.

## System Overview

robairagapi is a lightweight FastAPI-based REST API bridge that provides HTTP/JSON access to robaimodeltools' RAG system. Direct Python imports eliminate external MCP overhead while maintaining clean separation of concerns.

```
External Clients (HTTP)
    ↓
┌─────────────────────────────────────────┐
│  robairagapi (FastAPI Bridge)           │
│  ├─ HTTP Endpoints (23 endpoints)       │
│  ├─ Authentication & Rate Limiting      │
│  ├─ Input Validation (5 layers)         │
│  └─ Response Formatting                 │
└────────────┬────────────────────────────┘
             │ Direct Python Imports
             ↓
┌─────────────────────────────────────────┐
│  robaimodeltools (RAG Core)             │
│  ├─ Crawl4AIRAG (crawler)               │
│  ├─ SearchHandler (KG search)           │
│  ├─ GLOBAL_DB (storage layer)           │
│  └─ Domain Management                   │
└────────────┬────────────────────────────┘
             │
             ├──→ Crawl4AI (11235)
             ├──→ SQLite Database
             ├──→ KG Service (8088)
             └──→ Neo4j Graph DB (7687)
```

## Core Components

### 1. server.py (525 lines)

**Purpose**: Main FastAPI application with REST endpoints.

**Key Responsibilities**:
- HTTP request/response handling
- REST endpoint definitions
- Response formatting
- Exception handling

**Endpoint Categories**:
```python
# Health & Status (2)
GET /health
GET /api/v1/status

# Crawling (4)
POST /api/v1/crawl
POST /api/v1/crawl/store
POST /api/v1/crawl/temp
POST /api/v1/crawl/deep/store

# Search (3)
POST /api/v1/search
POST /api/v1/search/kg
POST /api/v1/search/enhanced

# Memory (3)
GET /api/v1/memory
DELETE /api/v1/memory
DELETE /api/v1/memory/temp

# Statistics (1)
GET /api/v1/stats

# Domain Management (3)
GET /api/v1/blocked-domains
POST /api/v1/blocked-domains
DELETE /api/v1/blocked-domains

# Help (1)
GET /api/v1/help
```

### 2. models.py (170 lines)

**Purpose**: Pydantic request/response models with validation.

**Key Models**:

```python
class CrawlRequest:
    url: str  # Required, validated

class CrawlStoreRequest:
    url: str  # Required
    tags: Optional[str]
    retention_policy: str  # permanent|session_only|30_days

class SearchRequest:
    query: str  # Required, max 500 chars
    limit: int  # 1-1000
    tags: Optional[str]

class SearchKGRequest:
    query: str
    rag_limit: int  # 1-100
    kg_limit: int   # 1-100
    tags: Optional[str]
    enable_expansion: bool
    include_context: bool

class DeepCrawlRequest:
    url: str
    max_depth: int          # 1-5
    max_pages: int          # 1-250
    include_external: bool
    score_threshold: float
    timeout: int            # 60-1800
    tags: Optional[str]
    retention_policy: str

class BlockedDomainRequest:
    pattern: str
    description: Optional[str]

class CrawlResponse:
    success: bool
    data: Dict
    timestamp: str

class SearchResponse:
    success: bool
    data: Dict
    timestamp: str
```

### 3. auth.py (198 lines)

**Purpose**: Authentication and rate limiting.

**Key Functions**:

```python
class RateLimiter:
    - check_rate_limit(api_key: str) -> bool
    - get_current_api_key(request: Request) -> str

def verify_api_key(request: Request) -> str:
    # Extract and validate Bearer token
    # Public endpoints: /health, /help
    # Other endpoints: require valid key

class SessionManager:
    - create_session(api_key: str) -> str
    - get_session(api_key: str) -> Session
    - cleanup_expired()  # Auto cleanup
```

**Rate Limiting**:
- Per API key sliding window
- Default: 60 requests/minute
- Configurable via env var
- Response: 429 (Too Many Requests)

**Session Management**:
- 24-hour session timeout
- SHA256-based session IDs
- Auto-cleanup every hour
- Tracks per-key metrics

### 4. validation.py (221 lines)

**Purpose**: Input validation (5-layer defense).

**Layer 1 - Pydantic Models**:
- Type checking
- Required vs optional
- Length limits (255-500 chars)
- Range validation

**Layer 2 - URL Validation**:
```python
def validate_url(url: str):
    # Protocol: HTTP/HTTPS only
    # No localhost (127.0.0.1, ::1)
    # No private IPs (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
    # No link-local (169.254.0.0/16)
    # No cloud metadata (169.254.169.254, 100.100.100.200)
    # No .local, .internal, .corp
```

**Layer 3 - SQL Injection Prevention**:
- Multi-layer SQL keyword detection
- NULL byte filtering
- Context-aware detection

**Layer 4 - Operation Validation**:
- Business logic in robaimodeltools
- Database integrity checks
- Service availability

**Layer 5 - Response Validation**:
- HTTP status verification
- JSON serialization
- Timestamp presence
- Success flag accuracy

## Request/Response Flow

### Crawl Request Flow

```
HTTP Request (POST /api/v1/crawl/store)
    ↓
FastAPI Endpoint Handler
    ├─ Parse JSON body
    ├─ Pydantic validation (Layer 1)
    └─ Extract API key
    ↓
Authentication Middleware
    ├─ Verify Bearer token
    └─ Check rate limit
    ↓
Crawl Operation
    ├─ Validate URL (Layer 2)
    ├─ Call robaimodeltools.Crawl4AIRAG
    ├─ Extract content
    ├─ Create embeddings
    └─ Store in SQLite
    ↓
Response Formatting
    ├─ Create response dict
    ├─ Add timestamp
    └─ JSON serialization
    ↓
HTTP Response (200 + JSON)
```

### Search Request Flow

```
HTTP Request (POST /api/v1/search)
    ↓
Authentication & Rate Limit Check
    ↓
Search Operation Selection
    ├─ /search → Simple vector search
    ├─ /search/kg → Hybrid search
    └─ /search/enhanced → Full 5-phase
    ↓
Execute Search
    ├─ robaimodeltools.SearchHandler
    ├─ Vector similarity
    ├─ Optional: KG expansion
    └─ Optional: 5-phase pipeline
    ↓
Result Aggregation
    ├─ Rank results
    ├─ Format responses
    └─ Add metadata
    ↓
HTTP Response (200 + JSON)
```

## Data Models

### Content Storage

```python
{
    "content_id": int,          # SQLite row ID
    "url": str,                 # Original URL
    "title": str,               # Extracted title
    "content": str,             # Plain text
    "markdown": str,            # Markdown formatted
    "word_count": int,          # Content size
    "chunk_count": int,         # Split chunks
    "session_id": Optional[str], # Session ID
    "retention_policy": str,    # Retention type
    "tags": List[str],          # Tag list
    "created_at": datetime,     # Creation time
    "updated_at": datetime      # Last update
}
```

### Search Result

```python
{
    "content_id": int,
    "url": str,
    "title": str,
    "chunk_text": str,
    "similarity_score": float,  # 0-1
    "tags": List[str],
    "chunk_index": int
}
```

### KG Entity

```python
{
    "entity": str,
    "type": str,
    "context": str,
    "confidence": float,        # 0-1
    "referenced_chunks": List[int]
}
```

## Design Patterns

### 1. Dependency Injection Pattern

```python
@app.post("/api/v1/crawl/store")
async def crawl_and_store(
    request: CrawlStoreRequest,
    api_key: str = Depends(verify_api_key)
):
    # API key injected from authentication middleware
```

### 2. Response Wrapper Pattern

```python
def create_response(data: Dict, timestamp: str = None):
    return {
        "success": True,
        "data": data,
        "timestamp": timestamp or datetime.utcnow().isoformat()
    }
```

### 3. Exception Handling Pattern

```python
@app.exception_handler(ValueError)
async def handle_validation_error(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )
```

### 4. Async/Await Pattern

```python
@app.post("/api/v1/crawl/deep/store")
async def deep_crawl_store(request: DeepCrawlRequest):
    # Run in thread pool for blocking operations
    result = await asyncio.get_event_loop().run_in_executor(
        None,
        crawler.deep_crawl,
        request.url
    )
```

### 5. Middleware Pattern

```python
@app.middleware("http")
async def add_process_time_header(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

## Security Architecture

### Authentication

**Bearer Token**:
```
Authorization: Bearer YOUR_API_KEY
```

**Validation**:
- Extract token from header
- Check against configured keys
- Support up to 2 keys (rotation)

**Public Endpoints**:
- `/health` - Public
- `/api/v1/help` - Public
- All others - Require auth

### Rate Limiting

**Mechanism**:
- In-memory rate limiter
- Per-API-key sliding window
- 60-second window (default)
- Configurable via env var

**Response**:
```json
{
  "detail": "Rate limit exceeded. Try again later."
}
```

### Input Validation

**5-Layer Defense**:
1. Pydantic schema validation
2. URL security checks
3. SQL injection prevention
4. Business logic validation
5. Response format validation

### CORS Security

```python
@app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,  # Configurable
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

## Performance Characteristics

### Response Times (typical)

| Endpoint | Time | Factors |
|----------|------|---------|
| `/health` | 1ms | Simple response |
| `/api/v1/status` | 5ms | Config check |
| `/api/v1/crawl` | 2-10s | Page size, network |
| `/api/v1/search` | 100-500ms | Database size |
| `/api/v1/search/kg` | 500-2000ms | KG connectivity |
| `/api/v1/search/enhanced` | 1-3s | Full pipeline |
| `/api/v1/crawl/deep/store` | 30-300s | Depth, page count |

### Throughput

- **Rate Limit**: 60 req/min/key (default)
- **Workers**: Configurable (1+ via gunicorn)
- **Bottleneck**: Backend services (Crawl4AI, Neo4j)

### Resource Usage

- **Memory**: 100-300MB
- **CPU**: Low at idle, scales with requests
- **Disk**: Database size dependent
- **Network**: Crawl4AI, KG service access

## Deployment Architecture

### Single Instance

```
Client → robairagapi:8080 → robaimodeltools → SQLite
```

### Docker Container

```dockerfile
FROM python:3.11-slim
# ~50MB final image
# Non-root user
# Health checks
```

### Behind Reverse Proxy

```
Client → nginx:80 (TLS) → robairagapi:8080 (localhost)
```

### Scaled Deployment

```
Load Balancer → robairagapi:8080 (multiple instances)
                    ↓
            Shared SQLite Database
                    ↓
            Crawl4AI, KG Service
```

## Service Dependencies

### Required
- **Crawl4AI** (port 11235): Web crawling
- **SQLite**: Content storage

### Optional
- **KG Service** (port 8088): Knowledge graph
- **Neo4j** (port 7687): Graph database

### Graceful Degradation
- KG unavailable: Simple search still works
- Crawl4AI unavailable: Crawling fails gracefully

## Monitoring & Observability

### Logging

**Levels**: DEBUG, INFO, WARNING, ERROR

**Format**: `timestamp - name - level - message`

**Key Events**:
- Server startup/shutdown
- API requests (POST, GET)
- Authentication failures
- Crawl successes/failures
- Database errors

### Health Checks

```bash
# Check service
curl http://localhost:8080/health

# Check detailed status
curl -H "Authorization: Bearer KEY" \
  http://localhost:8080/api/v1/status
```

### Metrics

**Available via `/api/v1/stats`**:
- Total content stored
- Database size
- Retention policy breakdown
- Content age range
- KG processing status

## Configuration Management

### Environment Variables

```bash
LOCAL_API_KEY=...           # Authentication
REMOTE_API_KEY_2=...        # Backup key
SERVER_HOST=0.0.0.0        # Binding address
SERVER_PORT=8080            # Port
RATE_LIMIT_PER_MINUTE=60   # Limit
ENABLE_RATE_LIMIT=true     # Enable/disable
CORS_ORIGINS=*             # CORS config
LOG_LEVEL=INFO             # Logging
```

### Validation

- Required: At least one API key
- Optional: All others use defaults
- Startup: Validates configuration

## Scalability Considerations

### Current Limitations

- Single-instance only (no distributed queue)
- SQLite for storage (not suitable for extreme scale)
- No load balancing built-in

### Scaling Recommendations

**Vertical Scaling**:
- Increase workers: `gunicorn --workers 4`
- More RAM: Larger database cache
- Better CPU: Faster request processing

**Horizontal Scaling**:
- Multiple instances behind load balancer
- Shared SQLite on NFS (not ideal)
- Consider: PostgreSQL for production scale

**Database Scaling**:
- SQLite: ~GB scale (single instance)
- PostgreSQL: Multi-instance, better scaling
- Consider: Dedicated RAG database

## Next Steps

- [API Reference](api-reference.html) - Complete endpoint documentation
- [Configuration](configuration.html) - Configuration options
- [Getting Started](getting-started.html) - Installation and usage
