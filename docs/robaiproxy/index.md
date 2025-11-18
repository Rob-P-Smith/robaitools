---
layout: default
title: robaiproxy
nav_order: 8
has_children: true
---

# robaiproxy

**Intelligent API Gateway and Research Orchestration Proxy**

A sophisticated FastAPI-based proxy service that sits between clients and a vLLM language model backend, providing transparent request forwarding and multi-iteration web research capabilities.

## Overview

robaiproxy is an intelligent API gateway that provides two primary modes of operation:

1. **Passthrough Mode**: Transparent forwarding of standard chat completions to vLLM with minimal latency
2. **Research Mode**: Multi-iteration, context-accumulating web research with integrated knowledge base searches

The service acts as a central orchestration hub coordinating between multiple backends (vLLM, MCP RAG server, Serper web search API) to provide comprehensive research capabilities while maintaining compatibility with the OpenAI chat completions API.

## What Makes This Different

Unlike traditional reverse proxies or API gateways, robaiproxy:

- **Intelligent Request Routing**: Detects research intent and routes to appropriate handler
- **Multi-Iteration Research**: Performs 2-4 research iterations with progressive context accumulation
- **Multi-Source Information Gathering**: Combines web search, knowledge base queries, and URL crawling
- **Context Accumulation**: Preserves all research context (potentially 100K+ tokens) for final answer
- **Auto-Retry Logic**: Automatically reduces iteration count on context overflow
- **Queue Management**: Limits concurrent research requests with user-friendly status messages
- **Power Management**: GPU performance level automation based on API activity

## Key Features

### Dual Mode Operation

- **Passthrough Mode**: Direct streaming to vLLM for regular chat
- **Research Mode**: Multi-iteration research with web search and knowledge base integration

### Research Capabilities

- **Intelligent Query Generation**: LLM generates diverse search queries to avoid repetition
- **Multi-Source Data Collection**:
  - Web search via Serper API (10 initial + 5 per iteration)
  - Knowledge base search via MCP server (3-6 results per iteration)
  - Fresh URL crawling (3 URLs per iteration)
- **Progressive Context Accumulation**: All results added without truncation
- **Auto-Retry on Context Overflow**: Automatically reduces iterations if context limit exceeded
- **Client Disconnect Detection**: Gracefully stops research on abandoned requests

### Queue Management

- **Concurrent Request Limiting**:
  - Standard research: Max 3 concurrent
  - Deep research: Max 1 concurrent
- **User-Friendly Status Messages**: Queue position and availability communicated via streaming
- **Health Checks on Queue Full**: Verifies backend availability when waiting

## Quick Start

### Installation

```bash
cd robaiproxy

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Add API keys

# Start the service
uvicorn requestProxy:app --host 0.0.0.0 --port 8079
```

### Basic Usage

**Regular Chat (Passthrough)**:
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
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

**Research Mode**:
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

## System Architecture

```
Client Request (OpenAI-compatible)
    ↓
[Model Availability Check & Wait]
    ↓
[Multimodal Content Detection]
    ↓
[Research Mode Detection]
    ├─→ "research" keyword detected
    │   ↓
    │   [Queue Management (Semaphore)]
    │   ↓
    │   [Multi-iteration Research Mode]
    │   ├─→ Initial Serper Search (10 results)
    │   ├─→ 2-4 Research Iterations, each:
    │   │   ├─→ Generate search query
    │   │   ├─→ Search knowledge base (3-6 results)
    │   │   ├─→ Generate URLs
    │   │   ├─→ Crawl URLs (3 URLs)
    │   │   └─→ Generate + execute Serper search (5 results)
    │   └─→ Generate final answer with accumulated context
    │
    └─→ No "research" keyword
        ↓
        [Direct Passthrough to vLLM]
```

## Service Dependencies

```
robaiproxy (Port 8079)
    ├→ vLLM (8078) - LLM generations
    ├→ MCP RAG (8080) - Knowledge base & crawling
    │   └→ robaimodeltools - RAG operations
    │       ├→ crawl4ai - Web crawling
    │       └→ kg-service (8088) - Knowledge graph
    │           └→ Neo4j (7474) - Graph database
    ├→ Serper API - Web search
    └→ robairagapi (8081) - General RAG API
```

