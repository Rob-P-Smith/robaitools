---
layout: default
title: Architecture
parent: robairagapi
nav_order: 3
---

# Architecture

Deep dive into robairagapi's internal design and how it works.

## System Overview

robairagapi is a **FastAPI REST API bridge** that provides HTTP access to robaimodeltools RAG system via **direct Python imports**. Unlike robaitragmcp (which uses MCP protocol), robairagapi imports robaimodeltools as a standard Python library, eliminating protocol overhead.

```
External Clients (HTTP)
    ↓
┌────────────────────────────────────────────────────┐
│  Security Middleware (Layer 1)                     │
│  ├─ IP+MAC Validation                              │
│  ├─ pfSense Integration (strict mode)              │
│  ├─ LAN Trust (relaxed mode)                       │
│  └─ Attack Detection (path traversal, method       │
│     override, protocol downgrade)                  │
└────────────────────┬───────────────────────────────┘
                     ↓
┌────────────────────────────────────────────────────┐
│  robairagapi (Port 8081)                           │
│  ├─ FastAPI Application (641 lines)                │
│  ├─ Authentication & Rate Limiting                 │
│  ├─ 17 REST Endpoints                              │
│  ├─ Request Validation (Pydantic)                  │
│  └─ Response Formatting                            │
└────────────────────┬───────────────────────────────┘
                     │ Direct Python Import:
                     │ from robaimodeltools.operations.crawler import Crawl4AIRAG
                     ↓
┌────────────────────────────────────────────────────┐
│  robaimodeltools (Shared Library)                  │
│  ├─ Crawl4AIRAG (crawler operations)               │
│  ├─ SearchHandler (5-phase pipeline)               │
│  ├─ EnhancedSearchOrchestrator (optimized)         │
│  ├─ GLOBAL_DB (storage layer)                      │
│  └─ Domain Management                              │
└──────────┬─────────────────────────────────────────┘
           │
           ├──→ Crawl4AI (11235) - Web crawling
           ├──→ SQLite Database - Vector storage
           ├──→ KG Service (8088) - Entity extraction
           └──→ Neo4j (7687) - Graph database
```

## Key Architectural Decision: Direct Import

**Why direct imports instead of MCP?**

robaitragmcp uses MCP protocol (JSON-RPC over TCP) for AI assistant integration. robairagapi uses direct Python imports for simpler HTTP-to-RAG bridging.

**Comparison**:

```python
# robaitragmcp approach (MCP)
tcp_connection → JSON-RPC → Tool Discovery → Function Call → robaimodeltools
# Overhead: Protocol parsing, tool wrapping, TCP communication

# robairagapi approach (Direct)
HTTP request → FastAPI → Direct import → robaimodeltools
# Overhead: HTTP only (much simpler)
```

**Benefits of direct import**:
- **Simpler**: No protocol layer, standard Python calls
- **Faster**: ~10-20ms less overhead per request
- **Easier debugging**: Standard Python stack traces
- **No discovery needed**: Just import and call

**When to use each**:
- **robaitragmcp**: AI assistants (Claude Desktop, LM-Studio)
- **robairagapi**: HTTP clients (web apps, curl, Python requests)

## Core Components

### 1. api/server.py (641 lines)

**Purpose**: Main FastAPI application with 17 REST endpoints.

**Initialization**:
```python
# Direct import at module level
from robaimodeltools.operations.crawler import Crawl4AIRAG
from robaimodeltools.data.storage import GLOBAL_DB

# Create single instance (shared across requests)
crawl4ai_url = os.getenv("CRAWL4AI_URL", "http://localhost:11235")
rag_system = Crawl4AIRAG(crawl4ai_url=crawl4ai_url)
```

**Application factory**:
```python
def create_app() -> FastAPI:
    app = FastAPI(
        title="RobAI RAG API",
        description="REST API for RAG operations (crawling, search, KG)",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # Security middleware FIRST (before CORS)
    app.middleware("http")(security_middleware)

    # CORS middleware
    app.add_middleware(CORSMiddleware, ...)

    # Process time middleware
    @app.middleware("http")
    async def add_process_time_header(request, call_next):
        # Adds X-Process-Time header

    # Endpoints defined via decorators
    @app.post("/api/v1/crawl/store")
    async def crawl_and_store(...)

    return app
```

