---
layout: default
title: API Reference
parent: robaiproxy
nav_order: 3
---

# API Reference

Complete API documentation for robaiproxy endpoints.

## Overview

robaiproxy provides an OpenAI-compatible API with intelligent routing between passthrough and research modes. All endpoints follow OpenAI API conventions for seamless integration with existing tools.

**Base URL**: `http://localhost:8079`

**Authentication**: Not required (local deployment)

**Content-Type**: `application/json`

## Main Endpoints

### POST /v1/chat/completions

Main chat endpoint with intelligent routing to passthrough or research mode.

**Request Body**:

```json
{
  "model": "string",
  "messages": [
    {
      "role": "user|assistant|system",
      "content": "string"
    }
  ],
  "stream": boolean,
  "max_tokens": integer,
  "temperature": number,
  "top_p": number,
  "n": integer,
  "stop": string | array,
  "presence_penalty": number,
  "frequency_penalty": number,
  "stream_options": {
    "include_usage": boolean
  }
}
```

**Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `model` | string | Yes | - | Model name (e.g., "Qwen3-30B") |
| `messages` | array | Yes | - | Conversation messages |
| `stream` | boolean | No | false | Enable streaming responses |
| `max_tokens` | integer | No | - | Maximum tokens to generate |
| `temperature` | number | No | 1.0 | Sampling temperature (0-2) |
| `top_p` | number | No | 1.0 | Nucleus sampling threshold |
| `n` | integer | No | 1 | Number of completions |
| `stop` | string/array | No | - | Stop sequences |
| `presence_penalty` | number | No | 0 | Presence penalty (-2 to 2) |
| `frequency_penalty` | number | No | 0 | Frequency penalty (-2 to 2) |
| `stream_options` | object | No | - | Streaming configuration |

**Mode Detection**:

The endpoint automatically detects which mode to use:

1. **Research Mode**: Activated if first user message starts with "research"
2. **Passthrough Mode**: All other cases, including multimodal requests

**Streaming Response** (Server-Sent Events):

```
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1234567890,"model":"Qwen3-30B","choices":[{"index":0,"delta":{"role":"assistant","content":"Hello"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1234567890,"model":"Qwen3-30B","choices":[{"index":0,"delta":{"content":" there"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1234567890,"model":"Qwen3-30B","choices":[{"index":0,"delta":{},"finish_reason":"stop"}],"usage":{"prompt_tokens":10,"completion_tokens":20,"total_tokens":30}}

data: [DONE]
```

**Non-Streaming Response**:

```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "Qwen3-30B",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Response text here..."
      },
      "finish_reason": "stop",
      "logprobs": null
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 50,
    "total_tokens": 60
  }
}
```

**Example - Passthrough Mode**:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8079/v1",
    api_key="not-needed"
)

