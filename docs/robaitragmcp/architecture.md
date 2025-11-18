---
layout: default
title: Architecture
parent: robaitragmcp
nav_order: 4
---

# Architecture

Technical deep-dive into robaitragmcp's dynamic tool discovery and TCP-based MCP server.

## System Overview

robaitragmcp is a **TCP server** (port 3000) implementing MCP protocol via JSON-RPC 2.0. Key innovation: **zero hardcoded tools** - everything discovered dynamically from robaimodeltools.

```
┌─────────────────────────────────────────┐
│  MCP Clients (AI Assistants/robairagapi)│
│  Connect via TCP to localhost:3000      │
└──────────────┬──────────────────────────┘
               │ JSON-RPC 2.0 (newline-delimited)
┌──────────────▼──────────────────────────┐
│  MCPServer (core/mcp_server.py)         │
│  ┌───────────────────────────────────┐  │
│  │ TCP Server (asyncio.start_server) │  │
│  │ Port: 3000 (MCP_TCP_PORT)         │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │ DiscoveryEngine                   │  │
│  │ - Introspects robaimodeltools     │  │
│  │ - Finds Crawl4AIRAG methods       │  │
│  │ - Finds SearchHandler methods     │  │
│  │ - Creates tool definitions        │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │ WrapperFactory                    │  │
│  │ - Creates DynamicMCPTool wrappers │  │
│  │ - Handles type conversion         │  │
│  │ - Enforces 60s timeout            │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │ HealthMonitor                     │  │
│  │ - Monitors 4 Docker containers    │  │
│  │ - Detects restarts (every 30s)    │  │
│  │ - Triggers tool refresh           │  │
│  └───────────────────────────────────┘  │
└──────────────┬──────────────────────────┘
               │ Direct Python imports
┌──────────────▼──────────────────────────┐
│  robaimodeltools                        │
│  - Crawl4AIRAG (~15 methods)            │
│  - SearchHandler (~5 methods)           │
│  - All methods become tools             │
└─────────────────────────────────────────┘
```

## Core Components

### MCPServer (mcp_server.py)

Main server coordinating all components.

**Startup:**
1. Create server instance → Initialize components
2. Discover tools → Store in self.tools dict
3. Start health monitor → Monitor Docker containers
4. Start TCP server → Listen on port 3000
5. Ready → Log "✅ MCP Server listening"

**Request Handling:**
- Client connects → handle_connection()
- Read newline-delimited JSON → parse message
- validate_request() → (method, params, id)
- Route to handler (initialize/tools/list/tools/call)
- Execute and return response → Send JSON + "\n"

### DiscoveryEngine (discovery_engine.py)

Dynamically discovers tools from robaimodeltools.

**Process:**
- Import robaimodeltools (graceful fail if unavailable)
- Discover from Crawl4AIRAG class → crawler_* tools
- Discover from SearchHandler class → search_handler_* tools
- Use inspect.getmembers() to find public methods
- Extract function info (signature, docstring, params)
- Create tool definitions with JSON schema

### WrapperFactory (wrapper_factory.py)

Creates executable MCP tool wrappers.

**DynamicMCPTool:**
- Stores tool metadata (name, signature, docstring)
- Generates JSON schema from function signature
- execute(arguments) with 60s timeout enforcement
- Handles sync/async functions with asyncio.wait_for
- Returns MCP-compliant format: {content: [...], isError: bool}

### HealthMonitor (health_monitor.py)

Monitors Docker containers and triggers tool refresh.

**Monitored:** robaicrawler, robaineo4j, robaikg, robairagapi

**Process:**
- Every 30s: Check container StartedAt timestamps
- Compare with stored times → Detect restarts
- On restart: Trigger _refresh_tools()
- Re-discover and replace self.tools dict
- Graceful handling if Docker unavailable

## Data Flow

**Complete Request:**
1. Client connects TCP port 3000
2. Send initialize → Get capabilities
3. Send tools/list → Get all tools
4. Send tools/call → Execute tool → Get result
5. Connection stays open for multiple requests

**Tool Execution:**
- tools/call → MCPServer.call_tool()
- Look up tool → DynamicMCPTool.execute()
- Type conversion → Execute with timeout
- Format result → Return to client

**Container Restart:**
- Container restarts → Health monitor detects
- Trigger callback → _refresh_tools()
- Re-discover → Replace tools → Continue serving

## Performance

- Tool discovery: ~1s at startup (25 tools)
- Tool call overhead: < 10ms
- Health check: Every 30s (~50ms)
- Timeout: 60s default (configurable)
- TCP: Multiple concurrent connections

## Design Decisions

**TCP vs stdio:** Allows multiple clients, easier testing
**Dynamic discovery:** Single source of truth, zero maintenance
**Health monitoring:** Auto-recovery on container restarts
**60s timeout:** Handles deep crawling, prevents hung connections

## Next Steps

- **Configuration:** See [Configuration](configuration.md)
- **API Reference:** Review [API Reference](api-reference.md)
