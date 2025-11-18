---
layout: default
title: Getting Started
parent: robaiproxy
nav_order: 1
---

# Getting Started with robaiproxy

Complete installation and setup guide for the robaiproxy intelligent API gateway.

## Prerequisites

Before installing robaiproxy, ensure you have:

- **Python 3.10+** installed
- **Docker** running (for dependent services)
- **vLLM backend** running on port 8078
- **MCP RAG server** (robaitragmcp) running on port 8080
- **Serper API key** from [https://serper.dev](https://serper.dev)

## Installation

### Step 1: Navigate to Directory

```bash
cd /path/to/robaitools/robaiproxy
```

### Step 2: Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt
```

**Key Dependencies**:
- FastAPI 0.119.0 - Web framework
- Uvicorn 0.37.0 - ASGI server
- httpx 0.28.1 - HTTP client
- OpenAI SDK 2.3.0 - LLM client
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
# vLLM Backend
VLLM_BASE_URL=http://localhost:8078/v1

# MCP RAG Server
REST_API_URL=http://localhost:8080/api/v1
REST_API_KEY=your_mcp_api_key_here

# Serper API
SERPER_API_KEY=your_serper_api_key_here

# Server
HOST=0.0.0.0
PORT=8079
```

See [Configuration](configuration.html) for all available options.

### Step 4: Verify Dependencies

Before starting robaiproxy, verify all dependent services are running:

```bash
# Check vLLM is running
curl http://localhost:8078/v1/models

# Check MCP RAG server is running
curl -H "Authorization: Bearer your_api_key" \
  http://localhost:8080/api/v1/health

# Check Docker containers
docker ps
```

Expected containers:
- `vllm-qwen3` - vLLM backend
- `kg-service` - Knowledge graph service
- `neo4j-kg` - Neo4j graph database
- `mcprag-server` - MCP RAG server
- `crawl4ai` - Web crawling service

### Step 5: Start the Service

**Development Mode** (with auto-reload):

```bash
uvicorn requestProxy:app --host 0.0.0.0 --port 8079 --reload
```

**Production Mode** (with multiple workers):

```bash
uvicorn requestProxy:app --host 0.0.0.0 --port 8079 --workers 4
```

**Background Mode**:

```bash
nohup uvicorn requestProxy:app --host 0.0.0.0 --port 8079 > proxy.log 2>&1 &
```

### Step 6: Verify Installation

Check that the service is running:

```bash
# Health check
curl http://localhost:8079/health

# Check model availability
curl http://localhost:8079/v1/models
```

Expected health response:
```json
{
  "status": "healthy",
  "service": "request-proxy",
  "services": {
    "vllm-qwen3": {
      "model_loaded": true,
      "model_name": "Qwen3-30B",
      "status": "healthy"
    }
  }
}
```

## Basic Usage

### Using Python (OpenAI SDK)

#### 1. Install OpenAI SDK

```bash
pip install openai
```

#### 2. Regular Chat (Passthrough Mode)

```python
from openai import OpenAI

# Initialize client pointing to robaiproxy
client = OpenAI(
    base_url="http://localhost:8079/v1",
    api_key="not-needed"  # API key not required for local proxy
)

# Regular chat request
response = client.chat.completions.create(
    model="Qwen3-30B",
    messages=[
        {"role": "user", "content": "Explain Python decorators"}
    ],
    stream=True
)

# Print streaming response
for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

#### 3. Research Mode

```python
# Research request (standard - 2 iterations)
response = client.chat.completions.create(
    model="Qwen3-30B",
    messages=[
        {"role": "user", "content": "research kubernetes networking"}
    ],
    stream=True
)

# Print streaming research progress and results
for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

#### 4. Deep Research Mode

```python
# Deep research (4 iterations) - triggered by modifiers
response = client.chat.completions.create(
    model="Qwen3-30B",
    messages=[
        {"role": "user", "content": "research thoroughly machine learning deployment on kubernetes"}
    ],
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

**Deep Research Triggers**:
- thoroughly
- carefully
- all
- comprehensively/comprehensive
- deep/deeply
- detailed
- extensive/extensively

#### 5. Non-Streaming Mode

```python
# Get complete response at once
response = client.chat.completions.create(
    model="Qwen3-30B",
    messages=[
        {"role": "user", "content": "research python async programming"}
    ],
    stream=False
)

print(response.choices[0].message.content)
```

### Using cURL

#### Regular Chat

```bash
curl -X POST http://localhost:8079/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen3-30B",
    "messages": [
      {"role": "user", "content": "Explain Python decorators"}
    ],
    "stream": false
  }'