**Endpoint categories** (17 total):

**Health & Status** (2):
- GET `/health` - Quick health check (no auth)
- GET `/api/v1/status` - Detailed status (requires auth)

**Crawling** (4):
- POST `/api/v1/crawl` - Crawl without storing
- POST `/api/v1/crawl/store` - Crawl and store permanently
- POST `/api/v1/crawl/temp` - Crawl and store temporarily
- POST `/api/v1/crawl/deep/store` - Deep crawl multiple pages

**Search** (3):
- POST `/api/v1/search` - Simple vector similarity
- POST `/api/v1/search/kg` - Full 5-phase KG pipeline
- POST `/api/v1/search/enhanced` - Optimized search (focused results)

**Memory Management** (3):
- GET `/api/v1/memory` - List stored content
- DELETE `/api/v1/memory` - Forget specific URL
- DELETE `/api/v1/memory/temp` - Clear all temporary content

**Statistics** (2):
- GET `/api/v1/stats` - Database statistics
- GET `/api/v1/db/stats` - Alias for stats

**Domain Management** (3):
- GET `/api/v1/blocked-domains` - List blocked patterns
- POST `/api/v1/blocked-domains` - Add blocked pattern
- DELETE `/api/v1/blocked-domains` - Remove blocked pattern

**Help** (1):
- GET `/api/v1/help` - Tool list and documentation

**OpenAPI schema customization**:
```python
def custom_openapi():
    # Simplifies anyOf patterns for Cline compatibility
    # Cleans up numeric constraints (1000.0 → 1000)
```

### 2. api/models.py (172 lines)

**Purpose**: Pydantic request/response models with automatic validation.

**Key models**:

**Crawl requests**:
```python
class CrawlRequest(BaseModel):
    url: str  # Required, validated via @validator

    @validator('url')
    def validate_url_field(cls, v):
        if not validate_url(v):
            raise ValueError('Invalid or unsafe URL provided')
        return v

class CrawlStoreRequest(CrawlRequest):
    tags: Optional[str] = ""
    retention_policy: Optional[str] = "permanent"

    @validator('tags')
    def validate_tags(cls, v):
        return validate_string_length(v or "", 255, "tags")

class DeepCrawlStoreRequest(DeepCrawlRequest):
    url: str
    max_depth: Optional[int] = Field(2, ge=1, le=5)
    max_pages: Optional[int] = Field(10, ge=1, le=250)
    include_external: Optional[bool] = False
    score_threshold: Optional[float] = Field(0.0, ge=0.0, le=1.0)
    timeout: Optional[int] = Field(None, ge=60, le=1800)
    tags: Optional[str] = ""
    retention_policy: Optional[str] = "permanent"
```

**Search requests**:
```python
class SearchRequest(BaseModel):
    query: str  # Required, max 500 chars
    limit: Optional[int] = Field(2, ge=1, le=4)
    tags: Optional[str] = None

class KGSearchRequest(BaseModel):
    query: str
    rag_limit: Optional[int] = Field(1, ge=1, le=5)
    kg_limit: Optional[int] = Field(3, ge=1, le=10)
    tags: Optional[str] = None
    enable_expansion: Optional[bool] = True
    include_context: Optional[bool] = True

class EnhancedSearchRequest(BaseModel):
    query: str
    rag_limit: Optional[int] = Field(1, ge=1, le=5)
    kg_limit: Optional[int] = Field(10, ge=1, le=20)
    tags: Optional[str] = None
```

**Response models**:
```python
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    mcp_connected: bool  # Always True (legacy field)
    version: str

class StatusResponse(BaseModel):
    api_status: str
    mcp_status: str  # Always "direct" (not using MCP)
    timestamp: str
    components: dict
```

**Validation flow**:
1. Pydantic schema validation (automatic)
2. Custom @validator functions (explicit)
3. Field constraints (ge, le, minLength, maxLength)
4. Type coercion (str → int, etc.)

