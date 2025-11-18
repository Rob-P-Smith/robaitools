---
layout: default
title: Architecture
parent: robaiproxy
nav_order: 4
---

# Architecture

Detailed architectural documentation for robaiproxy.

## System Overview

robaiproxy is an intelligent API gateway that orchestrates between multiple backend services to provide both transparent request forwarding and advanced multi-iteration research capabilities.

```
┌─────────────────────────────────────────────────────────┐
│                   robaiproxy (Port 8079)                │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Intelligent Request Router                        │  │
│  │  ├─ Mode Detection (research keyword)            │  │
│  │  ├─ Multimodal Detection (images/audio)         │  │
│  │  └─ Queue Management (semaphores)                │  │
│  └───────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────────┐  ┌──────────────────────────────┐    │
│  │ Passthrough  │  │ Research Orchestrator        │    │
│  │ Mode         │  │  ├─ Initial Serper Search    │    │
│  │  └─ vLLM     │  │  ├─ Iteration Loop (2-4x)    │    │
│  │    Streaming │  │  │  ├─ KB Search              │    │
│  │              │  │  │  ├─ URL Crawling           │    │
│  │              │  │  │  └─ Web Search             │    │
│  │              │  │  └─ Final Answer Generation   │    │
│  └──────────────┘  └──────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
         │                    │         │         │
         │                    │         │         │
    ┌────┴─────┐  ┌──────────┴─┐  ┌───┴────┐  ┌─┴────────┐
    │  vLLM    │  │ MCP RAG    │  │ Serper │  │robairagapi│
    │  (8078)  │  │  (8080)    │  │  API   │  │  (8081)   │
    └──────────┘  └────────────┘  └────────┘  └───────────┘
```

## Core Components

### 1. requestProxy.py (975 lines)

**Purpose**: Main FastAPI application handling HTTP requests and orchestration.

**Architecture Layers**:

```
┌─────────────────────────────────────────┐
│         HTTP Request Layer              │
│  ├─ FastAPI Application                │
│  ├─ Middleware                          │
│  └─ CORS Configuration                  │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│      Request Routing Layer              │
│  ├─ Mode Detection                      │
│  │  ├─ Research keyword check           │
│  │  └─ Multimodal detection             │
│  ├─ Model Availability Check            │
│  └─ Queue Management                    │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│      Execution Layer                    │
│  ├─ Passthrough Handler                │
│  │  ├─ Streaming                        │
│  │  └─ Non-streaming                    │
│  └─ Research Handler                    │
│     ├─ Queue wrapper                    │
│     └─ Research agent invocation        │
└─────────────────────────────────────────┘
```

**Key Functions**:

| Function | Purpose | Lines |
|----------|---------|-------|
| `autonomous_chat()` | Main endpoint handler | ~150 |
| `detect_research_mode()` | Keyword detection | ~20 |
| `is_multimodal()` | Content type detection | ~15 |
| `passthrough_stream()` | Transparent streaming | ~80 |
| `passthrough_sync()` | Non-streaming forward | ~60 |
| `research_with_queue_management()` | Queue + research | ~100 |
| `wait_for_model()` | Startup model check | ~40 |
| `model_name_manager()` | Background polling | ~60 |
| `check_research_health()` | Health verification | ~150 |

**Global State Management**:

```python
# Model tracking
current_model_name: Optional[str] = None
current_model_data: Optional[dict] = None
model_fetch_task: Optional[asyncio.Task] = None

# Queue control
research_semaphore = asyncio.Semaphore(MAX_STANDARD_RESEARCH)
deep_research_semaphore = asyncio.Semaphore(MAX_DEEP_RESEARCH)

# Connection tracking
connection_manager = ConnectionManager()

# Power management (disabled)
# power_manager = PowerManager()
```

### 2. researchAgent.py (1,026 lines)

**Purpose**: Multi-iteration research workflow with context accumulation.

**Research Pipeline Architecture**:

