---
layout: default
title: Architecture
parent: robaiwebui
nav_order: 4
---

# Architecture

Deep technical documentation on robaiwebui's custom patches, integration patterns, data flow, and implementation details.

## Design Overview

robaiwebui is built on **Open WebUI**, an open-source chat interface for LLMs, with **three critical custom patches** applied to enable:

1. **User Context Tracking** - Forward user/session metadata to backend via headers
2. **Metadata Preservation** - Keep complete metadata in request body for intelligent processing
3. **Real-Time Status Updates** - Route SSE status events to WebSocket for live UI feedback

**Base Technology:**
- **Open WebUI** - Self-hosted web interface (Svelte frontend + FastAPI backend)
- **Docker Deployment** - Multi-stage build with frontend and backend
- **Git Submodule** - Upstream Open WebUI in `robaiwebui/open-webui/` subdirectory

**Customization Approach:**
- Patch base Open WebUI via Dockerfile
- Modify frontend Svelte components for research mode button
- Add middleware for status event routing
- Preserve upstream compatibility (minimal invasive changes)

## Service Position in Stack

robaiwebui is the **frontend tier** - the only user-facing service:

```
┌─────────────────────────────────────────────────┐
│  TIER 1: USER INTERFACE                         │
│  robaiwebui (Port 80)                           │
│  ├─ Open WebUI Frontend (Svelte)                │
│  ├─ Open WebUI Backend (FastAPI)                │
│  └─ SQLite Database (chat history)              │
└─────────────────┬───────────────────────────────┘
                  │ HTTP/SSE
                  │ OPENAI_API_BASE_URL=http://192.168.10.50:8079/v1
                  ↓
┌─────────────────────────────────────────────────┐
│  TIER 2: GATEWAY / ORCHESTRATION                │
│  robaiproxy (Port 8079) [Non-Docker]            │
│  ├─ Request routing                             │
│  ├─ Research mode detection                     │
│  ├─ Multi-iteration orchestration               │
│  └─ Status event generation                     │
└─────────────────┬───────────────────────────────┘
                  │ HTTP
                  ↓
┌─────────────────────────────────────────────────┐
│  TIER 3: RAG SYSTEM                             │
│  robairagapi (Port 8081)                        │
│  robaitragmcp (Port 3000)                       │
│  ├─ Vector search                               │
│  ├─ Knowledge graph queries                     │
│  └─ Tool discovery/execution                    │
└─────────────────┬───────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────┐
│  TIER 4: DATA SERVICES                          │
│  crawl4ai, kg-service, neo4j                    │
└─────────────────────────────────────────────────┘
```

**Zero Downstream Dependencies:** robaiwebui only consumes services, no services depend on it

## Custom Patches

### Patch 1: Metadata Headers (env.py)

**File Modified:** `/app/backend/open_webui/env.py` (line 212)

**Default Behavior:** `ENABLE_FORWARD_USER_INFO_HEADERS` defaults to `False`

**Patch Change:** Set default to `True`

**Effect:** Open WebUI automatically adds user context headers to ALL backend requests:

**Headers Added:**
```http
X-OpenWebUI-User-Name: alice
X-OpenWebUI-User-Id: user_abc123
X-OpenWebUI-User-Email: alice@example.com
X-OpenWebUI-User-Role: admin
X-OpenWebUI-Chat-Id: chat_xyz789
```

**Backend Use Cases:**
- **Per-User Rate Limiting** - Track request rates by user_id
- **Conversation Context** - Associate requests with specific chat sessions
- **Usage Analytics** - Monitor which users use which features
- **Audit Logging** - Track actions back to specific users
- **Session Continuity** - Maintain context across multi-turn conversations

**Implementation Details:**
```python
# Before patch (env.py default)
ENABLE_FORWARD_USER_INFO_HEADERS = bool(
    os.getenv("ENABLE_FORWARD_USER_INFO_HEADERS", "False").lower() == "true"
)

# After patch
ENABLE_FORWARD_USER_INFO_HEADERS = bool(
    os.getenv("ENABLE_FORWARD_USER_INFO_HEADERS", "True").lower() == "true"
)
```

**How It's Applied:**
- Dockerfile RUN command patches env.py before build
- Headers injected in `routers/openai.py` before forwarding request
- Backend receives headers transparently (no backend changes needed)