### 3. api/auth.py (246 lines)

**Purpose**: Authentication, rate limiting, session management.

**RateLimiter class** (60 req/min default):
```python
class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)  # {api_key: [timestamps]}
        self.max_requests = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
        self.enabled = os.getenv("ENABLE_RATE_LIMIT", "true").lower() == "true"

    def is_allowed(self, api_key: str) -> bool:
        # Sliding 60-second window
        now = time.time()
        minute_ago = now - 60

        # Remove old requests
        self.requests[api_key] = [
            req_time for req_time in self.requests[api_key]
            if req_time > minute_ago
        ]

        # Check limit
        if len(self.requests[api_key]) >= self.max_requests:
            return False

        # Record this request
        self.requests[api_key].append(now)
        return True
```

**SessionManager class** (24-hour timeout):
```python
class SessionManager:
    def __init__(self):
        self.sessions = {}  # {session_id: session_data}
        self.session_timeout = timedelta(hours=24)

    def create_session(self, api_key: str) -> str:
        session_id = hashlib.sha256(f"{api_key}{time.time()}".encode()).hexdigest()[:16]
        self.sessions[session_id] = {
            "api_key": api_key,
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
            "requests_count": 0
        }
        return session_id

    def cleanup_expired_sessions(self):
        # Called every hour via background task
        now = datetime.now()
        expired = [
            sid for sid, session in self.sessions.items()
            if now - session["last_activity"] > self.session_timeout
        ]
        for sid in expired:
            del self.sessions[sid]
```

**verify_api_key function**:
```python
def verify_api_key(credentials: HTTPAuthorizationCredentials) -> Dict[str, Any]:
    # Get token from Bearer header
    token = credentials.credentials

    # Normalize (handle whitespace, case)
    token = normalize_bearer_token(f"Bearer {token}")

    # Load valid keys from environment
    valid_keys = [
        os.getenv("OPENAI_API_KEY"),
        os.getenv("OPENAI_API_KEY_2"),
    ]
    valid_keys = [key.strip() for key in valid_keys if key]

    # Verify token
    if token not in valid_keys:
        # Return 404 (not 401/403) for security by obscurity
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not Found"
        )

    # Check rate limit
    if not rate_limiter.is_allowed(token):
        # Also return 404 on rate limit (hide endpoint existence)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not Found"
        )

    # Create session
    session_id = session_manager.create_session(token)

    return {
        "api_key": token,
        "session_id": session_id,
        "authenticated": True,
        "timestamp": datetime.now().isoformat()
    }
```

**Security by obscurity**:
- Invalid API key → 404 (not 401 "Unauthorized")
- Rate limit exceeded → 404 (not 429 "Too Many Requests")
- Hides endpoint existence from attackers

### 4. api/security.py (281 lines)

**Purpose**: Advanced security middleware with IP+MAC validation and attack detection.

**Two security modes**:

**STRICT MODE** (pfSense proxy requests):
- IP+MAC validation required
- Blocks path traversal attempts
- Blocks method override attempts
- Blocks protocol downgrade attempts
- Blocks suspicious headers
- Single Authorization header required

**RELAXED MODE** (trusted LAN requests):
- IP validation only (MAC optional)
- Allows from trusted subnet (192.168.10.0/24)
- Basic security checks
- More permissive for internal tools

**SecurityValidator class**:
```python
class SecurityValidator:
    def __init__(self):
        self.pfsense_ip = Config.PFSENSE_IP
        self.pfsense_mac = Config.PFSENSE_MAC
        self.trusted_subnet = Config.TRUSTED_LAN_SUBNET
        self.strict_mode_enabled = Config.STRICT_AUTH_FOR_PFSENSE
        self.mac_validation_enabled = Config.ENABLE_MAC_VALIDATION

    def validate_ip_and_mac(self, request: Request):
        client_ip = self.get_client_ip(request)  # Check X-Forwarded-For first

        # Get MAC if validation enabled
        mac_address = None
        if self.mac_validation_enabled:
            mac_address = get_mac_address_from_ip(client_ip)

        # Check if pfSense request
        is_pfsense = False
        if client_ip == self.pfsense_ip:
            if self.mac_validation_enabled:
                if mac_address.lower() == self.pfsense_mac.lower():
                    is_pfsense = True
                else:
                    # SECURITY ALERT: IP match but MAC mismatch (spoofing?)
                    raise HTTPException(403, "Access denied: Invalid network identity")
            else:
                is_pfsense = True  # MAC validation disabled

        return client_ip, mac_address, is_pfsense
```