```
┌────────────────────────────────────────────────┐
│           Initial Search Phase                 │
│  └─ Serper Web Search (10 results)            │
└────────────────────────────────────────────────┘
                    ↓
┌────────────────────────────────────────────────┐
│         Iteration Loop (2 or 4 times)          │
│  ┌──────────────────────────────────────────┐ │
│  │  Phase 1: Generate Search Query (LLM)    │ │
│  └──────────────────────────────────────────┘ │
│                    ↓                           │
│  ┌──────────────────────────────────────────┐ │
│  │  Phase 2: Knowledge Base Search (MCP)    │ │
│  │   Returns: 3-6 results with content      │ │
│  └──────────────────────────────────────────┘ │
│                    ↓                           │
│  ┌──────────────────────────────────────────┐ │
│  │  Phase 3: Generate URLs (LLM)            │ │
│  └──────────────────────────────────────────┘ │
│                    ↓                           │
│  ┌──────────────────────────────────────────┐ │
│  │  Phase 4: Crawl URLs (MCP)               │ │
│  │   Crawls: 3 URLs with full content       │ │
│  └──────────────────────────────────────────┘ │
│                    ↓                           │
│  ┌──────────────────────────────────────────┐ │
│  │  Phase 5: Generate Serper Query (LLM)    │ │
│  └──────────────────────────────────────────┘ │
│                    ↓                           │
│  ┌──────────────────────────────────────────┐ │
│  │  Phase 6: Web Search (Serper)            │ │
│  │   Returns: 5 results                      │ │
│  └──────────────────────────────────────────┘ │
│                    ↓                           │
│  ┌──────────────────────────────────────────┐ │
│  │  Accumulate all results to context       │ │
│  └──────────────────────────────────────────┘ │
└────────────────────────────────────────────────┘
                    ↓
┌────────────────────────────────────────────────┐
│         Final Answer Generation                │
│  ├─ Full accumulated context (60K-120K chars) │
│  ├─ LLM generates comprehensive answer        │
│  └─ Stream to client                          │
└────────────────────────────────────────────────┘
```

**Key Functions**:

| Function | Purpose | Lines |
|----------|---------|-------|
| `search_serper()` | Serper API client | ~60 |
| `call_mcp_tool()` | MCP tool executor | ~80 |
| `extract_tool_calls()` | XML tag parser | ~40 |
| `extract_urls_from_results()` | URL extraction | ~30 |
| `create_sse_chunk()` | SSE formatting | ~40 |
| `get_iteration_focus()` | Iteration instructions | ~50 |
| `_research_mode_stream_internal()` | Core research logic | ~400 |
| `research_mode_stream()` | Retry wrapper | ~100 |
| `research_mode_sync()` | Non-streaming version | ~150 |

**Context Accumulation Strategy**:

```python
accumulated_context = ""

# Phase 1: Initial search
accumulated_context += format_serper_results(initial_results)

# Phase 2: Iterations
for iteration in range(num_iterations):
    # KB search
    kb_results = search_memory(query)
    accumulated_context += format_kb_results(kb_results)

    # URL crawling
    crawled = crawl_urls(urls)
    accumulated_context += format_crawled(crawled)

    # Web search
    web_results = search_web(query)
    accumulated_context += format_web_results(web_results)

# Phase 3: Final answer with full context
final_prompt = build_final_prompt(user_query, accumulated_context)
answer = llm.generate(final_prompt)
```

### 3. config.py (180 lines)

**Purpose**: Environment-based configuration with validation.

**Configuration Architecture**:

```
┌─────────────────────────────────────────┐
│     Environment Variable Loading        │
│  ├─ .env file parsing                  │
│  ├─ Default value application          │
│  └─ Type conversion                     │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│         Validation Layer                │
│  ├─ Required keys check                │
│  ├─ Type validation                     │
│  └─ Range validation                    │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│       Configuration Object              │
│  ├─ Typed attributes                   │
│  ├─ Computed values                     │
│  └─ Masked display                      │
└─────────────────────────────────────────┘
```

**Configuration Categories**:

```python
class Config:
    # vLLM Backend (2 vars)
    VLLM_BASE_URL: str
    VLLM_TIMEOUT: int

    # MCP Server (3 vars)
    REST_API_URL: str
    REST_API_KEY: str  # Required
    MCP_TIMEOUT: int

    # External APIs (2 vars)
    SERPER_API_KEY: str  # Required
    SERPER_TIMEOUT: int

    # Research Limits (2 vars)
    MAX_STANDARD_RESEARCH: int
    MAX_DEEP_RESEARCH: int

    # Server Config (3 vars)
    HOST: str
    PORT: int
    LOG_LEVEL: str

    # Feature Flags (2 vars)
    AUTO_DETECT_MODEL: bool
    MODEL_POLL_INTERVAL: int
```