### Patch 2: Metadata Preservation (openai.py)

**File Modified:** `/app/backend/open_webui/routers/openai.py` (line 790)

**Default Behavior:** `.pop("metadata")` removes metadata from request body

**Patch Change:** Use `.get("metadata")` instead to preserve metadata

**Effect:** Metadata stays in JSON body sent to backend:

**Request Body Structure:**
```json
{
  "model": "Qwen3-30B",
  "messages": [
    {"role": "user", "content": "research FastAPI"},
    {"role": "assistant", "content": "..."}
  ],
  "stream": true,
  "metadata": {
    "user_id": "user_abc123",
    "chat_id": "chat_xyz789",
    "session_id": "session_def456",
    "message_id": "msg_ghi789",
    "filter_ids": [],
    "tool_ids": [],
    "files": [],
    "features": {
      "citations": false,
      "web_search": false
    },
    "variables": {}
  }
}
```

**Backend Access:**
```python
# robaiproxy can now access full metadata
metadata = request_body.get("metadata", {})
user_id = metadata.get("user_id")
chat_id = metadata.get("chat_id")
files = metadata.get("files", [])
```

**Use Cases:**
- **File Attachment Handling** - Access uploaded file metadata
- **Tool Filtering** - Respect user's tool_ids selection
- **Session Restoration** - Resume conversation with full context
- **Feature Flags** - Enable/disable features per request

**Implementation:**
```python
# Before patch (line 790)
metadata = data.pop("metadata", None)

# After patch
metadata = data.get("metadata", None)

# Result: metadata remains in 'data' dict sent to backend
```

### Patch 3: Status Event Bridge (middleware.py)

**File Modified:** `/app/backend/open_webui/utils/middleware.py` (line 2440)

**Purpose:** Route SSE status events from backend API to Socket.IO WebSocket

**Flow:**

```
Backend (robaiproxy) sends SSE:
  data: {"type":"status","data":{"description":"Turn 1...","done":false}}

Open WebUI middleware intercepts:
  1. Parse JSON event
  2. Check if type == "status"
  3. Extract status data
  4. Emit via Socket.IO event_emitter
  5. Skip sending as content (don't show status as text)

Frontend receives via WebSocket:
  - Socket.IO listener catches status event
  - Displays above message area (not inside)
  - Replaces previous status (not stacks)
  - Auto-clears when done: true
```

**Code Flow:**

```python
# Simplified implementation (actual patch in middleware.py)

async def process_sse_chunk(chunk: bytes):
    # Parse SSE format
    if chunk.startswith(b"data: "):
        json_str = chunk[6:].decode()
        try:
            event_data = json.loads(json_str)

            # Check if it's a status event
            if event_data.get("type") == "status":
                status_data = event_data.get("data", {})

                # Emit via Socket.IO to frontend
                await event_emitter.emit("status", {
                    "description": status_data.get("description"),
                    "done": status_data.get("done", False),
                    "hidden": status_data.get("hidden", False)
                })

                # Skip sending as content
                return None
        except json.JSONDecodeError:
            pass

    # Forward non-status events normally
    return chunk
```

**Event Format:**

**Status Event (from robaiproxy):**
```python
# Helper function in robaimultiturn/common/streaming.py
def create_status_event(description: str, done: bool = False, hidden: bool = False) -> str:
    return f"data: {json.dumps({
        'type': 'status',
        'data': {
            'description': description,
            'done': done,
            'hidden': hidden
        }
    })}\n\n"

# Usage
yield create_status_event("Turn 1 - Searching knowledge base...", done=False)
yield create_status_event("Turn 1 - Crawling sources...", done=False)
yield create_status_event("Done", done=True, hidden=True)  # Clear status
```

**Frontend Display:**
- Status box appears above message (separate UI element)
- Each new status replaces previous (uses same DOM element)
- When `done: true` received, status box hides
- Status NOT saved in message content (only as metadata)

**Use Cases:**
- Research mode progress updates
- Long-running operation feedback
- Multi-step process visualization
- User doesn't wait in dark (knows what's happening)

## Frontend Customizations

### Research Mode Button