**Security checks**:

**Authorization header security**:
```python
def check_authorization_header_security(self, request, is_strict):
    auth_headers = request.headers.getlist("Authorization")

    if is_strict:
        # Must have exactly 1 Authorization header
        if len(auth_headers) == 0:
            raise HTTPException(404, "Not Found")  # Hide endpoint
        if len(auth_headers) > 1:
            raise HTTPException(404, "Not Found")  # Multiple headers = attack

        # Check for suspicious headers
        suspicious = [
            "X-Authorization", "X-Forwarded-Authorization",
            "X-Original-Authorization", "X-Auth", "Proxy-Authorization"
        ]
        for header in suspicious:
            if request.headers.get(header):
                raise HTTPException(404, "Not Found")
```

**Path security**:
```python
def check_path_security(self, request, is_strict):
    path = request.url.path

    if is_strict:
        # Check path traversal
        if ".." in path:
            raise HTTPException(404, "Not Found")

        # Check encoded attacks
        encoded_patterns = ["%2e%2e", "%2f", "%5c", "%00"]
        for pattern in encoded_patterns:
            if pattern in path.lower():
                raise HTTPException(404, "Not Found")
```

**Method override check**:
```python
def check_method_override(self, request, is_strict):
    if is_strict:
        override_headers = [
            "X-HTTP-Method-Override",
            "X-Method-Override",
            "X-HTTP-Method"
        ]
        for header in override_headers:
            if request.headers.get(header):
                raise HTTPException(404, "Not Found")
```

**Protocol downgrade check**:
```python
def check_protocol_downgrade(self, request, is_strict):
    if is_strict:
        if request.headers.get("Upgrade"):
            # Block WebSocket upgrade attempts
            raise HTTPException(404, "Not Found")
```

**Main validation flow**:
```python
async def validate_request(self, request: Request):
    # Validate IP and MAC
    client_ip, mac_address, is_pfsense = self.validate_ip_and_mac(request)

    # Determine strictness
    is_strict = is_pfsense and self.strict_mode_enabled

    # Log mode
    if is_pfsense:
        print(f"🔒 STRICT MODE: Request from pfSense ({client_ip}, MAC: {mac_address})")
    else:
        print(f"🔓 RELAXED MODE: Request from LAN ({client_ip})")

    # Run all security checks
    self.check_authorization_header_security(request, is_strict)
    self.check_path_security(request, is_strict)
    self.check_method_override(request, is_strict)
    self.check_protocol_downgrade(request, is_strict)
```

**security_middleware function**:
```python
async def security_middleware(request: Request, call_next):
    try:
        # Validate request
        await security_validator.validate_request(request)

        # Continue to endpoint
        response = await call_next(request)
        return response

    except HTTPException as e:
        # Return as JSON
        return JSONResponse(
            status_code=e.status_code,
            content={
                "success": False,
                "error": e.detail,
                "timestamp": datetime.now().isoformat()
            }
        )
```

### 5. api/validation.py

**Purpose**: URL validation and SQL injection prevention.

**URL validation**:
```python
def validate_url(url: str) -> bool:
    # Block localhost
    if "localhost" in url or "127.0.0.1" in url or "::1" in url:
        return False

    # Block private IPs
    if any(url.startswith(prefix) for prefix in [
        "10.", "172.16.", "192.168."
    ]):
        return False

    # Block cloud metadata endpoints
    if "169.254.169.254" in url or "100.100.100.200" in url:
        return False

    # Block internal TLDs
    if any(tld in url for tld in [".local", ".internal", ".corp"]):
        return False

    return True
```

