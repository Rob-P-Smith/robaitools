---
layout: default
title: robaiwebui
nav_order: 11
has_children: true
---

# robaiwebui

Web-based chat interface providing real-time LLM interactions with integrated research mode, autonomous tool execution, and knowledge graph-powered RAG capabilities.

## Overview

robaiwebui is a **customized deployment of Open WebUI** - an open-source, self-hosted chat interface for Large Language Models. It serves as the primary user-facing interface for the robaitools RAG system, providing a familiar ChatGPT-like experience with powerful backend integration.

**Key Capabilities:**
- **Multi-Model Chat** - Interactive conversations with model selection per chat
- **Research Mode** - 3-state button (Off/Research/Deep Research) for autonomous research
- **Real-Time Status** - Live progress updates via WebSocket during long-running operations
- **Tool Integration** - Transparent autonomous tool execution with visibility
- **Session Management** - Persistent chat history, user authentication, conversation context
- **Document Upload** - File attachment support with content extraction

## Architecture Position

robaiwebui sits at the **frontend tier** as the user-facing interface with zero downstream dependencies (only consumes services):

```
┌──────────────────────────────────────────┐
│  FRONTEND TIER (User Interface)          │
│  robaiwebui (Port 80) ← YOU ARE HERE     │
│  - Web-based chat interface              │
│  - Research mode UI                      │
│  - Real-time status display              │
└────────────────┬─────────────────────────┘
                 │ OpenAI-compatible API
                 │ http://192.168.10.50:8079/v1
                 ↓
┌──────────────────────────────────────────┐
│  GATEWAY TIER                            │
│  robaiproxy (Port 8079)                  │
│  - Request routing                       │
│  - Research orchestration                │
│  - Multi-turn conversations              │
└────────────────┬─────────────────────────┘
                 │
                 ↓
┌──────────────────────────────────────────┐
│  API TIER                                │
│  robairagapi + robaitragmcp              │
│  - RAG operations                        │
│  - Knowledge graph queries               │
│  - Tool discovery and execution          │
└──────────────────────────────────────────┘
```

**Communication Flow:** User → robaiwebui → robaiproxy → (robairagapi + robaitragmcp) → Backend services

## What's Inside

### Base Technology: Open WebUI

**Open WebUI** is a feature-rich, self-hosted web interface providing:
- ChatGPT-like chat interface built with Svelte
- Multi-user support with authentication
- Session management and chat history
- OpenAI-compatible API integration
- Model selection and management
- Document/knowledge base integration
- Voice input/output capabilities
- Code execution in chat

**Deployment:** Docker container at port 80 (external) / 8080 (internal)

### Custom Patches (3 Applied)

robaiwebui applies **three critical patches** to the base Open WebUI:

#### 1. Metadata Headers Patch
**Purpose:** Forward user context to backend LLM server

**Headers Added:**
- `X-OpenWebUI-User-Name` - Username for tracking
- `X-OpenWebUI-User-Id` - Unique user identifier
- `X-OpenWebUI-User-Email` - User email
- `X-OpenWebUI-User-Role` - User role (admin/user)
- `X-OpenWebUI-Chat-Id` - Current conversation ID

**Use Case:** Backend can track conversations, implement per-user rate limiting, maintain session context

**Status:** Always enabled (unless explicitly disabled)

#### 2. Metadata Preservation Patch
**Purpose:** Keep metadata in request body sent to backend

**Change:** Modified `routers/openai.py` to use `.get("metadata")` instead of `.pop("metadata")`

**Effect:** Full metadata object stays in JSON payload:
```json
{
  "messages": [...],
  "model": "Qwen3-30B",
  "metadata": {
    "user_id": "user_123",
    "chat_id": "chat_456",
    "session_id": "session_789",
    "filter_ids": [],
    "tool_ids": [],
    "files": [],
    "features": {},
    "variables": {}
  }
}
```

**Use Case:** Backend receives complete conversation context for intelligent processing

#### 3. Status Event Bridge Patch
**Purpose:** Route SSE status events to WebSocket for real-time UI updates

**How It Works:**
1. Open WebUI middleware intercepts SSE stream from backend
2. Detects JSON events with `type: "status"`
3. Extracts status data and emits via Socket.IO
4. Frontend receives via WebSocket and displays above message
5. Each new status replaces previous (not stacked)
6. Auto-clears when `done: true` received

**Use Case:** Display research progress ("Turn 1 - Searching...", "Turn 2 - Analyzing...") without interrupting message stream

### Frontend Customizations

#### Research Mode Button
**Location:** Message input toolbar (bottom of chat interface)

**Functionality:**
- **3-state button** (cycles with each click):
  1. **Disabled** (gray flask icon) - Normal chat mode
  2. **Research** (blue flask icon) - 2-iteration research mode
  3. **Deep Research** (darker blue flask icon) - 4-iteration research mode

**Implementation:**
- Adds prefix to user message before sending:
  - Research: `<research_request>\n{message}`
  - Deep Research: `<research_request_deep>\n{message}`