**Modified Files:**
1. `MessageInput.svelte` - Input component (8 changes)
2. `Chat.svelte` - Main chat component (7 changes)
3. `Placeholder.svelte` - Placeholder component (2 changes)

**Total Changes:** 17 modifications across 3 Svelte components

#### MessageInput.svelte Changes

**Line 111** - State variable:
```javascript
export let researchModeEnabled = 0;  // 0=off, 1=research, 2=deep
```

**Lines 306-309** - Message prefix function:
```javascript
function preparePromptForSubmit(text) {
    if (researchModeEnabled === 1) {
        return `<research_request>\n${text}`;
    } else if (researchModeEnabled === 2) {
        return `<research_request_deep>\n${text}`;
    }
    return text;
}
```

**Lines 1516-1530** - Button UI:
```svelte
<button
    class="research-mode-btn"
    on:click={() => researchModeEnabled = (researchModeEnabled + 1) % 3}
    title={researchModeEnabled === 0 ? 'Off' :
           researchModeEnabled === 1 ? 'Research' : 'Deep Research'}
    aria-label="Toggle research mode"
>
    <!-- Flask/beaker SVG icon -->
    <svg>...</svg>
</button>

<style>
.research-mode-btn {
    /* Gray when off (0), blue when research (1), darker blue when deep (2) */
    color: {researchModeEnabled === 0 ? '#999' :
            researchModeEnabled === 1 ? '#4A90E2' : '#2E5C8A'};
}
</style>
```

**Lines 1046, 1062, 1315** - Apply prefix on submit:
```javascript
// Before
dispatch('submit', { prompt: prompt });

// After
dispatch('submit', { prompt: preparePromptForSubmit(prompt) });
```

#### Chat.svelte Changes

**Line 131** - State management:
```javascript
let researchModeEnabled = false;
```

**Lines 169-175, 254-264, 429-453, 576-594** - Reset handlers:
```javascript
// Reset research mode on various events:
// - New chat
// - Chat selection change
// - URL navigation
// - Clear conversation
```

**Lines 187-198, 587-594** - Persistence:
```javascript
// Save to sessionStorage
sessionStorage.setItem('researchModeEnabled', researchModeEnabled);

// Restore from sessionStorage
const saved = sessionStorage.getItem('researchModeEnabled');
if (saved !== null) {
    researchModeEnabled = parseInt(saved);
}
```

**Line 2535** - Bind to MessageInput:
```svelte
<MessageInput bind:researchModeEnabled={researchModeEnabled} />
```

#### Placeholder.svelte Changes

**Line 51** - Prop declaration:
```javascript
export let researchModeEnabled = 0;
```

**Line 205** - Pass to MessageInput:
```svelte
<MessageInput bind:researchModeEnabled />
```

### State Persistence

**sessionStorage Keys:**
```javascript
{
    "researchModeEnabled": "1",  // 0, 1, or 2
    "prompt": "research FastAPI",
    "files": []
}
```

**Lifecycle:**
1. User clicks flask icon → state updates
2. State saved to sessionStorage
3. User refreshes page → state restored
4. User presses Escape → state cleared
5. User starts new chat → state reset to 0

**Reset Triggers:**
- Escape key press
- New chat creation
- Chat selection change
- URL navigation (/c/:id change)

## Integration Patterns

### Request Flow to Backend

**Complete Request Cycle:**