**SQL injection prevention**:
```python
def validate_string_length(value: str, max_length: int, field_name: str) -> str:
    # NULL byte check
    if "\x00" in value:
        raise ValueError(f"{field_name} contains invalid characters")

    # Length check
    if len(value) > max_length:
        raise ValueError(f"{field_name} exceeds maximum length of {max_length}")

    # SQL keyword detection (case-insensitive)
    dangerous_keywords = ["DROP", "DELETE", "INSERT", "UPDATE", "CREATE", "ALTER"]
    value_upper = value.upper()
    for keyword in dangerous_keywords:
        if keyword in value_upper:
            raise ValueError(f"{field_name} contains potentially dangerous content")

    return value
```

### 6. config.py (68 lines)

**Purpose**: Centralized configuration with type safety.

```python
class Config(BaseSettings):
    # Server
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8081
    LOG_LEVEL: str = "INFO"

    # CORS
    ENABLE_CORS: bool = True
    CORS_ORIGINS: str = "*"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    ENABLE_RATE_LIMIT: bool = True

    # Security - pfSense Integration
    ENABLE_MAC_VALIDATION: bool = False
    STRICT_AUTH_FOR_PFSENSE: bool = False
    PFSENSE_IP: str = "192.168.10.1"
    PFSENSE_MAC: str = "00:00:00:00:00:00"
    TRUSTED_LAN_SUBNET: str = "192.168.10.0/24"

    class Config:
        env_file = ".env"
        case_sensitive = True
```

## Request/Response Flow

### Simple Search Flow

```
HTTP POST /api/v1/search
    ↓
Security Middleware
    ├─ Validate IP/MAC
    ├─ Check security mode (strict/relaxed)
    ├─ Run security checks
    └─ Continue or 404
    ↓
FastAPI Endpoint Handler
    ├─ Parse JSON body
    ├─ Pydantic validation (SearchRequest model)
    └─ Extract session data
    ↓
Authentication Dependency
    ├─ Extract Bearer token
    ├─ Verify against OPENAI_API_KEY(S)
    ├─ Check rate limit
    ├─ Create session
    └─ Return session data or 404
    ↓
Search Operation
    ├─ Direct call: await rag_system.search_knowledge(...)
    ├─ robaimodeltools.operations.crawler.Crawl4AIRAG
    ├─ Vector similarity search (SQLite + sqlite-vec)
    ├─ Sort by similarity score
    └─ Return top N results
    ↓
Response Formatting
    ├─ Wrap in standard response format
    ├─ Add timestamp
    ├─ Add X-Process-Time header
    └─ JSON serialization
    ↓
HTTP 200 + JSON Response
```

**Timing breakdown** (typical):
- Security middleware: 2-5ms
- Authentication: 1-3ms
- Search operation: 50-100ms
- Response formatting: 1-2ms
- **Total: 55-110ms**

### KG Search Flow (5-Phase)

```
HTTP POST /api/v1/search/kg
    ↓
Security Middleware (2-5ms)
    ↓
Authentication (1-3ms)
    ↓
Search Operation Setup
    ├─ Parse tags (comma-separated → list)
    ├─ Get KG_SERVICE_URL from env
    ├─ Initialize SearchHandler (from robaimodeltools.search.search_handler)
    └─ Configure limits (rag_limit, kg_limit)
    ↓
Execute 5-Phase Pipeline (via asyncio.to_thread)
    ├─ Phase 1: GLiNER Entity Extraction (20-30ms)
    │   └─ Extract entities from query
    ├─ Phase 2: Parallel Vector + Graph Search (80-120ms)
    │   ├─ SQLite vector search
    │   └─ Neo4j graph search (via kg-service HTTP)
    ├─ Phase 3: KG Entity Expansion (30-50ms)
    │   └─ Graph traversal for related entities
    ├─ Phase 4: Multi-Signal Ranking (10-20ms)
    │   ├─ Vector similarity: 35%
    │   ├─ Graph connectivity: 25%
    │   ├─ BM25 score: 20%
    │   ├─ Recency: 10%
    │   └─ Title match: 10%
    └─ Phase 5: Context Extraction (10-20ms)
        └─ Format results with metadata
    ↓
Response Formatting
    ├─ Separate RAG and KG results
    ├─ Add processing time
    └─ JSON serialization (1-4MB typical)
    ↓
HTTP 200 + JSON Response

Total: 150-250ms typical
```