- Backend (robaiproxy) detects prefix and triggers research orchestration
- State persisted in sessionStorage (survives page refresh)
- Reset on Escape key press

**Visual Feedback:**
- Icon color indicates current state
- Tooltip shows mode description
- Accessible ARIA labels for screen readers

## Data Flow

Complete request-response cycle:

```
1. User types message and clicks send
   - Research mode prefix added if enabled
   - Message submitted via MessageInput.svelte
   ↓
2. Open WebUI backend receives message
   - Route: POST /api/openai/chat/completions
   - Adds user context headers (Patch 1)
   - Preserves metadata in body (Patch 2)
   - Forwards to OPENAI_API_BASE_URL
   ↓
3. robaiproxy processes request
   - Detects <research_request> prefix
   - If research: orchestrates multi-iteration research
   - Returns SSE stream with status + content events
   ↓
4. Open WebUI middleware intercepts stream (Patch 3)
   - Detects {"type":"status",...} events
   - Routes status to Socket.IO WebSocket
   - Forwards content events normally
   ↓
5. Frontend displays response
   - Status appears ABOVE message in real-time
   - Content streams into message box
   - Status auto-clears when done
   - Complete message saved to database
```

## Use Cases

**Standard Chat:**
- Ask questions about your knowledge base
- Get code examples and explanations
- Multi-turn conversations with context
- Model selection per conversation

**Research Mode:**
- Autonomous web research on any topic
- Multi-iteration information gathering
- Automatic source crawling and indexing
- Knowledge graph expansion
- Synthesized comprehensive answers

**Deep Research Mode:**
- Extended research with 4 iterations
- Thorough topic exploration
- Ecosystem analysis (tools, alternatives, advanced features)
- Practical implementation guidance

**Document Work:**
- Upload files for analysis
- Extract and index content
- Query uploaded documents
- Combine with knowledge base search

## Configuration

**Environment Variables:**
```bash
# Server Ports
WEBUI_EXTERNAL_PORT=80          # Host access port
WEBUI_INTERNAL_PORT=8080        # Container internal port

# Backend Integration
OPENAI_API_BASE_URL=http://192.168.10.50:8079/v1  # robaiproxy endpoint
OPENAI_API_KEY=sk-dummy-key                        # API authentication

# Metadata Forwarding
ENABLE_FORWARD_USER_INFO_HEADERS=True              # Enabled by default

# Security
WEBUI_SECRET_KEY=<auto-generated>                  # Session encryption
```

**Docker Volumes:**
- `open-webui_open-webui:/app/backend/data` - Chat history, user data, settings

## Quick Links

- [Getting Started](getting-started.md) - Installation and first chat
- [Architecture](architecture.md) - Patches, integration patterns, data flow
- [Configuration](configuration.md) - Environment variables and customization
- [API Reference](api-reference.md) - API endpoints, metadata structure, status events

## Technology Stack

**Frontend:**
- Svelte (component framework)
- JavaScript/TypeScript
- Tailwind CSS (styling)
- Socket.IO (WebSocket for real-time updates)

**Backend:**
- Python 3.11
- FastAPI (web framework)
- Uvicorn (ASGI server)
- SQLAlchemy (ORM)
- SQLite (data storage)

**Build:**
- Node.js (frontend build)
- Docker multi-stage build

## Resource Requirements

**Minimum:**
- Disk: 500MB (image + runtime data)
- Memory: 512MB
- CPU: 1 core

**Recommended:**
- Disk: 2GB (for growth)
- Memory: 1GB
- CPU: 2 cores

**Current Usage:**
- Docker image: ~400MB
- Runtime memory: ~300MB
- Persistent data: Grows with chat history

## Key Features

**Chat Interface:**
- Multi-model selection
- Streaming responses
- Code syntax highlighting
- Markdown rendering
- Message editing and regeneration

**Research Integration:**
- Visual research mode toggle
- Real-time status updates
- Multi-iteration progress tracking
- Autonomous tool execution visibility

**User Management:**
- Email/password authentication
- Role-based access (admin/user)
- Per-user chat history
- Session persistence

**Document Processing:**
- File upload support
- Content extraction
- Document indexing
- Query integration

## Related Components

**Upstream Dependencies:**
- robaiproxy - Request routing and research orchestration
- robairagapi - REST API bridge
- robaitragmcp - MCP server with tool discovery

**Backend Services:**
- crawl4ai - Web content crawling
- kg-service - Knowledge graph extraction
- neo4j - Graph database

**Shared Libraries:**
- robaimodeltools - Core RAG operations
- robaimultiturn - Multi-turn research orchestration

## Next Steps

1. **New Users:** Start with [Getting Started](getting-started.md) for installation
2. **Feature Exploration:** Try research mode and tool integration
3. **Customization:** Check [Configuration](configuration.md) for environment settings
4. **API Integration:** See [API Reference](api-reference.md) for endpoint documentation
5. **Advanced Usage:** Review [Architecture](architecture.md) for technical details
