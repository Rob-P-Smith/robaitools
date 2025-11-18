---
layout: default
title: robaitragmcp
nav_order: 6
has_children: true
---

# robaitragmcp

**Zero-Hardcoded-Tools MCP Server with Dynamic Tool Discovery**

A Model Context Protocol (MCP) server that dynamically discovers and exposes all robaimodeltools functions to AI assistants via stdio protocol. NO hardcoded tools - everything is discovered automatically through Python introspection.

## Overview

robaitragmcp is a standalone microservice providing AI assistants (Claude Desktop, LM-Studio, etc.) with direct access to the robaitools RAG system through MCP protocol. The key innovation: **automatic tool discovery** eliminates manual tool definitions.

### What It Does

**Dynamic Tool Discovery:**
- Automatically finds all public methods from robaimodeltools
- Creates MCP tool definitions on the fly
- Updates tool registry when containers restart
- Zero maintenance for new functions

**AI Assistant Integration:**
- JSON-RPC 2.0 over stdio protocol
- Direct Python function calls (no HTTP overhead)
- Graceful error handling and timeouts
- Detailed action logging

**Crawling & Indexing:**
- Web content extraction via Crawl4AI
- Automatic chunking and embedding generation
- Deep crawling with configurable limits
- Domain blocking for security

**Semantic Search:**
- Fast vector similarity via SQLite + sqlite-vec
- Optional Knowledge Graph enhancement
- Multi-signal ranking (5 signals)
- Tag-based filtering

## Key Innovation: Zero Hardcoded Tools

**Traditional MCP servers** require manual tool definitions:
```python
# ❌ Old way - manual maintenance required
TOOLS = [
    {"name": "crawl_url", "description": "...", "inputSchema": {...}},
    {"name": "search", "description": "...", "inputSchema": {...}},
    # ... 50+ tool definitions to maintain manually
]
```

**robaitragmcp** uses automatic discovery:
```python
# ✅ New way - zero maintenance
discovered_tools = discovery_engine.discover_all_tools()
# Automatically finds ALL public methods from:
#   - Crawl4AIRAG class → crawler_* tools
#   - SearchHandler class → search_handler_* tools
#   - Any new functions added → automatically available
```

**Benefits:**
- **No maintenance:** Add functions to robaimodeltools, they automatically become MCP tools
- **No duplication:** Single source of truth (robaimodeltools)
- **Always in sync:** Tool definitions match implementation
- **Auto-updates:** Container restarts refresh tool registry

## Architecture

```
AI Assistant (Claude Desktop / LM-Studio)
    ↓ JSON-RPC 2.0 over stdio
┌────────────────────────────────────────────┐
│ MCP Server (robaitragmcp)                 │
│ ┌──────────────┐  ┌───────────────────┐  │
│ │ Discovery    │→ │ Wrapper Factory   │  │
│ │ Engine       │  │ (creates tools)   │  │
│ └──────────────┘  └───────────────────┘  │
│ ┌──────────────────────────────────────┐  │
│ │ Health Monitor                       │  │
│ │ - Detects container restarts         │  │
│ │ - Refreshes tool registry            │  │
│ └──────────────────────────────────────┘  │
│ ┌──────────────────────────────────────┐  │
│ │ Protocol Handler (JSON-RPC)          │  │
│ │ - initialize, tools/list, tools/call │  │
│ └──────────────────────────────────────┘  │
└──────────────┬─────────────────────────────┘
               │ Direct Python imports
┌──────────────▼─────────────────────────────┐
│ robaimodeltools                            │
│ - Crawl4AIRAG (crawling, indexing)        │
│ - SearchHandler (search operations)        │
│ - All other modules                        │
└────────────────────────────────────────────┘
```

## Components

### Core Modules

**core/mcp_server.py** (Main Entry Point)
- Implements MCP JSON-RPC 2.0 protocol
- Handles initialize, tools/list, tools/call messages
- Manages server lifecycle and state
- Coordinates discovery and health monitoring

**core/discovery_engine.py** (Dynamic Discovery)
- Introspects robaimodeltools modules
- Finds all public methods via Python inspect
- Generates MCP tool schemas automatically
- Handles graceful degradation if modules unavailable

**core/wrapper_factory.py** (Tool Wrapping)
- Creates DynamicMCPTool instances
- Wraps discovered functions for MCP protocol
- Handles parameter validation and type conversion
- Implements timeout enforcement (60s default)

**core/protocol_handler.py** (JSON-RPC)
- Parses JSON-RPC 2.0 messages
- Validates request/response format
- Generates proper error codes
- Ensures protocol compliance

**core/health_monitor.py** (Health Monitoring)
- Detects container restarts (via timestamp file)
- Triggers tool registry refresh on restart
- Runs periodic health checks (30s default)
- Calls restart callback when needed

### Utilities

**utils/mcp_logger.py** (Action Logging)
- Dedicated MCP action log (/tmp/robaimcp.log)
- Logs all tool calls with parameters
- Truncates large outputs for readability
- Configurable log levels

**utils/introspection.py** (Function Analysis)
- Extracts function signatures
- Parses docstrings for descriptions
- Generates JSON schema for parameters
- Identifies public vs private methods

## Discovered Tools

Tools are automatically discovered from robaimodeltools. Typical tools include:

**Crawler Tools** (`crawler_*`):
- `crawler_crawl_url` - Crawl single URL
- `crawler_crawl_urls_batch` - Crawl multiple URLs
- `crawler_deep_crawl` - Recursive crawling
- `crawler_search_knowledge` - Search knowledge base
- `crawler_add_blocked_domain` - Block domain patterns
- `crawler_remove_blocked_domain` - Unblock domains
- Plus ~10 more methods from Crawl4AIRAG class