### Deep Crawl Flow

```
HTTP POST /api/v1/crawl/deep/store
    ↓
Security Middleware (2-5ms)
    ↓
Authentication (1-3ms)
    ↓
Deep Crawl Operation (run in thread pool via asyncio.to_thread)
    ├─ Validate root URL
    ├─ Initialize crawl queue
    ├─ Start recursive crawling
    │   ├─ Crawl page 1 (via Crawl4AI HTTP)
    │   ├─ Extract links from page 1
    │   ├─ Score links by relevance
    │   ├─ Add qualified links to queue
    │   ├─ Crawl page 2...
    │   └─ Continue until max_depth or max_pages reached
    ├─ Process each crawled page
    │   ├─ Extract text content
    │   ├─ Generate embeddings
    │   ├─ Split into chunks
    │   └─ Store in SQLite with retention policy
    └─ Return summary
    ↓
Response Formatting
    ├─ Pages crawled count
    ├─ URLs list
    ├─ Content IDs list
    ├─ Crawl duration
    └─ Timestamp
    ↓
HTTP 200 + JSON Response

Total: 30-180 seconds (depends on max_pages)
```

## Search Endpoint Comparison

### 1. Simple Search (`/api/v1/search`)

**Purpose**: Fast vector similarity search, no KG overhead.

**Pipeline**:
```
Query → Embedding → SQLite vector search → Sort by similarity → Return
```

**Performance**: 50-100ms
**Data size**: 10-50KB (5-10 results)
**Requirements**: None (only SQLite)
**Use case**: Quick lookups, known keywords

### 2. KG Search (`/api/v1/search/kg`)

**Purpose**: Comprehensive 5-phase knowledge graph analysis.

**Pipeline**:
```
Query
    → Phase 1: GLiNER entity extraction
    → Phase 2: Parallel vector + Neo4j graph search
    → Phase 3: KG entity expansion (graph traversal)
    → Phase 4: Multi-signal ranking (5 signals)
    → Phase 5: Context extraction
    → Return RAG + KG results
```

**Performance**: 150-250ms
**Data size**: 1-4MB (comprehensive results)
**Requirements**: Neo4j + kg-service running
**Use case**: Complex queries, research, exploration

### 3. Enhanced Search (`/api/v1/search/enhanced`)

**Purpose**: Optimized search with focused, high-quality results.

**Pipeline**:
```
Query
    → GLiNER entity extraction
    → Fetch 250 KG chunks from kg-service
    → Aggregate to 20 documents
    → Entity density ranking
    → Return:
        - 1 top RAG result (full doc, 100K char limit)
        - 10 KG chunks (entity-rich snippets)
        - 1 top KG document (full doc, 100K char limit, different URL)
```

**Performance**: 200-300ms
**Data size**: 200-250KB (90% smaller than KG search)
**Requirements**: Neo4j + kg-service running
**Use case**: Comprehensive context with controlled data size

**Comparison table**:

| Feature | Simple | KG Search | Enhanced |
|---------|--------|-----------|----------|
| Speed | 50-100ms | 150-250ms | 200-300ms |
| Data size | 10-50KB | 1-4MB | 200-250KB |
| Entity extraction | No | Yes | Yes |
| Graph traversal | No | Yes | No |
| Multi-signal ranking | No | Yes | Yes (entity density) |
| Results | N chunks | RAG + KG separate | 1 RAG doc + 10 chunks + 1 KG doc |
| Requirements | SQLite only | Neo4j + kg-service | Neo4j + kg-service |
| Best for | Quick lookups | Research | Balanced quality + size |

## Middleware Stack

**Execution order** (LIFO - Last In, First Out):

```
1. security_middleware (FIRST)
    ├─ IP+MAC validation
    ├─ Security checks
    └─ Attack detection
    ↓
2. CORSMiddleware (if enabled)
    ├─ Handle preflight OPTIONS
    ├─ Add CORS headers
    └─ Continue
    ↓
3. add_process_time_header
    ├─ Record start time
    ├─ Call next (endpoint)
    ├─ Calculate duration
    └─ Add X-Process-Time header
    ↓
4. Endpoint Handler
    ├─ Pydantic validation
    ├─ Authentication dependency (verify_api_key)
    ├─ Business logic
    └─ Return response
```