response = client.chat.completions.create(
    model="Qwen3-30B",
    messages=[
        {"role": "user", "content": "Explain Python decorators"}
    ],
    stream=True,
    temperature=0.7
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

**Example - Research Mode (Standard)**:

```python
response = client.chat.completions.create(
    model="Qwen3-30B",
    messages=[
        {"role": "user", "content": "research kubernetes networking"}
    ],
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

**Example - Research Mode (Deep)**:

```python
response = client.chat.completions.create(
    model="Qwen3-30B",
    messages=[
        {"role": "user", "content": "research thoroughly machine learning on kubernetes"}
    ],
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

**Deep Research Triggers**:
- thoroughly
- carefully
- all
- comprehensively / comprehensive
- deep / deeply
- detailed
- extensive / extensively

**cURL Example**:

```bash
curl -X POST http://localhost:8079/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen3-30B",
    "messages": [
      {"role": "user", "content": "research kubernetes networking"}
    ],
    "stream": true
  }'
```

**Error Responses**:

```json
{
  "error": {
    "message": "Error description",
    "type": "invalid_request_error",
    "code": "invalid_request"
  }
}
```

**Status Codes**:
- `200` - Success
- `400` - Bad request (invalid parameters)
- `408` - Request timeout
- `429` - Rate limit exceeded / Queue full
- `500` - Internal server error
- `502` - Bad gateway (backend unavailable)
- `503` - Service unavailable

---

### GET /health

Comprehensive multi-service health check.

**Response**:

```json
{
  "status": "healthy|degraded|unhealthy",
  "service": "request-proxy",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "vllm-qwen3": {
      "model_loaded": true,
      "model_name": "Qwen3-30B",
      "status": "healthy",
      "container_status": "running",
      "available": true
    },
    "kg-service": {
      "status": "healthy",
      "container_status": "running",
      "available": true
    },
    "mcprag-server": {
      "status": "healthy",
      "container_status": "running",
      "available": true
    },
    "crawl4ai": {
      "container_status": "running",
      "available": true
    },
    "neo4j-kg": {
      "status": "healthy",
      "container_status": "running",
      "available": true
    },
    "open-webui": {
      "status": "healthy",
      "container_status": "running",
      "available": true
    }
  }
}
```

**Status Field Values**:

| Status | Description |
|--------|-------------|
| `healthy` | All critical services operational |
| `degraded` | Some non-critical services unavailable |
| `unhealthy` | Critical services unavailable |

**Critical Services**:
- `vllm-qwen3` - Must have model loaded
- `kg-service` - Must be running and healthy
- `neo4j-kg` - Must be running and healthy

**Service Status Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `model_loaded` | boolean | Model is loaded in vLLM |
| `model_name` | string | Name of loaded model |
| `status` | string | Service health status |
| `container_status` | string | Docker container state |
| `available` | boolean | Service is reachable |

**Example**:

```python
import requests

health = requests.get("http://localhost:8079/health").json()

if health["status"] == "healthy":
    print("✓ All systems operational")
    print(f"Model: {health['services']['vllm-qwen3']['model_name']}")
else:
    print(f"✗ Status: {health['status']}")
    for service, status in health["services"].items():
        if not status.get("available", False):
            print(f"  ✗ {service}: unavailable")
```

**cURL Example**:

```bash
curl http://localhost:8079/health
```

---

### GET /v1/models

List available language models.

**Response**:

```json
{
  "object": "list",
  "data": [
    {
      "id": "Qwen3-30B",
      "object": "model",
      "created": 1234567890,
      "owned_by": "organization"
    }
  ]
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `object` | string | Always "list" |
| `data` | array | Array of model objects |
| `id` | string | Model identifier |
| `object` | string | Always "model" |
| `created` | integer | Unix timestamp |
| `owned_by` | string | Model owner |

**Example**:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8079/v1",
    api_key="not-needed"
)

models = client.models.list()
for model in models:
    print(f"Model: {model.id}")
```

**cURL Example**:

```bash
curl http://localhost:8079/v1/models
```

**Notes**:
- Cached from vLLM backend
- Updates automatically via background polling
- Returns empty list if vLLM not ready

---

### GET /openapi.json

Retrieve OpenAPI schema for robairagapi.

**Response**: OpenAPI 3.0 specification (JSON)

**Example**:

```bash
curl http://localhost:8079/openapi.json
```

**Notes**:
- Forwarded from robairagapi on port 8081
- Provides schema for RAG API endpoints
- Used for API documentation generation

---

## Catch-All Routing

### GET/POST /{path:path}

Routes requests to appropriate backend based on path.

**Routing Logic**:

```python
if path in vllm_endpoints:
    forward_to(VLLM_BACKEND_URL)
else:
    forward_to("http://localhost:8081")  # robairagapi
```

**vLLM Endpoints**:
- `/v1/completions`
- `/v1/embeddings`
- `/v1/chat/completions`
- `/tokenize`
- `/detokenize`
- `/v1/models`

**Other Endpoints**: Forwarded to robairagapi

---

## Research Mode API

### Research Workflow

When research mode is activated, the following workflow executes:

**Phase 1: Initial Search**

```
1. Detect "research" keyword in first user message
2. Check queue availability (semaphore)
3. Perform initial Serper web search (10 results)
4. Add results to accumulated_context
```

**Phase 2: Research Iterations**

Standard Research (2 iterations):
1. Main concepts and understanding
2. Practical implementation details

Deep Research (4 iterations):
1. Main concepts and understanding
2. Practical implementation details
3. Advanced features and troubleshooting
4. Ecosystem, alternatives, and comparisons

**Each Iteration**:

```
1. Generate search query (LLM)
   - Tool call: search_memory

2. Search knowledge base (MCP)
   - Returns: 3-6 results with full content
   - Add to accumulated_context

3. Generate URLs (LLM)
   - Tool call: suggest_urls

4. Crawl URLs (MCP)
   - Tool call: crawl_url (3 URLs)
   - Returns: Full page content
   - Add to accumulated_context

5. Generate Serper query (LLM)
   - Tool call: search_web

6. Execute Serper search (5 results)
   - Add to accumulated_context

7. Check for client disconnect
8. Continue to next iteration
```

**Phase 3: Final Answer**

```
1. Create final prompt with full accumulated_context
2. Generate comprehensive answer (LLM)
3. Stream answer to client
4. Send [DONE] marker
```

### Research Status Messages

During research, clients receive status updates via streaming:

**Queue Full**:
```
Research queue is full. Standard research queue (3/3 slots used).
Waiting for an available slot...

[Health check results if services unavailable]

Slot available. Starting research...
```

**Deep Research Queue**:
```
Deep research slot occupied (1/1). Waiting for the slot to become available...

Deep research slot available. Starting deep research...
```

**Context Overflow**:
```
Context overflow detected. The research accumulated too much context.
Restarting with 2 iterations instead of 4...
```

**Client Disconnect**:
```
(Research stops silently, no message sent)
```

### Tool Calls

Research mode uses XML-tagged tool calls:

**search_memory**:
```xml
<tool_call>
{
  "name": "search_memory",
  "arguments": {
    "query": "kubernetes networking concepts"
  }
}
</tool_call>
```

**crawl_url**:
```xml
<tool_call>
{
  "name": "crawl_url",
  "arguments": {
    "url": "https://kubernetes.io/docs/concepts/networking/"
  }
}
</tool_call>
```

**search_web**:
```xml
<tool_call>
{
  "name": "search_web",
  "arguments": {
    "query": "kubernetes service mesh comparison"
  }
}
</tool_call>
```

---

## Queue Management API

### Concurrent Limits

**Standard Research**: Controlled by `research_semaphore`
- Default: 3 concurrent requests
- Configurable via `MAX_STANDARD_RESEARCH`

**Deep Research**: Controlled by `deep_research_semaphore`
- Default: 1 concurrent request
- Configurable via `MAX_DEEP_RESEARCH`

### Queue Behavior

**When Queue Full**:
1. Send status message to client
2. Perform health check (verify backends operational)
3. Send health status if issues detected
4. Wait for available slot (non-blocking)
5. Send availability message when slot opens
6. Begin research

**When Research Completes**:
1. Release semaphore
2. Next queued request proceeds automatically

---

## Error Handling

### Common Errors

**Context Length Exceeded**:

```json
{
  "error": {
    "message": "maximum context length exceeded",
    "type": "context_length_exceeded",
    "code": "context_overflow"
  }
}
```

**Auto-retry behavior**: Automatically reduces iterations and retries

**Backend Unavailable**:

```json
{
  "error": {
    "message": "vLLM backend unavailable",
    "type": "service_unavailable",
    "code": "backend_error"
  }
}
```

**Invalid Request**:

```json
{
  "error": {
    "message": "Invalid request format",
    "type": "invalid_request_error",
    "code": "invalid_request"
  }
}
```

**Authentication Failed** (MCP server):

```json
{
  "error": {
    "message": "MCP authentication failed",
    "type": "authentication_error",
    "code": "auth_failed"
  }
}
```

---

## Integration Examples

### Python with OpenAI SDK

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8079/v1",
    api_key="not-needed"
)

# Passthrough mode
response = client.chat.completions.create(
    model="Qwen3-30B",
    messages=[{"role": "user", "content": "Hello"}],
    stream=True
)

# Research mode
response = client.chat.completions.create(
    model="Qwen3-30B",
    messages=[{"role": "user", "content": "research python async"}],
    stream=True
)
```

### JavaScript/Node.js

```javascript
const OpenAI = require('openai');

const client = new OpenAI({
  baseURL: 'http://localhost:8079/v1',
  apiKey: 'not-needed'
});

async function chat() {
  const response = await client.chat.completions.create({
    model: 'Qwen3-30B',
    messages: [
      { role: 'user', content: 'Explain async/await' }
    ],
    stream: true
  });

  for await (const chunk of response) {
    process.stdout.write(chunk.choices[0]?.delta?.content || '');
  }
}

async function research() {
  const response = await client.chat.completions.create({
    model: 'Qwen3-30B',
    messages: [
      { role: 'user', content: 'research kubernetes networking' }
    ],
    stream: true
  });

  for await (const chunk of response) {
    process.stdout.write(chunk.choices[0]?.delta?.content || '');
  }
}
```

### cURL

```bash
# Passthrough mode
curl -X POST http://localhost:8079/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen3-30B",
    "messages": [
      {"role": "user", "content": "Hello"}
    ],
    "stream": false
  }'