```
1. User Input (Browser)
   - User types "research FastAPI" in chat
   - Research mode enabled (flask icon blue)
   - Clicks Send
   ↓
2. Frontend Processing (MessageInput.svelte)
   - preparePromptForSubmit() adds prefix
   - Message becomes: "<research_request>\nresearch FastAPI"
   - Dispatch to Chat component
   ↓
3. Chat Submission (Chat.svelte)
   - Add message to conversation history
   - Build request payload with metadata
   - Send via fetch() to backend
   ↓
4. Open WebUI Backend (routers/openai.py)
   - Route: POST /api/openai/chat/completions
   - Extract form data and metadata
   - Add user context headers (Patch 1):
       X-OpenWebUI-User-Name: alice
       X-OpenWebUI-User-Id: user_123
       X-OpenWebUI-Chat-Id: chat_456
   - Preserve metadata in body (Patch 2)
   - Forward to OPENAI_API_BASE_URL (robaiproxy)
   ↓
5. robaiproxy Processing (requestProxy.py)
   - Receive POST /v1/chat/completions
   - Extract prefix: "<research_request>"
   - Remove prefix from message
   - Detect research mode: iterations=2
   - Start research orchestration
   - Yield SSE stream:
       data: {"type":"status","data":{"description":"Turn 1...","done":false}}
       data: {"choices":[{"delta":{"content":"FastAPI"}}]}
       data: {"type":"status","data":{"done":true,"hidden":true}}
       data: [DONE]
   ↓
6. Open WebUI Middleware (middleware.py - Patch 3)
   - Intercept SSE stream
   - Parse each "data:" line
   - If type=="status":
       - Extract status data
       - Emit via Socket.IO: event_emitter.emit("status", {...})
       - Skip forwarding (don't show status as content)
   - Else:
       - Forward chunk to frontend normally
   ↓
7. Frontend Display (Chat.svelte + Socket.IO)
   - Socket.IO listener receives status events
   - Display status above message area
   - Replace previous status
   - Stream content into message box
   - When done: hide status, show complete message
```

### Metadata Flow

**What Gets Sent:**

```json
{
  "method": "POST",
  "url": "http://192.168.10.50:8079/v1/chat/completions",
  "headers": {
    "Content-Type": "application/json",
    "Authorization": "Bearer sk-dummy-key",
    "X-OpenWebUI-User-Name": "alice",
    "X-OpenWebUI-User-Id": "user_abc123",
    "X-OpenWebUI-User-Email": "alice@example.com",
    "X-OpenWebUI-User-Role": "admin",
    "X-OpenWebUI-Chat-Id": "chat_xyz789"
  },
  "body": {
    "model": "Qwen3-30B",
    "messages": [
      {"role": "user", "content": "<research_request>\nresearch FastAPI"}
    ],
    "stream": true,
    "metadata": {
      "user_id": "user_abc123",
      "chat_id": "chat_xyz789",
      "session_id": "session_def456",
      "message_id": "msg_ghi789",
      "filter_ids": [],
      "tool_ids": [],
      "files": [],
      "features": {},
      "variables": {}
    }
  }
}
```

**Backend Access Pattern:**

```python
# robaiproxy/requestProxy.py

async def handle_chat_completion(request: Request):
    # Access headers
    user_name = request.headers.get("X-OpenWebUI-User-Name")
    user_id = request.headers.get("X-OpenWebUI-User-Id")
    chat_id = request.headers.get("X-OpenWebUI-Chat-Id")

    # Access body metadata
    body = await request.json()
    metadata = body.get("metadata", {})
    files = metadata.get("files", [])
    session_id = metadata.get("session_id")

    # Use for context-aware processing
    logger.info(f"User {user_name} (ID: {user_id}) in chat {chat_id}")
```

### Status Event System

**Event Creation (Backend - robaimultiturn):**

```python
# robaimultiturn/common/streaming.py

def create_status_event(description: str, done: bool = False, hidden: bool = False) -> str:
    """Create SSE status event for Open WebUI."""
    return f"data: {json.dumps({
        'type': 'status',
        'data': {
            'description': description,
            'done': done,
            'hidden': hidden
        }
    })}\n\n"

# Usage in research mode
async def research_iteration(turn: int):
    # Start iteration
    yield create_status_event(f"Turn {turn} - Searching knowledge base...")
    results = await search_kb()

    # Update status
    yield create_status_event(f"Turn {turn} - Crawling {len(urls)} sources...")
    await crawl_urls(urls)

    # Clear status before content
    yield create_status_event("Done", done=True, hidden=True)

    # Stream actual response
    async for chunk in generate_response():
        yield f"data: {json.dumps(chunk)}\n\n"
```

**Event Routing (Open WebUI Middleware):**

```python
# Simplified from middleware.py patch

async for chunk in backend_response:
    # Parse SSE line
    if chunk.startswith(b"data: "):
        try:
            event_data = json.loads(chunk[6:])

            # Status event?
            if event_data.get("type") == "status":
                status = event_data["data"]

                # Route to WebSocket
                await socket_io.emit("status", {
                    "chat_id": current_chat_id,
                    "description": status["description"],
                    "done": status.get("done", False),
                    "hidden": status.get("hidden", False)
                })

                # Don't forward as content
                continue
        except:
            pass

    # Forward other events normally
    yield chunk
```