**Why security middleware is FIRST**:
- Rejects attacks before any processing
- Prevents auth bypass attempts
- Protects CORS middleware itself

## Background Tasks

### Session Cleanup Task

```python
async def session_cleanup_task():
    """Cleanup expired sessions periodically"""
    while True:
        await asyncio.sleep(3600)  # Every hour
        cleanup_sessions()
```

Started automatically on application startup:

```python
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(session_cleanup_task())
```

**Purpose**: Remove sessions inactive for 24+ hours to free memory.

## Error Handling

### Global Exception Handler

```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )
```

### Endpoint-Level Error Handling

```python
@app.post("/api/v1/crawl/store")
async def crawl_and_store(...):
    try:
        result = await rag_system.crawl_and_store(...)
        return {"success": True, "data": result, "timestamp": ...}
    except ValueError as e:
        # Validation error (400 Bad Request)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Log error
        log_error("api_crawl_store", e, request.url)
        # Return 500
        raise HTTPException(status_code=500, detail=str(e))
```

**Standard error response format**:
```json
{
  "success": false,
  "error": "Error message here",
  "timestamp": "2025-01-18T10:30:45.123456"
}
```

## Performance Optimizations

### 1. Single Crawl4AIRAG Instance

**Why**:
```python
# Module-level singleton
rag_system = Crawl4AIRAG(crawl4ai_url=crawl4ai_url)

# Not created per-request
# Shared across all requests
# Reuses connections, caches
```

**Benefits**:
- Connection pooling to Crawl4AI
- Shared caches
- Lower memory usage

### 2. Thread Pool for Blocking Operations

```python
# Deep crawl is blocking (sync function)
result = await asyncio.to_thread(
    rag_system.deep_crawl_and_store,
    url, ...
)

# Runs in thread pool, doesn't block event loop
# Other requests continue processing
```

### 3. Process Time Header

```python
@app.middleware("http")
async def add_process_time_header(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
    return response
```

**Purpose**: Client can track performance, detect slow requests.

### 4. Streaming Not Implemented

**Current**: All responses are buffered and sent at once.

**Why**: Most operations complete in 50-300ms, streaming not necessary.

**Future**: Could add streaming for deep crawl progress updates.

## Security Architecture

### Defense in Depth (5 Layers)

**Layer 1: Network Security**
- IP+MAC validation (strict mode)
- Trusted subnet filtering (relaxed mode)
- pfSense integration

**Layer 2: Request Security**
- Path traversal detection
- Method override blocking
- Protocol downgrade blocking
- Suspicious header detection

**Layer 3: Authentication**
- Bearer token required (except /health)
- Multi-key support (rotation)
- Rate limiting (60 req/min/key)
- Returns 404 on auth failure (security by obscurity)

**Layer 4: Input Validation**
- Pydantic schema validation
- URL security checks (no localhost, private IPs, metadata endpoints)
- SQL injection prevention
- Length limits

**Layer 5: Business Logic**
- robaimodeltools enforces domain blocking
- Retention policies prevent data leaks
- Session timeouts (24 hours)

### Attack Scenarios and Defenses

**Scenario 1: API Key Brute Force**
- Defense: Rate limiting (60 req/min) + 404 response (hides endpoint)
- Attacker can't tell if key is wrong or endpoint doesn't exist

**Scenario 2: IP Spoofing**
- Defense: MAC validation (strict mode)
- Even if attacker spoofs pfSense IP, MAC won't match

**Scenario 3: Path Traversal**
- Defense: ".." detection + encoded pattern detection (%2e%2e)
- Blocked at middleware layer (before reaching endpoint)

**Scenario 4: Method Override Bypass**
- Defense: X-HTTP-Method-Override header blocked
- Attacker can't change POST to GET/DELETE

