# RobAI Tools

**Version:** 2.0.0
**A production-grade, multi-service RAG system with intelligent research capabilities, knowledge graph processing, and autonomous tool execution.**

---

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Key Features](#key-features)
- [Service Components](#service-components)
- [Request Flow](#request-flow)
- [Research Modes](#research-modes)
- [Installation & Setup](#installation--setup)
- [Configuration](#configuration)
- [Usage](#usage)
- [Development](#development)
- [Troubleshooting](#troubleshooting)

---

## Overview

**robaitools** is a comprehensive AI research and knowledge management platform that combines:

- **Intelligent Research Orchestration**: Multi-iteration research with web search and knowledge base integration
- **Knowledge Graph Enhancement**: Neo4j-backed entity extraction and relationship mapping
- **Autonomous Tool Execution**: Budget-based tool calling with LLM decision-making
- **RAG Pipeline**: 5-phase semantic search with vector similarity and graph traversal
- **Web Crawling**: Deep crawling with content cleaning and quality filtering
- **Multi-Service Architecture**: Docker-based microservices with non-Docker API gateway

### Architecture Philosophy

- **Microservices**: Each service has a single responsibility and can scale independently
- **Event-Driven**: Streaming responses with real-time status updates
- **Tag-Based Routing**: Explicit user control over request processing modes
- **Graceful Degradation**: Fallback logic ensures service availability during partial failures
- **Security-First**: Multi-layered input validation, SQL injection prevention, SSRF protection

---

## System Architecture

### High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│  User Interface (open-webui on port 80)                           │
│  Chat interface with research mode button                         │
└────────────────┬───────────────────────────────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────────────────────────────┐
│  API Gateway (robaiproxy on port 8079) - NON-DOCKER              │
│  Request routing, mode detection, research orchestration          │
│  Tag Detection: [[autonomous]], [[research_request]], etc.        │
└────────┬──────────────────────────┬────────────────────────────────┘
         │                          │
         ↓                          ↓
┌────────────────────┐    ┌────────────────────────────┐
│  REST API Bridge   │    │  MCP Server                │
│  (robairagapi)     │    │  (robaitragmcp)           │
│  Port: 8081        │    │  Port: 3000 (TCP)         │
│  Bearer auth       │    │  Tool discovery           │
└────────┬───────────┘    └────────┬───────────────────┘
         │                         │
         └───────────┬─────────────┘
                     ↓
         ┌───────────────────────────────┐
         │  Shared RAG Library           │
         │  (robaimodeltools)            │
         │  Vector search, chunking      │
         └───────┬───────────────────────┘
                 │
    ┌────────────┼────────────┬──────────────┐
    ↓            ↓            ↓              ↓
┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────┐
│Crawl4AI │  │KG Service│  │Neo4j DB │  │vLLM (opt)  │
│Port:    │  │Port: 8088│  │Ports:   │  │Port: 8078  │
│11235    │  │Entities  │  │7474,7687│  │(disabled)  │
└─────────┘  └──────────┘  └─────────┘  └────────────┘
```

### Service Dependencies (Startup Order)

1. **crawl4ai** (no dependencies)
2. **neo4j** → waits for crawl4ai network
3. **kg-service** → waits for neo4j + vllm
4. **robaitragmcp** → waits for crawl4ai + kg-service
5. **robairagapi** → waits for robaitragmcp
6. **open-webui** (optional UI)
7. **robaiproxy** (non-Docker, manual start)

### Data Flow

```
User Query
    ↓
open-webui (adds tags like [[research_request]])
    ↓
robaiproxy (detects mode from tags)
    ↓
┌─────────────┬──────────────┬────────────────┐
│ Research    │ Autonomous   │ Pure LLM       │
│ Mode        │ Mode         │ Passthrough    │
└─────────────┴──────────────┴────────────────┘
    ↓              ↓              ↓
robaimultiturn  robaitragmcp   Direct vLLM
    ↓              ↓
robaimodeltools (RAG operations)
    ↓
crawl4ai + kg-service + neo4j
```

---

## Key Features

### 1. Intelligent Research Modes

**Standard Research** (2 iterations):
- Initial Serper web search (10 results)
- Knowledge base search (3-6 results)
- Web crawling (3 URLs)
- Accumulated context for final answer

**Deep Research** (4 iterations):
- All standard research features
- Additional iterations for advanced concepts
- Ecosystem exploration
- Auto-retry with reduced iterations if context overflow

**Triggered by:**
- Explicit tags: `[[research_request]]` or `[[research_deeply]]`
- Agentic detection: LLM classifier analyzes user intent
- Modifiers: "thoroughly", "carefully", "comprehensive", "deep"

### 2. Autonomous Tool Execution

**Features:**
- Budget-based tool calling (configurable points per request)
- Dynamic tool discovery from robaimodeltools
- LLM decides which tools to invoke
- Streaming execution with real-time status updates

**Triggered by:**
- `[[autonomous]]` tag for direct tool execution
- `[[autonomous_plus]]` tag for classifier-based routing (research vs tools)

### 3. Knowledge Graph Enhancement

**Capabilities:**
- Entity extraction with GLiNER (119 entity types)
- Relationship mapping in Neo4j
- Entity expansion for related concepts
- Graph-based retrieval with fuzzy matching

**Pipeline:**
- Content → Extract entities → Store in Neo4j
- Query → Match entities → Traverse relationships → Retrieve relevant chunks

### 4. 5-Phase RAG Pipeline

**Phase 1: Query Understanding**
- GLiNER entity extraction
- Intent detection (informational/transactional/navigational)
- Query normalization

**Phase 2: Parallel Retrieval**
- Vector similarity (SQLite-vec, 384-dim embeddings)
- Graph retrieval (Neo4j entity relationships)
- Concurrent execution

**Phase 3: Knowledge Graph Expansion**
- Related entity discovery
- Relationship traversal
- Co-occurrence patterns

**Phase 4: Multi-Signal Ranking**
- Vector similarity: 35%
- Graph relevance: 25%
- BM25 text match: 20%
- Document recency: 10%
- Title matching: 10%

**Phase 5: Response Formatting**
- Structured JSON response
- Score breakdowns
- Suggested queries
- Entity provenance

### 5. Tag-Based Routing

**System Priority (checked in order):**

1. **Cline Detection** (entire request) → LLM passthrough
   - Detects: `"You are Cline,"`
   - Bypasses all agentic features for IDE integration

2. **Mode Detection** (last user message only)
   - `[[pure_llm]]` → Direct LLM (no RAG/tools/research)
   - `[[research_deeply]]` → 4-iteration deep research
   - `[[research_request]]` → 2-iteration standard research
   - `[[autonomous]]` → Direct tool execution
   - `[[autonomous_plus]]` → Classifier decides (research vs tools)

3. **Auto Mode** (no tag) → Agentic detection
   - PromptAnalyzer determines if research needed
   - Confidence threshold: 0.91
   - Falls back to LLM passthrough if no research detected

**Important:** Tags in the most recent user message override previous tags (multi-turn support)

### 6. Web Crawling & Content Processing

**Single URL Crawl:**
- Stateless extraction via Crawl4AI service
- Content cleaning (navigation/boilerplate removal)
- Error page detection
- Language filtering (English keyword-based)

**Deep Crawl:**
- Breadth-first search with configurable depth (1-5)
- Page limits (1-250)
- Domain blocking (wildcards, substring, exact)
- Social media filtering
- Adult content filtering
- Rate limiting (0.5s delays)

**Content Quality:**
- Navigation density threshold
- Link-to-word ratio filtering
- Minimum content requirements
- Footer detection and removal

---

## Service Components

### robaiproxy (Port 8079) - API Gateway

**Location:** `robaiproxy/`
**Type:** Non-Docker (manual start)
**Language:** Python (FastAPI)

**Responsibilities:**
- Request routing based on tag detection
- Research orchestration (2-4 iteration loops)
- Serper API integration for web search
- Context accumulation (no truncation between iterations)
- Rate limiting and session management
- Analytics tracking

**Key Features:**
- Power management (GPU performance levels)
- Connection monitoring
- User rate limiting (metadata-driven)
- Session timeout (3600s)
- Auto-detection of research intent

**Environment Variables:**
```bash
PROXY_VLLM_URL=http://localhost:8078/v1
REST_API_URL=http://localhost:8081/api/v1
SERPER_API_KEY=your-api-key
MAX_STANDARD_RESEARCH=3
MAX_DEEP_RESEARCH=1
```

### robairagapi (Port 8081) - REST API Bridge

**Location:** `robairagapi/`
**Type:** Docker
**Language:** Python (FastAPI)

**Responsibilities:**
- REST API for MCP tools
- Bearer token authentication
- Rate limiting (60 req/min default)
- CORS configuration
- LAN access support

**Endpoints:**
```
POST /api/v1/search          - Knowledge base search
POST /api/v1/crawl           - Single URL crawl & store
POST /api/v1/deep_crawl      - Recursive crawling
GET  /api/v1/domains         - List domains
POST /api/v1/domains/block   - Block domain pattern
GET  /api/v1/status          - Service health
```

**Authentication:**
```bash
Authorization: Bearer your-api-key
```

### robaitragmcp (Port 3000) - MCP Server

**Location:** `robaitragmcp/`
**Type:** Docker (TCP via socat)
**Language:** Python

**Responsibilities:**
- Dynamic tool discovery from robaimodeltools
- Zero-hardcoded tools (auto-discovery every 30s)
- Tool naming: `{module}_{function}` or `{class}_{method}`
- Action logging with truncation
- Connection via stdio

**Discovered Tools (13+):**
- `crawler_search_knowledge` - Semantic search
- `crawler_crawl_and_store` - Single URL processing
- `crawler_deep_crawl_and_store` - Recursive crawling
- `crawler_add_blocked_domain` - Domain management
- `crawler_list_domains` - Domain listing
- `crawler_get_database_stats` - Metrics
- `crawler_process_ingestion_batch` - Queue processing
- (More auto-discovered from robaimodeltools)

**Environment Variables:**
```bash
MCP_TCP_PORT=3000
MCP_CRAWL4AI_URL=http://localhost:11235
MCP_KG_SERVICE_URL=http://localhost:8088
DB_PATH=/data/crawl4ai_rag.db
USE_MEMORY_DB=true
```

### robaimodeltools - Shared RAG Library

**Location:** `robaimodeltools/`
**Type:** Python package (imported by services)
**Size:** 7,786 lines

**Responsibilities:**
- Core RAG logic and database operations
- Vector similarity search (SQLite-vec)
- Content chunking and embedding generation
- SQL injection prevention
- SSRF protection
- Dual-mode database (RAM with differential sync or disk-only)

**Key Classes:**
- `Crawl4AIRAG` - Facade orchestrator
- `RAGDatabase` - Database abstraction with dual-mode support
- `SearchHandler` - High-level search interface
- `QueryParser` - GLiNER entity extraction
- `VectorRetriever` - SQLite-vec similarity search
- `AdvancedRanker` - Multi-signal ranking

**Architecture:**
- Data Layer: 2,494 lines (persistence, security)
- Operations Layer: 1,436 lines (orchestration)
- Search Layer: 3,856 lines (5-phase pipeline)

### robaimultiturn - Research Orchestration

**Location:** `robaimultiturn/`
**Type:** Python package (imported by robaiproxy)

**Responsibilities:**
- Multi-iteration research loops
- Tool budget management (3-6 points per iteration)
- Duplicate search detection (0.7 similarity threshold)
- Smart content filtering
- Context accumulation
- Status event streaming (Open WebUI native format)

**Functions:**
- `research_stream()` - Streaming research execution
- `research_sync()` - Synchronous research
- `augment_with_rag()` - RAG augmentation
- `augment_with_crawl()` - Web crawl augmentation
- `execute_autonomous_tools_stream()` - Tool execution

**Configuration:**
```bash
ROBAIMULTITURN_TOOL_BUDGET=3
ROBAIMULTITURN_RESEARCH_TOOL_BUDGET=6
ROBAIMULTITURN_AGENTIC_TOOL_BUDGET=4
ROBAIMULTITURN_DUPLICATE_THRESHOLD=0.7
ROBAIMULTITURN_DEEP_MEMORY_LIMIT=4
```

### robaikg - Knowledge Graph Service

**Location:** `robaikg/`
**Type:** Docker (2 containers: kg-service + neo4j)

**Responsibilities:**
- Entity and relationship extraction
- Neo4j graph storage and querying
- Entity expansion via relationship traversal
- Fuzzy entity matching
- KG dashboard (port 8090)

**Endpoints:**
```
POST /api/v1/expand/entities   - Expand via relationships
POST /api/v1/search/entities   - Fuzzy entity matching
POST /api/v1/search/chunks     - Retrieve by entities
GET  /health                   - Service health
```

**Configuration:**
```bash
# Neo4j
NEO4J_USER=neo4j
NEO4J_PASSWORD=knowledge_graph_2024
NEO4J_URI=bolt://localhost:7687
NEO4J_HEAP_MAX_SIZE=16G

# KG Service
KG_SERVICE_PORT=8088
EXTRACTOR_MODEL_URL=http://localhost:8079
AUGMENT_LLM_URL=http://localhost:8078
```

### robaicrawler - Crawl4AI Service

**Location:** `robaicrawler/`
**Type:** Docker
**Port:** 11235

**Responsibilities:**
- Headless browser-based web crawling
- Content extraction and cleaning
- Markdown conversion
- Error page detection

**Endpoint:**
```
POST /crawl
{
  "urls": ["https://example.com"],
  "word_count_threshold": 10,
  "excluded_tags": ["nav", "footer", "aside"],
  "remove_forms": true
}
```

**Configuration:**
```bash
CRAWL4AI_PORT=11235
CRAWL4AI_SHM_SIZE=1gb
CRAWL_URL_MAX_CHARS=20000
CRAWL4AI_CORS_ORIGINS=*
```

### robaiwebui - Open WebUI

**Location:** `robaiwebui/`
**Type:** Docker
**Port:** 80

**Responsibilities:**
- Chat interface
- Research mode button (flask icon)
- Tag injection (`<research_request>`)
- User authentication
- File upload handling

**Features:**
- Research mode button (adds `<research_request>` tag)
- Session persistence
- Multi-turn conversations
- File upload support (RAG processing)

**Configuration:**
```bash
WEBUI_EXTERNAL_PORT=80
OPENAI_API_BASE_URL=http://192.168.10.50:8079/v1
OPENAI_API_KEY=your-api-key
ENABLE_VERSION_UPDATE_CHECK=false
RAG_ALLOWED_FILE_EXTENSIONS=txt,md,pdf,doc,docx,...
```

---

## Request Flow

### Example 1: Research Mode Flow

```
User: "Research Python async programming"
  ↓
open-webui: Adds [[research_request]] tag
  ↓
robaiproxy:
  ├─ Detects tag in last user message
  ├─ Strips tag from LLM input
  ├─ Initiates 2-iteration research
  │
  ├─ Iteration 1:
  │   ├─ Serper search: "python async programming" (10 results)
  │   ├─ RAG search via robairagapi → robaitragmcp → robaimodeltools (3 results)
  │   ├─ Crawl top 3 URLs via Crawl4AI
  │   └─ Accumulate context
  │
  ├─ Iteration 2:
  │   ├─ Serper search: "python asyncio best practices" (5 results)
  │   ├─ RAG search with expanded query (6 results)
  │   ├─ Crawl top 3 new URLs
  │   └─ Accumulate context (appended, not truncated)
  │
  └─ Generate final answer with full accumulated context
      ↓
User: Receives comprehensive research-based response
```

### Example 2: Autonomous Mode Flow

```
User: "[[autonomous]] Search memory for FastAPI docs and summarize"
  ↓
robaiproxy:
  ├─ Detects [[autonomous]] tag in last message
  ├─ Strips tag from LLM input
  ├─ Gets MCP tools from robaitragmcp (13 tools discovered)
  ├─ Injects tool-calling system prompt
  │
  ├─ Turn 1:
  │   ├─ LLM decides to call: crawler_search_knowledge
  │   ├─ Arguments: {"query": "FastAPI", "top_k": 5}
  │   ├─ Tool execution via MCP
  │   └─ Result streamed back to LLM
  │
  ├─ Turn 2:
  │   ├─ LLM receives search results
  │   ├─ Generates summary (no more tools needed)
  │   └─ Streams response to user
  │
  └─ Complete (budget exhausted or LLM finished)
```

### Example 3: Multi-Turn Tag Switching

```
Turn 1:
User: "[[research_deeply]] Tell me about Python async"
robaiproxy: Routes to deep research (4 iterations)
  ↓
Turn 2:
User: "[[autonomous]] Now create a test file"
robaiproxy: Routes to autonomous mode (last message tag wins!)
  ↓
Turn 3:
User: "Can you explain that code?"
robaiproxy: Routes to auto mode (no tag, falls back to agentic detection)
```

---

## Research Modes

### Standard Research (2 Iterations)

**Triggered by:**
- `[[research_request]]` tag
- Agentic detection with research keywords

**Iteration Pattern:**
```
Initial Query → Serper (10 results)
  ↓
Iteration 1: Focus on main concepts
  ├─ Serper search (5 results)
  ├─ RAG search (3-6 results)
  ├─ Crawl URLs (3 URLs)
  └─ Accumulate context
  ↓
Iteration 2: Focus on practical implementation
  ├─ Serper search (5 results)
  ├─ RAG search (3-6 results)
  ├─ Crawl URLs (3 URLs)
  └─ Accumulate context
  ↓
Generate final answer (full context, no truncation)
```

**Context Accumulation:**
- All results from all iterations preserved
- No truncation between iterations
- Final context can exceed 80K+ characters
- LLM receives complete research history

### Deep Research (4 Iterations)

**Triggered by:**
- `[[research_deeply]]` tag
- Agentic detection with modifiers: "thoroughly", "carefully", "comprehensive", "deep", "detailed"

**Iteration Pattern:**
```
Iteration 1: Main concepts
Iteration 2: Practical implementation
Iteration 3: Advanced features
Iteration 4: Ecosystem exploration
  ↓
Auto-retry: If context overflow, reduces to 2 iterations
```

**Configuration:**
```bash
MAX_DEEP_RESEARCH=1  # Max concurrent deep research requests
```

### Autonomous Mode

**Triggered by:**
- `[[autonomous]]` tag

**Features:**
- Budget: 6 points default (configurable)
- Max turns: 3
- Tool discovery: Automatic from robaimodeltools
- Streaming: Real-time tool execution updates

**Tool Budget:**
```bash
ROBAIMULTITURN_AGENTIC_TOOL_BUDGET=4  # Points per iteration
```

**Execution:**
1. LLM receives tool definitions
2. LLM decides which tools to call (via OpenAI function calling format)
3. Tools execute via MCP
4. Results streamed back to LLM
5. Process repeats until budget exhausted or LLM completes

### Autonomous Plus Mode

**Triggered by:**
- `[[autonomous_plus]]` tag

**Features:**
- LLM classifier determines: Research or Autonomous?
- Classifier prompt: "RESEARCH or AUTONOMOUS?"
- Routes to appropriate mode based on classification

**Classifier Endpoint:**
```
POST http://localhost:8092/classify (if enabled)
```

**Fallback:**
- If classifier unavailable, defaults to autonomous mode

---

## Installation & Setup

### Prerequisites

- **OS:** Linux (Ubuntu 20.04+ recommended)
- **Docker:** 20.10+
- **Docker Compose:** 2.0+
- **Python:** 3.9+
- **Git:** For cloning repositories
- **RAM:** 32GB minimum (Neo4j + vLLM + in-memory DB)
- **Disk:** 50GB+ for models and data

### Clone Repository

```bash
cd ~/Documents
git clone <repository-url> robaitools
cd robaitools

# Initialize submodules
git submodule update --init --recursive
```

### Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit configuration
nano .env
```

**Required Environment Variables:**

```bash
# API Keys (REQUIRED)
OPENAI_API_KEY=your-openai-compatible-key
SERPER_API_KEY=your-serper-api-key

# Service URLs
CRAWL4AI_URL=http://localhost:11235
KG_SERVICE_URL=http://localhost:8088
VLLM_BASE_URL=http://localhost:8078  # If using vLLM

# Database
DB_PATH=./robaidata/crawl4ai_rag.db
USE_MEMORY_DB=true

# Neo4j
NEO4J_PASSWORD=knowledge_graph_2024
NEO4J_HEAP_MAX_SIZE=16G
```

### Build Docker Images

```bash
# Build all services
docker compose build

# Or build specific services
docker compose build robairagapi
docker compose build robaitragmcp
docker compose build open-webui
```

### Start Services

```bash
# Start all Docker services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f
```

**Services start in dependency order:**
1. crawl4ai
2. neo4j
3. kg-service
4. robaitragmcp
5. robairagapi
6. open-webui

### Start robaiproxy (Manual)

```bash
# Create virtual environment (if needed)
python3 -m venv robaivenv
source robaivenv/bin/activate

# Install dependencies
cd robaiproxy
pip install -r requirements.txt

# Start proxy
uvicorn requestProxy:app --host 0.0.0.0 --port 8079 --reload
```

### Verify Installation

```bash
# Check robaiproxy health
curl http://localhost:8079/health

# Check individual services
curl http://localhost:11235/health      # crawl4ai
curl http://localhost:8088/health       # kg-service
curl http://localhost:8081/api/v1/status # robairagapi
curl http://localhost:7474              # neo4j browser
```

### Access Web UI

Open browser to: `http://localhost` or `http://192.168.10.50` (LAN IP)

---

## Configuration

### Centralized Configuration (.env)

All services use the `.env` file in the repository root.

**Configuration Precedence:**
1. Master `docker-compose.yml` environment block (highest)
2. `.env` file in repo root
3. Child service `docker-compose.yml`
4. Dockerfile ENV statements
5. Code defaults (lowest)

### Key Configuration Sections

#### Database Configuration

```bash
# Disk-only mode (simpler, traditional)
USE_MEMORY_DB=false
DB_PATH=./robaidata/crawl4ai_rag.db

# RAM mode with differential sync (faster, production)
USE_MEMORY_DB=true
DB_PATH=./robaidata/crawl4ai_rag.db
DB_BUSY_TIMEOUT=5000
```

**RAM Mode Benefits:**
- ~10x faster read/write operations
- Differential sync (only changed records)
- Composite trigger: idle (5s) + periodic (5m)

#### Research Configuration

```bash
# Research concurrency limits
MAX_STANDARD_RESEARCH=3
MAX_DEEP_RESEARCH=1

# Tool budgets
ROBAIMULTITURN_TOOL_BUDGET=3
ROBAIMULTITURN_RESEARCH_TOOL_BUDGET=6
ROBAIMULTITURN_AGENTIC_TOOL_BUDGET=4

# Duplicate detection
ROBAIMULTITURN_DUPLICATE_THRESHOLD=0.7

# Deep research memory limit
ROBAIMULTITURN_DEEP_MEMORY_LIMIT=4
```

#### Security Configuration

```bash
# RAG API authentication
OPENAI_API_KEY=your-key-here
OPENAI_API_KEY_2=secondary-key

# Rate limiting
RATE_LIMIT_PER_MINUTE=120
ENABLE_RATE_LIMIT=true

# pfSense firewall (for public proxy)
PFSENSE_IP=192.168.10.1
PFSENSE_MAC=58:9c:fc:10:ff:d8
TRUSTED_LAN_SUBNET=192.168.10.0/24
STRICT_AUTH_FOR_PFSENSE=true
```

#### Model Configuration

```bash
# vLLM (if using)
VLLM_BASE_URL=http://localhost:8078
VLLM_TIMEOUT=1800
VLLM_MAX_TOKENS=262144
VLLM_TEMPERATURE=0.7

# KG Service models
EXTRACTOR_MODEL_URL=http://localhost:8079  # Proxy (GPU power mgmt)
AUGMENT_LLM_URL=http://localhost:8078      # Direct vLLM
RESEARCH_MODEL_URL=http://localhost:8078   # Research agent
```

#### Neo4j Configuration

```bash
NEO4J_USER=neo4j
NEO4J_PASSWORD=knowledge_graph_2024
NEO4J_URI=bolt://localhost:7687
NEO4J_HEAP_INITIAL_SIZE=512m
NEO4J_HEAP_MAX_SIZE=16G
NEO4J_PAGECACHE_SIZE=2G
NEO4J_PLUGINS=["apoc"]
```

### Service-Specific Configuration Files

- `robaiproxy/.env` - Proxy overrides (if needed)
- `robaikg/kg-service/.env` - KG service config
- `robaiwebui/open-webui/.env` - WebUI config

---

## Usage

### Using the Web UI

1. **Access:** Open browser to `http://localhost`
2. **Research Mode:** Click flask icon (next to integration menu)
3. **Send Request:** Type query and send
4. **Monitor:** Watch real-time status updates

**Research Mode Button:**
- **Inactive:** Gray, transparent border
- **Active:** Cornflower blue text + border
- **Effect:** Adds `<research_request>` tag to message

### Using Tags Directly

```
User: "[[research_request]] Tell me about FastAPI"
→ Triggers 2-iteration standard research

User: "[[research_deeply]] Comprehensive guide to async Python"
→ Triggers 4-iteration deep research

User: "[[autonomous]] Search memory for Python docs and list key topics"
→ Triggers autonomous tool execution

User: "[[autonomous_plus]] Should I research or just answer about FastAPI?"
→ LLM classifier decides: research or autonomous

User: "[[pure_llm]] Just answer quickly: what is FastAPI?"
→ Direct LLM passthrough (no RAG/research/tools)
```

### Using the REST API

```bash
# Search knowledge base
curl -X POST http://localhost:8081/api/v1/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "query": "FastAPI tutorial",
    "top_k": 10,
    "tags": "python"
  }'

# Crawl and store
curl -X POST http://localhost:8081/api/v1/crawl \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "url": "https://fastapi.tiangolo.com",
    "retention_policy": "permanent",
    "tags": "fastapi, documentation"
  }'

# Deep crawl
curl -X POST http://localhost:8081/api/v1/deep_crawl \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "starting_url": "https://fastapi.tiangolo.com",
    "max_depth": 3,
    "max_pages": 50,
    "retention_policy": "30_days",
    "tags": "fastapi"
  }'

# List domains
curl http://localhost:8081/api/v1/domains \
  -H "Authorization: Bearer your-api-key"

# Block domain
curl -X POST http://localhost:8081/api/v1/domains/block \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{"pattern": "*.ru"}'
```

### Using via robaiproxy

```bash
# Research request (via proxy)
curl -X POST http://localhost:8079/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen3-30B",
    "messages": [
      {"role": "user", "content": "[[research_deeply]] Python async best practices"}
    ],
    "stream": true
  }'

# Autonomous request
curl -X POST http://localhost:8079/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen3-30B",
    "messages": [
      {"role": "user", "content": "[[autonomous]] Search memory for FastAPI and summarize"}
    ],
    "stream": true
  }'
```

### Python Client Example

```python
import requests

# Research mode
response = requests.post(
    "http://localhost:8079/v1/chat/completions",
    json={
        "model": "Qwen3-30B",
        "messages": [
            {"role": "user", "content": "[[research_request]] Tell me about FastAPI"}
        ],
        "stream": False
    }
)

# Autonomous mode
response = requests.post(
    "http://localhost:8079/v1/chat/completions",
    json={
        "model": "Qwen3-30B",
        "messages": [
            {"role": "user", "content": "[[autonomous]] Search for Python async docs"}
        ],
        "stream": True
    }
)

# Stream response
for line in response.iter_lines():
    if line:
        print(line.decode())
```

---

## Development

### Project Structure

```
robaitools/
├── .env                        # Centralized configuration
├── docker-compose.yml          # Master orchestration
├── CLAUDE.md                   # Developer guide for Claude Code
├── SERVICE_MAPPING.md          # Service name mapping
├── CONFIGURATION.md            # Configuration documentation
│
├── robaiproxy/                 # API Gateway (NON-DOCKER)
│   ├── requestProxy.py         # Main routing logic
│   ├── config.py               # Configuration
│   ├── powerManager.py         # GPU power management
│   └── requirements.txt
│
├── robaimultiturn/             # Research orchestration (Python package)
│   ├── research/               # Research loop implementation
│   ├── tool_loop.py            # Autonomous tool execution
│   └── common/streaming.py     # SSE status events
│
├── robaimodeltools/            # Shared RAG library (Python package)
│   ├── data/                   # Database layer
│   ├── operations/             # Orchestration layer
│   ├── search/                 # 5-phase RAG pipeline
│   └── taxonomy/               # Entity definitions
│
├── robairagapi/                # REST API Bridge (Docker)
│   ├── api/                    # FastAPI endpoints
│   └── docker-compose.yml
│
├── robaitragmcp/               # MCP Server (Docker)
│   ├── core/                   # MCP core logic
│   ├── discovery_engine.py     # Tool discovery
│   └── docker-compose.yml
│
├── robaikg/                    # Knowledge Graph (Docker)
│   ├── kg-service/             # Entity extraction service
│   ├── neo4j/                  # Neo4j database
│   └── docker-compose.yml
│
├── robaicrawler/               # Crawl4AI (Docker)
│   └── docker-compose.yml
│
├── robaiwebui/                 # Open WebUI (Docker)
│   ├── open-webui/             # WebUI source
│   └── researchmode.md         # Research button implementation
│
└── robaidata/                  # Shared data volume
    └── crawl4ai_rag.db         # SQLite database
```

### Adding New Features

#### Adding a New RAG Operation

1. **Add function to robaimodeltools:**

```python
# robaimodeltools/operations/my_module.py
def my_new_function(param1: str, param2: int = 10) -> dict:
    """This becomes an MCP tool automatically!"""
    return {"result": f"{param1} * {param2}"}
```

2. **Function auto-discovered as MCP tool:**
   - Tool name: `my_module_my_new_function`
   - No changes needed to robaitragmcp!

3. **Add to Crawl4AIRAG facade (optional):**

```python
# robaimodeltools/operations/crawler.py
def my_new_function(self, param1, param2=10):
    return my_module.my_new_function(param1, param2)
```

4. **Use in REST API (optional):**

```python
# robairagapi/api/server.py
@app.post("/api/v1/my-endpoint")
async def my_endpoint(param1: str, param2: int = 10):
    result = rag_system.my_new_function(param1, param2)
    return {"success": True, "data": result}
```

#### Adding a New Routing Mode

1. **Add tag detection function:**

```python
# robaiproxy/requestProxy.py
def has_my_mode_tag(last_user_msg: str) -> bool:
    return "[[my_mode]]" in last_user_msg.lower()
```

2. **Update detect_request_mode:**

```python
def detect_request_mode(last_user_msg: str) -> tuple[str, str]:
    if has_pure_llm_tag(last_user_msg):
        return ("pure_llm", "Explicit [[pure_llm]] tag")
    if has_my_mode_tag(last_user_msg):  # Add here
        return ("my_mode", "Explicit [[my_mode]] tag")
    # ... rest of detection
```

3. **Add routing logic:**

```python
# In autonomous_chat function
if mode == "my_mode":
    # Your custom routing logic
    return StreamingResponse(...)
```

4. **Update strip_routing_tags:**

```python
routing_tags = [
    r'\[\[research_request\]\]',
    r'\[\[my_mode\]\]',  # Add here
    # ... rest
]
```

### Testing

#### Health Checks

```bash
# Check all services
curl http://localhost:8079/health       # robaiproxy
curl http://localhost:8081/api/v1/status # robairagapi
curl http://localhost:11235/health      # crawl4ai
curl http://localhost:8088/health       # kg-service
curl http://localhost:7474              # neo4j browser
```

#### Test Research Mode

```bash
# Standard research
curl -X POST http://localhost:8079/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen3-30B",
    "messages": [
      {"role": "user", "content": "[[research_request]] test query"}
    ],
    "stream": true
  }'
```

#### Test Autonomous Mode

```bash
# Check tool discovery
cd robaitragmcp
source ../robaivenv/bin/activate
python3 -c "
from core.discovery_engine import DiscoveryEngine
engine = DiscoveryEngine()
tools = engine.discover_all_tools()
print(f'Discovered {len(tools)} tools')
for name in tools.keys():
    print(f'  - {name}')
"
```

#### Database Tests

```bash
# Check database stats
cd robaimodeltools
python utilities/dbstats.py

# Dump database contents
cd robaimodeltools/data
python dbDump.py
```

### Debugging

#### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f robaitragmcp
docker compose logs -f kg-service

# robaiproxy (non-Docker)
cd robaiproxy
tail -f proxy.log
```

#### Common Issues

**Service won't start:**
```bash
# Check logs
docker compose logs service-name

# Restart service
docker compose restart service-name

# Full restart
docker compose down
docker compose up -d
```

**Database issues:**
```bash
# Check database file
ls -lh robaidata/crawl4ai_rag.db

# Check sync status (if RAM mode)
# Look for sync metrics in logs

# Reset database (WARNING: deletes all data)
rm robaidata/crawl4ai_rag.db
docker compose restart robaitragmcp
```

**MCP tool discovery fails:**
```bash
# Check if robaimodeltools is accessible
docker compose exec robaitragmcp python3 -c "import robaimodeltools; print('OK')"

# Force rediscovery
docker compose restart robaitragmcp
```

---

## Troubleshooting

### Context Overflow Detected

**Symptom:** Research mode logs "Context overflow detected"

**Solution:**
- System automatically retries with reduced iterations (4→2)
- If still failing, check vLLM context window size
- Consider reducing max_pages in deep crawl

### Service Name Not Found

**Symptom:** `docker compose` can't find service

**Solution:**
- Use master service names from master `docker-compose.yml`
- Check `SERVICE_MAPPING.md` for correct names
- Examples:
  - ✅ `robaitragmcp` (correct)
  - ❌ `mcp-server` (wrong)

### Volume Not Found

**Symptom:** Docker complains about missing volume

**Solution:**
- Named volumes must be declared in master `docker-compose.yml`
- Check volumes section at bottom of file
- Use `docker volume ls` to list volumes

### Import Errors in robaimodeltools

**Symptom:** Python can't import robaimodeltools

**Solution:**
```bash
# Verify PYTHONPATH includes repo root
export PYTHONPATH=/home/robiloo/Documents/robaitools:$PYTHONPATH

# Test import
python3 -c "from robaimodeltools.operations.crawler import Crawl4AIRAG; print('OK')"
```

### Neo4j Connection Refused

**Symptom:** kg-service can't connect to Neo4j

**Solution:**
```bash
# Check Neo4j is running
docker compose ps neo4j

# Verify port 7687 is accessible
curl http://localhost:7474

# Check credentials in .env
NEO4J_USER=neo4j
NEO4J_PASSWORD=knowledge_graph_2024
```

### robaiproxy Won't Start

**Symptom:** uvicorn crashes on startup

**Solution:**
```bash
# Activate virtual environment
source robaivenv/bin/activate

# Install dependencies
cd robaiproxy
pip install -r requirements.txt

# Check Python version
python --version  # Should be 3.9+

# Start with debug logging
uvicorn requestProxy:app --host 0.0.0.0 --port 8079 --reload --log-level debug
```

### Tags Not Working in Multi-Turn

**Symptom:** Old tags override new tags in conversations

**Solution:**
- This was fixed in the latest version
- Tags are now checked in the **last user message only** (except "You are Cline")
- Restart robaiproxy to apply fix

### GPU Power Management Errors

**Symptom:** `sudo: a terminal is required to read the password`

**Solution:**
```bash
# Add passwordless sudo for rocm-smi
sudo visudo

# Add this line (replace username):
username ALL=(ALL) NOPASSWD: /usr/bin/rocm-smi

# Or disable power management in config.py
ENABLE_POWER_MANAGEMENT = False
```

---

## Performance Notes

### Typical Latencies

- **Vector search**: 50-100ms
- **Hybrid search** (vector + graph): 150-250ms
- **Full 5-phase pipeline**: 200-350ms
- **Crawl & store**: 500-1500ms (depends on page size)
- **Deep crawl** (50 pages): 30-60s (with rate limiting)
- **RAM mode DB**: ~10x faster than disk mode

### Throughput (Concurrent Requests)

- **Search**: ~100 queries/second
- **Crawl & store**: ~20 pages/second (limited by Crawl4AI)
- **Database ops**: ~1000 reads/sec, ~500 writes/sec

### Scaling Recommendations

**Horizontal Scaling:**
- Multiple robaiproxy instances (load balancer)
- Multiple robairagapi instances (shared database)
- Scale Crawl4AI for higher crawl throughput

**Vertical Scaling:**
- More RAM for larger in-memory database
- Faster CPU for embedding generation
- Faster SSD for disk sync

---

## Documentation

- **[CLAUDE.md](CLAUDE.md)** - Developer guide for Claude Code
- **[SERVICE_MAPPING.md](SERVICE_MAPPING.md)** - Service name reference
- **[CONFIGURATION.md](CONFIGURATION.md)** - Configuration guide
- **[robaimultiturn/__init__.py](robaimultiturn/__init__.py)** - Research API reference
- **[robaimodeltools/README.md](robaimodeltools/README.md)** - RAG library documentation
- **[robaiwebui/researchmode.md](robaiwebui/researchmode.md)** - Research button implementation

---

## License

[Include license information here]

---

## Contact

For issues, questions, or contributions, please contact [maintainer contact info].

---

**Last Updated:** 2025-11-18
**Version:** 2.0.0