**Event Display (Frontend):**

```javascript
// Chat.svelte (simplified)

let currentStatus = null;
let statusVisible = false;

// Socket.IO listener
socket.on('status', (event) => {
    if (event.done) {
        // Hide status
        statusVisible = false;
        currentStatus = null;
    } else {
        // Show/update status
        currentStatus = event.description;
        statusVisible = true;
    }
});
```

```svelte
<!-- Status display (above message area) -->
{#if statusVisible}
    <div class="status-box">
        {currentStatus}
    </div>
{/if}

<div class="message-area">
    <!-- Messages -->
</div>
```

## Docker Architecture

### Multi-Stage Build

**Dockerfile Structure:**

```dockerfile
# Stage 1: Build frontend (Node.js)
FROM node:20 AS frontend-builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY src/ ./src/
RUN npm run build

# Stage 2: Build backend (Python)
FROM python:3.11-slim AS backend-builder
WORKDIR /app/backend
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./

# Stage 3: Final image (apply patches)
FROM python:3.11-slim
WORKDIR /app

# Copy frontend build
COPY --from=frontend-builder /app/build ./frontend/build

# Copy backend
COPY --from=backend-builder /app/backend ./backend

# Apply custom patches
RUN sed -i 's/ENABLE_FORWARD_USER_INFO_HEADERS", "False"/ENABLE_FORWARD_USER_INFO_HEADERS", "True"/g' \
    /app/backend/open_webui/env.py

RUN sed -i 's/.pop("metadata"/.get("metadata"/g' \
    /app/backend/open_webui/routers/openai.py

# Status event bridge patch (more complex, see actual Dockerfile)
RUN echo "PATCH applied for status event routing" && \
    # ... sed commands for middleware.py ...

# Set entrypoint
ENTRYPOINT ["./backend/start.sh"]
```

### Volume Mounting

**Docker Compose Configuration:**

```yaml
open-webui:
  image: robai-webui:latest
  container_name: open-webui
  ports:
    - "80:8080"  # External 80 → Internal 8080
  volumes:
    - open-webui_open-webui:/app/backend/data
  environment:
    - OPENAI_API_BASE_URL=http://192.168.10.50:8079/v1
    - OPENAI_API_KEY=${OPENAI_API_KEY}
  healthcheck:
    test: ["CMD-SHELL", "curl -f http://localhost:8080/ || exit 1"]
    interval: 30s
```

**Volume Contents:**

```
/app/backend/data/  (open-webui_open-webui volume)
├── webui.db          # SQLite database (chat history, users)
├── uploads/          # User uploaded files
├── cache/            # Embedding cache (if local embedding enabled)
└── logs/             # Application logs
```

## Communication Protocols

### HTTP/HTTPS (Request-Response)

**Chat Completion Request:**
```http
POST /api/openai/chat/completions HTTP/1.1
Host: localhost:8080
Content-Type: application/json
Cookie: session=abc123...

{
  "model": "Qwen3-30B",
  "messages": [...],
  "stream": true
}
```

**Proxy to robaiproxy:**
```http
POST /v1/chat/completions HTTP/1.1
Host: 192.168.10.50:8079
Content-Type: application/json
X-OpenWebUI-User-Name: alice
X-OpenWebUI-User-Id: user_123

{
  "model": "Qwen3-30B",
  "messages": [...],
  "stream": true,
  "metadata": {...}
}
```

### Server-Sent Events (SSE)

**Response Stream:**
```
data: {"choices":[{"delta":{"role":"assistant"}}]}

data: {"choices":[{"delta":{"content":"FastAPI"}}]}

data: {"choices":[{"delta":{"content":" is"}}]}

data: {"type":"status","data":{"description":"Turn 1...","done":false}}

data: {"choices":[{"delta":{"content":" a"}}]}

data: {"type":"status","data":{"done":true,"hidden":true}}

data: [DONE]
```

### WebSocket (Socket.IO)

**Status Event Emission:**
```javascript
// Backend emits
socket.emit('status', {
    chat_id: 'chat_xyz789',
    description: 'Turn 1 - Searching...',
    done: false
});

// Frontend receives
socket.on('status', (event) => {
    console.log('Status update:', event.description);
    updateStatusUI(event);
});
```