### 4. connectionManager.py (230 lines)

**Purpose**: Track active API requests for monitoring and power management.

**Connection Tracking Architecture**:

```
┌─────────────────────────────────────────┐
│      Connection Registry                │
│  ├─ Active connections dict             │
│  ├─ Connection metadata                 │
│  └─ Thread-safe operations              │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│      Activity Detection                 │
│  ├─ 0 → 1+ transition (activity start) │
│  ├─ 1+ → 0 transition (activity stop)  │
│  └─ Callback firing                     │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│      Metrics & Status                   │
│  ├─ Active count                        │
│  ├─ Connection list                     │
│  └─ Status queries                      │
└─────────────────────────────────────────┘
```

**Connection Metadata**:

```python
{
    "request_id": str,       # UUID
    "endpoint": str,         # /v1/chat/completions
    "method": str,           # POST
    "client_ip": str,        # 192.168.1.100
    "started_at": datetime,  # UTC timestamp
    "status": str,           # active/completed/failed
    "model": Optional[str],  # Qwen3-30B
    "is_research": bool      # True for research mode
}
```

### 5. powerManager.py (286 lines)

**Purpose**: GPU power management based on API activity (currently disabled).

**Power Management Architecture**:

```
┌─────────────────────────────────────────┐
│      Activity Monitoring                │
│  ├─ Connection count tracking           │
│  ├─ Activity callbacks                  │
│  └─ State transitions                   │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│      Idle Timer Management              │
│  ├─ 2-minute countdown                  │
│  ├─ Timer cancellation                  │
│  └─ Timeout handling                    │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│      GPU Command Execution              │
│  ├─ rocm-smi invocation                │
│  ├─ Performance level setting           │
│  └─ Error handling                      │
└─────────────────────────────────────────┘
```

**Power States**:

```python
class PowerLevel(str, Enum):
    AUTO = "auto"      # Default AMD performance
    LOW = "low"        # Minimal power consumption
    HIGH = "high"      # Maximum performance
    MANUAL = "manual"  # User-controlled
```

**State Machine**:

```
      ┌─────────────┐
      │  Auto Mode  │ ← Default state
      └─────────────┘
            │
            │ No activity for 2 minutes
            ↓
      ┌─────────────┐
      │  Low Power  │
      └─────────────┘
            │
            │ Activity detected
            ↓
      ┌─────────────┐
      │  Auto Mode  │ ← Return to default
      └─────────────┘
```

## Request Flow Diagrams

### Passthrough Mode Flow

```
Client Request
    ↓
┌─────────────────────────┐
│ FastAPI Endpoint        │
│ autonomous_chat()       │
└─────────────────────────┘
    ↓
┌─────────────────────────┐
│ Mode Detection          │
│ ├─ No "research"        │
│ └─ OR multimodal        │
└─────────────────────────┘
    ↓
┌─────────────────────────┐
│ Passthrough Handler     │
│ ├─ Forward to vLLM      │
│ └─ Stream/sync response │
└─────────────────────────┘
    ↓
Client Response
```

### Research Mode Flow

```
Client Request
    ↓
┌──────────────────────────┐
│ FastAPI Endpoint         │
│ autonomous_chat()        │
└──────────────────────────┘
    ↓
┌──────────────────────────┐
│ Mode Detection           │
│ └─ "research" keyword    │
└──────────────────────────┘
    ↓
┌──────────────────────────┐
│ Queue Check              │
│ ├─ Semaphore available?  │
│ └─ Wait if full          │
└──────────────────────────┘
    ↓
┌──────────────────────────┐
│ Research Orchestrator    │
│ ├─ Initial Serper (10)   │
│ ├─ Iteration loop (2-4x) │
│ │  ├─ KB search          │
│ │  ├─ URL crawl          │
│ │  └─ Web search         │
│ └─ Final answer          │
└──────────────────────────┘
    ↓
Client Response (streaming)
```

## Design Patterns

### 1. Intelligent Request Router Pattern