# Research mode
curl -X POST http://localhost:8079/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen3-30B",
    "messages": [
      {"role": "user", "content": "research kubernetes networking"}
    ],
    "stream": true
  }'
```

### HTTPie

```bash
# Passthrough mode
http POST http://localhost:8079/v1/chat/completions \
  model="Qwen3-30B" \
  messages:='[{"role":"user","content":"Hello"}]' \
  stream:=false

# Research mode
http POST http://localhost:8079/v1/chat/completions \
  model="Qwen3-30B" \
  messages:='[{"role":"user","content":"research kubernetes"}]' \
  stream:=true
```

---

## Rate Limiting

robaiproxy uses semaphore-based queue management instead of traditional rate limiting:

**Standard Research**:
- Max concurrent: 3 (configurable)
- No per-minute limit
- Queued requests wait for available slot

**Deep Research**:
- Max concurrent: 1 (configurable)
- No per-minute limit
- Queued requests wait for available slot

**Passthrough Mode**:
- No rate limits
- Limited only by vLLM backend capacity

**External APIs**:
- Serper API: Subject to Serper account limits
- MCP server: No rate limits (internal)

---

## Best Practices

### Streaming

**Always use streaming for research mode**:
```python
stream=True  # Get progress updates and status messages
```

### Error Handling

**Handle context overflow gracefully**:
```python
try:
    response = client.chat.completions.create(...)
    for chunk in response:
        print(chunk.choices[0].delta.content, end="")
except Exception as e:
    if "context length exceeded" in str(e):
        print("Context overflow - automatic retry in progress")
    else:
        raise
```

### Queue Management

**Monitor queue status**:
```python
# Listen for queue status messages in stream
for chunk in response:
    content = chunk.choices[0].delta.content
    if "queue is full" in content.lower():
        print("Waiting in queue...")
```

### Health Checks

**Verify backend health before bulk operations**:
```python
health = requests.get("http://localhost:8079/health").json()
if health["status"] != "healthy":
    print("Warning: Some services unavailable")
    # Decide whether to proceed
```

---

## Next Steps

- [Configuration](configuration.html) - Configure the proxy
- [Architecture](architecture.html) - Understanding the system design
- [Getting Started](getting-started.html) - Installation and setup