**Search Tools** (`search_handler_*`):
- `search_handler_search` - Semantic search
- `search_handler_hybrid_search` - Vector + graph search
- Plus other SearchHandler methods

**Dynamic Updates:**
- New methods in robaimodeltools automatically appear as tools
- No code changes needed in robaitragmcp
- Tool count varies based on robaimodeltools version

## Communication Protocol

**MCP uses JSON-RPC 2.0 over stdio:**

**Initialize:**
```json
// Client → Server
{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
  "protocolVersion": "0.1.0",
  "clientInfo": {"name": "Claude Desktop"}
}}

// Server → Client
{"jsonrpc": "2.0", "id": 1, "result": {
  "protocolVersion": "0.1.0",
  "serverInfo": {"name": "robai-mcp-server", "version": "1.0.0"},
  "capabilities": {"tools": {}}
}}
```

**List Tools:**
```json
// Client → Server
{"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}

// Server → Client (returns ALL discovered tools)
{"jsonrpc": "2.0", "id": 2, "result": {
  "tools": [
    {
      "name": "crawler_crawl_url",
      "description": "Crawl a single URL and extract content",
      "inputSchema": {
        "type": "object",
        "properties": {
          "url": {"type": "string", "description": "URL to crawl"},
          "tags": {"type": "string", "description": "Comma-separated tags"},
          "retention_policy": {"type": "string", "description": "permanent/session/days30"}
        },
        "required": ["url"]
      }
    }
    // ... all other discovered tools
  ]
}}
```

**Call Tool:**
```json
// Client → Server
{"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
  "name": "crawler_crawl_url",
  "arguments": {"url": "https://docs.python.org", "tags": "python,docs"}
}}

// Server → Client (after executing function)
{"jsonrpc": "2.0", "id": 3, "result": {
  "content": [
    {"type": "text", "text": "Successfully crawled URL and stored 15 chunks"}
  ]
}}
```

## Integration Points

### AI Assistants

**Claude Desktop:**
- Configure in `claude_desktop_config.json`
- Uses stdio transport
- Tools appear automatically in Claude UI

**LM-Studio:**
- Configure in MCP settings
- Local model + robaitools RAG
- Direct function execution

### Backend Services

**Depends On:**
- robaimodeltools (shared library, direct import)
- Optional: Crawl4AI service (port 11235)
- Optional: KG service (port 8088)
- Optional: Neo4j (port 7687)

**Used By:**
- robairagapi (wraps MCP tools as REST API)
- AI assistants (direct MCP protocol)

## Statistics

**Codebase:**
- Main server: ~500 lines (mcp_server.py)
- Discovery engine: ~200 lines (discovery_engine.py)
- Total: ~1,500 lines across all modules
- Discovers: 20-30 tools (varies by robaimodeltools version)

**Performance:**
- Tool discovery: < 1 second at startup
- Tool call overhead: < 10ms
- Timeout enforcement: 60 seconds (configurable)
- Health check interval: 30 seconds (configurable)

**Reliability:**
- Graceful degradation if robaimodeltools unavailable
- Auto-recovery on container restarts
- Error isolation (tool failures don't crash server)
- Detailed logging for troubleshooting

## Quick Start

### Docker Deployment (Recommended)

```bash
cd /home/robiloo/Documents/robaitools
docker compose up -d robaitragmcp
```

### Local Development

```bash
cd robaitragmcp
python3 -u core/mcp_server.py
```

### Test with Echo

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | \
  python3 -u core/mcp_server.py
```

## Configuration

**Environment Variables:**
- `DISCOVERY_INTERVAL`: Seconds between health checks (default: 30)
- `CRAWL4AI_URL`: Crawl4AI service URL (default: http://localhost:11235)
- `USE_MEMORY_DB`: RAM mode for SQLite (default: true)
- `LOG_LEVEL`: Logging verbosity (default: INFO)

**File Locations:**
- Main log: `/tmp/robaimcp.log`
- Health timestamp: `/tmp/mcp_start_time.txt`
- Database: `/data/crawl4ai_rag.db` (via robaimodeltools)

## Use Cases

**AI-Powered Research:**
- Claude crawls documentation automatically
- Builds searchable knowledge base
- Answers questions with citations
- Discovers related concepts via KG

**Knowledge Management:**
- Organize content with tags
- Manage retention policies
- Track content updates
- Power chatbots with current info

**Development Workflow:**
- Local LLM + robaitools integration
- Direct function access (no HTTP)
- Real-time tool updates
- Debugging with detailed logs

## Related Components

**Upstream:**
- robaimodeltools - Core RAG logic (direct import)
- Crawl4AI - Web content extraction (HTTP)
- Neo4j - Knowledge graph (Bolt protocol)

**Downstream:**
- robairagapi - REST API wrapper (uses same tools)
- AI assistants - MCP protocol clients

**Shared:**
- robaidata - SQLite database (file access)
- Taxonomy - Entity type definitions (file access)

## Next Steps

1. **Getting Started:** See [Getting Started](getting-started.md) for installation and setup
2. **Configuration:** Review [Configuration](configuration.md) for environment variables
3. **Architecture:** Check [Architecture](architecture.md) for technical deep dive
4. **API Reference:** Browse [API Reference](api-reference.md) for discovered tools

## Advantages Over Manual Tool Definitions

**Development Speed:**
- Add function to robaimodeltools → automatically available as tool
- No manual schema writing
- No synchronization overhead

**Maintenance:**
- Single source of truth
- No duplicate definitions
- Auto-updates on restart

**Reliability:**
- Schema matches implementation
- Type safety from function signatures
- Automated documentation from docstrings

**Flexibility:**
- Works with any robaimodeltools version
- Gracefully handles missing modules
- Scales to hundreds of tools effortlessly