**Implementation**:

```python
def detect_mode(messages):
    first_message = get_first_user_message(messages)

    # Priority 1: Multimodal → Passthrough
    if is_multimodal(messages):
        return "passthrough"

    # Priority 2: Research keyword → Research
    if first_message.lower().startswith("research"):
        return "research"

    # Default: Passthrough
    return "passthrough"
```

**Benefits**:
- Single endpoint for all modes
- Natural language control
- OpenAI API compatibility

### 2. Semaphore-Based Queue Management Pattern

**Implementation**:

```python
research_semaphore = asyncio.Semaphore(3)
deep_research_semaphore = asyncio.Semaphore(1)

async def research_with_queue(is_deep):
    semaphore = deep_research_semaphore if is_deep else research_semaphore

    # Check availability
    if semaphore.locked():
        yield queue_status_message()
        yield health_check_results()

    # Wait for slot
    async with semaphore:
        yield "Slot available. Starting research..."
        async for chunk in perform_research():
            yield chunk
```

**Benefits**:
- Fair FIFO queuing
- Prevents backend overload
- User-friendly status messages
- Automatic release on completion

### 3. Progressive Context Accumulation Pattern

**Implementation**:

```python
accumulated_context = ""

for iteration in iterations:
    # Each iteration adds to context
    results = await search_knowledge_base()
    accumulated_context += format_results(results)

    crawled = await crawl_urls()
    accumulated_context += format_content(crawled)

    web = await search_web()
    accumulated_context += format_web(web)

# Final answer uses complete context
answer = await llm.generate(accumulated_context)
```

**Benefits**:
- No information loss
- Better quality answers
- LLM has full context

### 4. Tool Call Pattern

**Implementation**:

```python
# LLM generates XML-tagged tool calls
response = """
<tool_call>
{
  "name": "search_memory",
  "arguments": {"query": "kubernetes networking"}
}
</tool_call>
"""

# Extract and execute
tool_calls = extract_tool_calls(response)
for call in tool_calls:
    result = await call_mcp_tool(
        tool_name=call["name"],
        arguments=call["arguments"]
    )
    # Add result back to conversation
    messages.append({"role": "user", "content": result})
```

**Benefits**:
- Structured tool invocation
- Multiple tools per response
- LLM-controlled execution

### 5. Background Model Monitoring Pattern

**Implementation**:

```python
async def model_name_manager():
    global current_model_name

    while True:
        try:
            # Poll vLLM
            model = await fetch_model_name()

            if model:
                current_model_name = model
                await asyncio.sleep(10)  # Slow poll
            else:
                await asyncio.sleep(2)   # Fast poll

        except Exception as e:
            logger.error(f"Model polling error: {e}")
            await asyncio.sleep(2)

# Start at startup
@app.on_event("startup")
async def startup():
    global model_fetch_task
    model_fetch_task = asyncio.create_task(model_name_manager())
```

**Benefits**:
- Decoupled availability checking
- Cached model name
- Resilient to failures
- Adaptive polling rate

### 6. Auto-Retry on Context Overflow Pattern

**Implementation**:

```python
async def research_mode_stream(query, iterations=4):
    try:
        # Attempt with requested iterations
        async for chunk in _research_mode_stream_internal(
            query, iterations
        ):
            yield chunk

    except ContextLengthExceededError as e:
        # Auto-retry with reduced iterations
        logger.warning(f"Context overflow, retrying with 2 iterations")

        yield create_sse_chunk(
            "Context overflow detected. Restarting with 2 iterations..."
        )

        # Retry with reduced scope
        async for chunk in _research_mode_stream_internal(
            query, iterations=2
        ):
            yield chunk
```

**Benefits**:
- Graceful degradation
- User informed
- Prevents complete failure

### 7. Client Disconnect Detection Pattern

**Implementation**:

```python
async def research_iteration(request):
    for i in range(iterations):
        # Check disconnect before expensive ops
        if await request.is_disconnected():
            logger.info("Client disconnected, stopping")
            return

        # Proceed with expensive operation
        results = await crawl_urls(urls)
        accumulated_context += results
```

**Benefits**:
- Prevents wasted computation
- Releases resources quickly
- Better system efficiency

## Service Integration

### Upstream Integration