**Scenario 5: SQL Injection**
- Defense: Parameterized queries + keyword detection + NULL byte filtering
- Multiple layers prevent injection

**Scenario 6: SSRF (Server-Side Request Forgery)**
- Defense: URL validation blocks localhost, private IPs, cloud metadata
- Can't use crawl endpoints to probe internal network

## Deployment Patterns

### Single Instance (Development)

```bash
# Direct uvicorn
python main.py

# Or manually
uvicorn api.server:app --host 0.0.0.0 --port 8081
```

**Pros**: Simple, easy debugging
**Cons**: Single point of failure, limited throughput

### Multi-Worker (Production)

```bash
gunicorn api.server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8081 \
  --timeout 120
```

**Pros**: Better throughput, worker isolation
**Cons**: Shared rate limiter (in-memory), no distributed state

### Docker (Recommended)

```yaml
# docker-compose.yml
services:
  robairagapi:
    image: robairagapi:latest
    network_mode: "host"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - SERVER_PORT=8081
    volumes:
      - robaimodeltools:/robaimodeltools
      - robaidata:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8081/health"]
      interval: 30s
```

**Pros**: Reproducible, isolated, easy scaling
**Cons**: Requires Docker infrastructure

### Behind Reverse Proxy

```nginx
upstream robairagapi {
    server localhost:8081;
    keepalive 32;
}

server {
    listen 443 ssl;
    server_name api.example.com;

    location / {
        proxy_pass http://robairagapi;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Authorization $http_authorization;
    }
}
```

**Pros**: TLS termination, load balancing, caching
**Cons**: Additional infrastructure complexity

## Monitoring and Observability

### Health Check Endpoint

```bash
curl http://localhost:8081/health
```

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-18T10:30:45.123456",
  "mcp_connected": true,
  "version": "1.0.0"
}
```

**Use cases**:
- Docker healthchecks
- Load balancer health probes
- Monitoring systems (Prometheus, etc.)

### Detailed Status Endpoint

```bash
curl -H "Authorization: Bearer $API_KEY" \
  http://localhost:8081/api/v1/status
```

**Response**:
```json
{
  "api_status": "running",
  "mcp_status": "direct",
  "timestamp": "2025-01-18T10:30:45.123456",
  "components": {
    "crawl4ai_url": "http://localhost:11235",
    "mode": "direct"
  }
}
```

### Logging

**Log format**:
```
[timestamp] [level] [module] - message
```

**Key events logged**:
- Server startup/shutdown
- Authentication failures (with IP)
- Rate limit exceeded (with API key preview)
- Security alerts (spoofing attempts, attacks)
- Endpoint errors (with exception details)

**Log levels**:
- DEBUG: Detailed request/response data
- INFO: Normal operations
- WARNING: Recoverable issues
- ERROR: Operation failures

### Metrics (via /api/v1/stats)

```json
{
  "total_content": 1234,
  "total_chunks": 45678,
  "total_embeddings": 45678,
  "db_size_mb": 234.5,
  "permanent_content": 1000,
  "session_content": 150,
  "30day_content": 84,
  "tag_distribution": {
    "python": 450,
    "javascript": 320
  }
}
```

## Scalability Considerations

### Current Limitations

1. **In-memory rate limiter**: Not shared across instances
2. **In-memory sessions**: Lost on restart
3. **SQLite backend**: Single-writer bottleneck
4. **No distributed locking**: Multiple instances can conflict

### Scaling Recommendations

**Vertical Scaling**:
- Increase workers: `--workers $(nproc)`
- More RAM: Larger SQLite cache
- Faster CPU: Better request throughput

**Horizontal Scaling** (requires changes):
- Redis for rate limiter (shared state)
- Redis for sessions (persistent)
- PostgreSQL instead of SQLite (multi-writer)
- Load balancer with sticky sessions

**Database Scaling**:
- SQLite: Good for ~10-100 req/s
- PostgreSQL: Good for ~100-1000 req/s
- Distributed DB: 1000+ req/s

## Next Steps

- [Getting Started](getting-started.md) - Installation and usage
- [Configuration](configuration.md) - Complete configuration reference
- [API Reference](api-reference.md) - All endpoints documented