## Core Components

### requestProxy.py (975 lines)

Main FastAPI application with request routing and orchestration.

**Key Responsibilities**:
- HTTP request handling and routing
- Research mode detection
- Model availability monitoring
- Health check coordination
- Queue management
- Request forwarding to vLLM

### researchAgent.py (1,026 lines)

Multi-iteration research workflow with context accumulation.

**Key Responsibilities**:
- Research iteration execution
- Tool call extraction and execution
- Context accumulation
- SSE (Server-Sent Events) formatting
- Auto-retry on context overflow

### config.py (180 lines)

Environment-based configuration with validation.

**Configuration Categories**:
- vLLM Backend
- MCP Server
- External APIs (Serper)
- Research Limits
- Server Config
- Feature Flags

## Operating Modes

### Passthrough Mode

**When Activated**:
- No "research" keyword in user message, OR
- Multimodal content detected (images, audio)

**Use Cases**:
- Regular chat conversations
- Code generation
- Q&A without research
- Multimodal requests

### Research Mode

**When Activated**:
- User message starts with "research" keyword

**Research Types**:

**Standard Research (2 iterations)**:
```json
{
  "messages": [
    {"role": "user", "content": "research kubernetes networking"}
  ]
}
```

**Deep Research (4 iterations)**:
- Triggered by modifiers: thoroughly, carefully, all, comprehensively, comprehensive, deep, deeply, detailed, extensive, extensively

```json
{
  "messages": [
    {"role": "user", "content": "research thoroughly kubernetes networking"}
  ]
}
```

## API Endpoints

### Main Endpoints

- **POST /v1/chat/completions** - Main chat endpoint with intelligent routing
- **GET /health** - Comprehensive multi-service health check
- **GET /v1/models** - List available models (cached from vLLM)
- **GET /openapi.json** - Proxy RAG API OpenAPI schema

### Health Check Response

```json
{
  "status": "healthy",
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
    }
  }
}
```

## Research Workflow

### Phase 1: Initial Search

1. Detect "research" keyword
2. Check queue availability
3. Perform initial Serper search (10 results)
4. Add results to accumulated_context

### Phase 2: Iteration Loop (2-4 times)

For each iteration:
1. Generate search query (LLM)
2. Search knowledge base (MCP) - 3-6 results
3. Generate URLs (LLM)
4. Crawl URLs (MCP) - 3 URLs
5. Generate Serper query (LLM)
6. Execute Serper search - 5 results
7. Add all results to accumulated_context
8. Check for client disconnect
9. Continue to next iteration

### Phase 3: Final Answer

1. Create final prompt with accumulated_context
2. Generate comprehensive answer (LLM)
3. Stream answer to client
4. Send [DONE] marker

## Statistics

- **Total Lines**: ~3,200 lines of application code
- **Python Packages**: 23 direct dependencies
- **Core Framework**: FastAPI 0.119.0 + Uvicorn 0.37.0
- **Downstream Services**: 6 (vLLM, MCP RAG, Serper, robairagapi, crawl4ai, Neo4j)
- **Monitored Services**: 6 (vllm-qwen3, kg-service, mcprag-server, crawl4ai, neo4j-kg, open-webui)
- **Critical Services**: 3 (vllm-qwen3, kg-service, neo4j-kg)

## Design Patterns

1. **Intelligent Request Router** - Content-based routing with mode detection
2. **Semaphore-Based Queue Management** - Asyncio semaphore for concurrency control
3. **Progressive Context Accumulation** - Append-only context building
4. **Tool Call Pattern** - XML-tagged tool calls in LLM responses
5. **Background Model Monitoring** - Asyncio background task with polling
6. **Auto-Retry on Context Overflow** - Exception-driven retry with reduced scope
7. **Client Disconnect Detection** - Periodic request.is_disconnected() checks

## Next Steps

- [Getting Started](getting-started.html) - Installation and basic usage
- [Configuration](configuration.html) - Configuration options and environment variables
- [API Reference](api-reference.html) - Complete API documentation
- [Architecture](architecture.html) - Detailed architecture and design patterns