```

#### Research Mode

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

### Using with Open WebUI

robaiproxy is fully compatible with Open WebUI as an OpenAI-compatible backend.

**Configure Open WebUI**:

1. Open WebUI Settings → Connections
2. Add new connection:
   - **URL**: `http://localhost:8079/v1`
   - **API Key**: (leave empty or any value)
3. Save and verify connection

**Using Research Mode in Open WebUI**:

Simply start your message with "research" to activate research mode:

```
research explain how kubernetes networking works with practical examples
```

For deep research, add modifiers:

```
research thoroughly explain kubernetes networking, including advanced features
```

## Understanding the Modes

### Passthrough Mode

**Activated When**:
- No "research" keyword in user message
- Multimodal content present (images, audio)

**Behavior**:
- Direct transparent forwarding to vLLM
- Minimal latency overhead
- Full streaming support
- All vLLM features available

**Use Cases**:
- Regular chat conversations
- Code generation
- Quick Q&A
- Image analysis (multimodal)

### Research Mode

**Activated When**:
- User message starts with "research" keyword

**Behavior**:
- Initial web search (10 results)
- 2 or 4 research iterations:
  - Knowledge base search (3-6 results)
  - URL crawling (3 URLs)
  - Additional web search (5 results)
- Progressive context accumulation
- Final comprehensive answer
- Status messages during research

**Use Cases**:
- Current/recent information gathering
- Multi-source research tasks
- In-depth topic exploration
- Comprehensive analysis

**Example Research Flow**:

```
User: "research python async programming"
    ↓
[Proxy detects "research" keyword]
    ↓
[Initial web search: 10 results]
    ↓
[Iteration 1: Main concepts]
  - Search knowledge base
  - Crawl 3 URLs
  - Web search: 5 results
    ↓
[Iteration 2: Practical implementation]
  - Search knowledge base
  - Crawl 3 URLs
  - Web search: 5 results
    ↓
[Generate comprehensive answer]
    ↓
[Stream to client]
```

## Queue Management

When multiple research requests occur simultaneously, robaiproxy manages queuing automatically.

### Concurrency Limits

- **Standard Research**: Max 3 concurrent
- **Deep Research**: Max 1 concurrent

### Queue Behavior

If queue is full, you'll receive status messages:

```
Research queue is full. Standard research queue (3/3 slots used).
Waiting for an available slot...

[Health check results if services are down]

Slot available. Starting research...
```

The request will automatically proceed when a slot becomes available.

## Health Monitoring

Check overall system health:

```python
import requests

health = requests.get("http://localhost:8079/health").json()

print(f"Status: {health['status']}")
print(f"\nServices:")
for service, status in health["services"].items():
    print(f"  {service}: {status.get('status', 'N/A')}")
```

**Status Values**:
- `healthy`: All critical services operational
- `degraded`: Some non-critical services unavailable
- `unhealthy`: Critical services unavailable

## Testing Your Installation

Use the included test suite:

```bash
# Run comprehensive endpoint tests
python test_endpoints.py
```

Tests include:
- Model availability checks
- Passthrough mode tests
- Standard research mode tests
- Deep research mode tests
- Multimodal request tests
- Health endpoint tests
- Error handling tests

## Troubleshooting