## Security Considerations

### User Authentication

**SQLite Database:**
- User credentials hashed with bcrypt
- Session tokens stored with expiration
- Role-based access control (admin/user)

**First User = Admin:**
- First account created gets admin role
- Admin can manage users, settings, models

### API Key Forwarding

**Backend Authentication:**
- OPENAI_API_KEY sent to robaiproxy
- robaiproxy validates key
- Invalid key = 401 Unauthorized

**Key Rotation:**
- Multiple API keys supported in backend
- Can rotate without restarting frontend

### Session Security

**WEBUI_SECRET_KEY:**
- Encrypts session cookies
- Auto-generated on first startup
- Stored in /app/backend/data/

**Session Expiration:**
- Default: 24 hours
- Configurable via environment variable
- Auto-logout on expiration

### Data Privacy

**Chat History:**
- Stored locally in SQLite (not cloud)
- Per-user isolation (can't see others' chats)
- Admin can view all chats (for moderation)

**Metadata Forwarding:**
- User email/name sent to backend
- Backend should handle PII appropriately
- No external analytics by default

## Performance Characteristics

**Response Times:**

| Operation | Latency |
|-----------|---------|
| Page Load | 1-2s (initial) |
| New Message (standard) | 500ms - 3s |
| Research Mode (2 iterations) | 30-60s |
| Deep Research (4 iterations) | 90-180s |
| Status Update Delivery | <100ms (WebSocket) |

**Resource Usage:**

| Metric | Value |
|--------|-------|
| Docker Image Size | ~400MB |
| Runtime Memory | ~300MB |
| CPU (idle) | <1% |
| CPU (active chat) | 5-10% |
| Disk I/O | Minimal (SQLite writes) |

**Scalability:**

**Single Instance:**
- Handles ~100 concurrent users
- Limited by robaiproxy backend capacity
- Bottleneck: LLM generation, not frontend

**Horizontal Scaling:**
- Can run multiple Open WebUI instances
- Shared backend (robaiproxy)
- Load balancer distributes traffic

## Troubleshooting Architecture

### Patch Verification

**Check if patches applied:**

```bash
# Metadata headers patch
docker exec open-webui grep -n "ENABLE_FORWARD_USER_INFO_HEADERS" \
    /app/backend/open_webui/env.py
# Should show: "True" default (not "False")

# Metadata preservation patch
docker exec open-webui grep -n ".get(\"metadata\"" \
    /app/backend/open_webui/routers/openai.py
# Should show: .get("metadata") (not .pop("metadata"))

# Status event bridge patch
docker exec open-webui grep -n "status event" \
    /app/backend/open_webui/utils/middleware.py
# Should show: patch code for event routing
```

### Request Tracing

**Follow a request through the stack:**

```bash
# 1. Frontend sends to Open WebUI backend
# Browser dev tools (F12) → Network tab → See POST /api/openai/chat/completions

# 2. Open WebUI logs show forwarding
docker compose logs -f open-webui | grep "Forwarding to"

# 3. robaiproxy receives request
cd robaiproxy
tail -f proxy.log | grep "POST /v1/chat/completions"

# 4. robaiproxy processes and responds
tail -f proxy.log | grep "research mode detected"

# 5. Open WebUI middleware processes response
docker compose logs -f open-webui | grep "status event"

# 6. Frontend displays (browser console)
# F12 → Console → See "Status update: Turn 1..."
```

### WebSocket Debugging

**Check Socket.IO connection:**

```javascript
// Browser console (F12)
// Look for these messages:

"Socket.IO connected"
"Status update: Turn 1 - Searching..."
"Status update: Done (hidden)"

// If not seeing status:
// 1. Check WebSocket connection in Network tab
// 2. Verify middleware patch applied
// 3. Check backend is sending status events
```

## Next Steps

1. **Configuration:** Review [Configuration](configuration.md) for environment variables and tuning
2. **API Reference:** See [API Reference](api-reference.md) for endpoint documentation
3. **Getting Started:** Try [Getting Started](getting-started.md) for usage workflows
4. **Customization:** Modify Svelte components for additional UI features