**Open WebUI**:
```
Open WebUI (Port 80)
    ↓
Configured as OpenAI-compatible backend
    ↓
Base URL: http://localhost:8079/v1
    ↓
All chat requests routed through proxy
```

### Downstream Integration

**vLLM Backend**:
```
robaiproxy → http://localhost:8078/v1
    ├─ /v1/chat/completions (all modes)
    ├─ /v1/models (cached)
    └─ Model: Qwen3-30B
```

**MCP RAG Server**:
```
robaiproxy → http://localhost:8080/api/v1
    ├─ search_memory tool
    ├─ crawl_url tool
    └─ Authentication: Bearer token
```

**Serper API**:
```
robaiproxy → https://google.serper.dev/search
    ├─ Web search
    ├─ Authentication: X-API-KEY
    └─ Rate limits per account tier
```

**robairagapi**:
```
robaiproxy → http://localhost:8081
    └─ Catch-all for non-vLLM endpoints
```

## Performance Characteristics

### Passthrough Mode

**Latency**:
- Overhead: ~5-10ms
- Total: vLLM latency + minimal overhead
- Streaming: Real-time forwarding

**Throughput**:
- Limited by vLLM capacity
- No artificial limits in proxy

### Research Mode

**Latency**:

Standard Research (2 iterations):
- Initial search: ~2-3 seconds
- Per iteration: ~10-15 seconds
- Total: ~25-35 seconds

Deep Research (4 iterations):
- Initial search: ~2-3 seconds
- Per iteration: ~10-15 seconds
- Total: ~45-65 seconds

**Context Size**:
- Standard: 40K-60K characters
- Deep: 80K-120K characters
- Auto-retry if exceeds model limit

**Throughput**:
- Standard: Max 3 concurrent
- Deep: Max 1 concurrent
- Queue-based management

## Scalability Considerations

### Current Limitations

**Single Instance**:
- No horizontal scaling
- No distributed queue
- No load balancing

**Queue Limits**:
- Standard: 3 concurrent
- Deep: 1 concurrent
- FIFO waiting for queued requests

**Context Size**:
- Depends on vLLM model window
- Auto-retry helps but doesn't eliminate limit
- Very deep research may still overflow

### Scaling Recommendations

**Horizontal Scaling**:
```
Load Balancer
    ├─ robaiproxy instance 1
    ├─ robaiproxy instance 2
    └─ robaiproxy instance 3
        ↓
    Shared vLLM cluster
```

**Queue Scaling**:
```
# Increase limits for high-capacity systems
MAX_STANDARD_RESEARCH=10
MAX_DEEP_RESEARCH=3
```

**Backend Scaling**:
```
# Multiple vLLM instances behind load balancer
VLLM_BASE_URL=http://vllm-loadbalancer:8078/v1
```

## Security Architecture

### API Key Management

**Storage**:
- `.env` file (not committed)
- Environment variables
- File permissions: 600

**Usage**:
- MCP: Bearer token
- Serper: X-API-KEY header

**Logging**:
- Masked display (last 8 chars)
- No plaintext in logs

### Network Security

**Binding**:
- Default: 0.0.0.0 (all interfaces)
- Development: 127.0.0.1 (localhost)
- Production: Reverse proxy with TLS

**Authentication**:
- Currently: None
- Recommendation: Add middleware for production

## Monitoring & Observability

### Logging

**Console Logging**:
- Level: INFO or configured
- Format: Simple level + message
- Output: stdout

**File Logging**:
- Level: DEBUG (always)
- Format: Timestamp + name + level + message
- File: proxy.log
- Rotation: Manual

### Health Checking

**Multi-Service Checks**:
- Docker container status
- HTTP endpoint availability
- Model loading verification
- Critical service tracking

**Health Statuses**:
- healthy: All critical services up
- degraded: Some non-critical down
- unhealthy: Critical services down

### Metrics

**Connection Tracking**:
- Active count
- Request metadata
- Research vs passthrough
- Duration tracking

**Queue Metrics**:
- Slots used/available
- Wait times
- Completion rates

## Next Steps

- [API Reference](api-reference.html) - Complete API documentation
- [Configuration](configuration.html) - Configuration options
- [Getting Started](getting-started.html) - Installation and setup