### Service Won't Start

**Problem**: `uvicorn` fails to start

**Solutions**:
1. Check port 8079 is not in use:
   ```bash
   lsof -i :8079
   ```
2. Verify all dependencies installed:
   ```bash
   pip install -r requirements.txt
   ```
3. Check configuration file:
   ```bash
   cat .env
   ```

### Health Check Fails

**Problem**: `/health` endpoint returns unhealthy status

**Solutions**:
1. Verify vLLM is running:
   ```bash
   curl http://localhost:8078/v1/models
   ```
2. Check Docker containers:
   ```bash
   docker ps
   ```
3. Verify MCP server:
   ```bash
   curl -H "Authorization: Bearer your_key" \
     http://localhost:8080/api/v1/health
   ```

### Research Mode Not Working

**Problem**: Research requests go to passthrough mode

**Solutions**:
1. Ensure message starts with "research":
   ```python
   messages=[{"role": "user", "content": "research kubernetes"}]
   ```
2. Check MCP server is accessible
3. Verify SERPER_API_KEY is set in `.env`
4. Check logs:
   ```bash
   tail -f proxy.log
   ```

### Queue Full Messages

**Problem**: "Research queue is full" messages

**Solutions**:
1. Wait for current research to complete
2. Increase queue limits in `.env`:
   ```bash
   MAX_STANDARD_RESEARCH=5  # Default: 3
   MAX_DEEP_RESEARCH=2      # Default: 1
   ```
3. Use standard research instead of deep research

### Context Overflow Errors

**Problem**: "Context overflow detected" messages

**Expected Behavior**: System automatically retries with fewer iterations

**If persisting**:
- Research query is too broad
- Consider breaking into smaller queries
- Use standard research instead of deep research

## Performance Tips

1. **Use Streaming**: Enables immediate response feedback
   ```python
   stream=True
   ```

2. **Adjust Research Depth**: Use standard research unless deep analysis needed
   - Standard: 2 iterations (faster)
   - Deep: 4 iterations (comprehensive)

3. **Monitor Queue**: Check active connections
   ```bash
   python check_connections.py
   ```

4. **Optimize Backend**: Ensure vLLM has adequate GPU resources

## Next Steps

- [Configuration](configuration.html) - Detailed configuration options
- [API Reference](api-reference.html) - Complete API documentation
- [Architecture](architecture.html) - Understanding the system design

## Example Scripts

### Simple Chat Client

```python
#!/usr/bin/env python3
from openai import OpenAI

def chat():
    client = OpenAI(
        base_url="http://localhost:8079/v1",
        api_key="not-needed"
    )

    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ['quit', 'exit']:
            break

        print("Assistant: ", end="", flush=True)
        response = client.chat.completions.create(
            model="Qwen3-30B",
            messages=[{"role": "user", "content": user_input}],
            stream=True
        )

        for chunk in response:
            if chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="", flush=True)
        print()

if __name__ == "__main__":
    chat()
```

### Research Helper

```python
#!/usr/bin/env python3
from openai import OpenAI
import sys

def research(query, deep=False):
    client = OpenAI(
        base_url="http://localhost:8079/v1",
        api_key="not-needed"
    )

    if deep:
        query = f"research thoroughly {query}"
    else:
        query = f"research {query}"

    print(f"Researching: {query}\n")
    print("Response:\n", "="*60)

    response = client.chat.completions.create(
        model="Qwen3-30B",
        messages=[{"role": "user", "content": query}],
        stream=True
    )

    for chunk in response:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    print("\n" + "="*60)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python research_helper.py <query> [--deep]")
        sys.exit(1)

    query = " ".join(arg for arg in sys.argv[1:] if not arg.startswith("--"))
    deep = "--deep" in sys.argv

    research(query, deep)
```

**Usage**:
```bash
# Standard research
python research_helper.py kubernetes networking

# Deep research
python research_helper.py kubernetes networking --deep
```
