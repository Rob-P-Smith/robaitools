---
layout: default
title: API Reference
parent: robaiwebui
nav_order: 3
---

# API Reference

Complete API documentation for robaiwebui including HTTP endpoints, WebSocket events, metadata structures, and integration examples.

## HTTP Endpoints

Open WebUI exposes HTTP API endpoints for chat completions, user management, and configuration.

### Chat Completion API

**POST /api/openai/chat/completions**

**Purpose:** Submit chat messages and receive streaming responses

**Request:**
```http
POST /api/openai/chat/completions HTTP/1.1
Host: localhost:8080
Content-Type: application/json
Cookie: session=abc123...

{
  "model": "Qwen3-30B",
  "messages": [
    {"role": "user", "content": "What is FastAPI?"}
  ],
  "stream": true,
  "temperature": 0.7,
  "max_tokens": 2000
}
```

**Response (Streaming SSE):**
```
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1234567890,"model":"Qwen3-30B","choices":[{"index":0,"delta":{"role":"assistant","content":""},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1234567890,"model":"Qwen3-30B","choices":[{"index":0,"delta":{"content":"FastAPI"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1234567890,"model":"Qwen3-30B","choices":[{"index":0,"delta":{"content":" is"},"finish_reason":null}]}

data: [DONE]
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| model | string | Yes | Model name (e.g., "Qwen3-30B") |
| messages | array | Yes | Conversation history |
| stream | boolean | No | Enable streaming (default: false) |
| temperature | float | No | Response randomness 0-2 (default: 0.7) |
| max_tokens | integer | No | Max response length (default: model limit) |
| top_p | float | No | Nucleus sampling 0-1 (default: 1.0) |
| frequency_penalty | float | No | Reduce repetition -2 to 2 (default: 0) |
| presence_penalty | float | No | Encourage new topics -2 to 2 (default: 0) |
| stop | array | No | Stop sequences (default: null) |

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique completion ID |
| object | string | Always "chat.completion.chunk" for streaming |
| created | integer | Unix timestamp |
| model | string | Model used for generation |
| choices | array | Response choices (usually 1) |
| choices[].index | integer | Choice index (0-based) |
| choices[].delta | object | Content delta |
| choices[].delta.role | string | "assistant" (first chunk only) |
| choices[].delta.content | string | Text content chunk |
| choices[].finish_reason | string | "stop", "length", or null |

**Error Responses:**

```json
{
  "error": {
    "message": "Model not found: invalid-model",
    "type": "invalid_request_error",
    "param": "model",
    "code": 404
  }
}
```

**Common Error Codes:**

| Code | Type | Description |
|------|------|-------------|
| 400 | invalid_request_error | Malformed request |
| 401 | authentication_error | Invalid API key |
| 404 | not_found_error | Model not found |
| 429 | rate_limit_exceeded | Too many requests |
| 500 | internal_server_error | Backend error |
| 503 | service_unavailable | Backend unreachable |

### User Management API

**POST /api/v1/auths/signup**

**Purpose:** Create new user account

**Request:**
```http
POST /api/v1/auths/signup HTTP/1.1
Host: localhost:8080
Content-Type: application/json

{
  "email": "alice@example.com",
  "password": "secure-password-123",
  "name": "Alice"
}
```

**Response:**
```json
{
  "id": "user_abc123",
  "email": "alice@example.com",
  "name": "Alice",
  "role": "admin",
  "created_at": 1234567890
}
```

**Notes:**
- First user created gets "admin" role
- Subsequent users get role from DEFAULT_USER_ROLE env var
- Requires ENABLE_SIGNUP=true

**POST /api/v1/auths/signin**

**Purpose:** User login

**Request:**
```json
{
  "email": "alice@example.com",
  "password": "secure-password-123"
}
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "user_abc123",
    "email": "alice@example.com",
    "name": "Alice",
    "role": "admin"
  }
}
```

**GET /api/v1/users**

**Purpose:** List all users (admin only)

**Headers:**
```http
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "users": [
    {
      "id": "user_abc123",
      "email": "alice@example.com",
      "name": "Alice",
      "role": "admin",
      "created_at": 1234567890
    },
    {
      "id": "user_xyz789",
      "email": "bob@example.com",
      "name": "Bob",
      "role": "user",
      "created_at": 1234567900
    }
  ]
}
```

### Chat Management API

**GET /api/v1/chats**

**Purpose:** Get user's chat history

**Headers:**
```http
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "chats": [
    {
      "id": "chat_123",
      "title": "FastAPI Discussion",
      "created_at": 1234567890,
      "updated_at": 1234567950,
      "message_count": 12
    },
    {
      "id": "chat_456",
      "title": "Python Async Programming",
      "created_at": 1234567800,
      "updated_at": 1234567900,
      "message_count": 8
    }
  ]
}
```

**GET /api/v1/chats/{chat_id}**

**Purpose:** Get specific chat messages

**Response:**
```json
{
  "id": "chat_123",
  "title": "FastAPI Discussion",
  "model": "Qwen3-30B",
  "messages": [
    {
      "id": "msg_1",
      "role": "user",
      "content": "What is FastAPI?",
      "timestamp": 1234567890
    },
    {
      "id": "msg_2",
      "role": "assistant",
      "content": "FastAPI is a modern...",
      "timestamp": 1234567893
    }
  ],
  "created_at": 1234567890,
  "updated_at": 1234567950
}
```

**DELETE /api/v1/chats/{chat_id}**

**Purpose:** Delete chat

**Response:**
```json
{
  "success": true,
  "message": "Chat deleted successfully"
}
```

### Model Management API

**GET /api/v1/models**

**Purpose:** List available models

**Response:**
```json
{
  "models": [
    {
      "id": "Qwen3-30B",
      "name": "Qwen3-30B",
      "object": "model",
      "created": 1234567890,
      "owned_by": "robaitools"
    }
  ]
}
```

**Notes:**
- Models list comes from backend (robaiproxy)
- Filtered by MODEL_FILTER_LIST if ENABLE_MODEL_FILTER=true

### Health Check API

**GET /health**

**Purpose:** Service health check

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime": 3600
}
```

**GET /api/v1/status**

**Purpose:** Detailed status information

**Response:**
```json
{
  "backend_url": "http://192.168.10.50:8079/v1",
  "backend_reachable": true,
  "database_connected": true,
  "active_sessions": 5,
  "total_users": 12,
  "total_chats": 145
}
```

## WebSocket API (Socket.IO)

### Connection

**URL:** `ws://localhost:80/socket.io/`

**Protocol:** Socket.IO (WebSocket with fallback to HTTP long-polling)

**Authentication:** Via session cookie (set after login)

**Client-Side Connection:**
```javascript
import { io } from 'socket.io-client';

const socket = io('http://localhost:80', {
  auth: {
    token: jwt_token
  },
  transports: ['websocket', 'polling']
});

socket.on('connect', () => {
  console.log('Connected to WebSocket');
});

socket.on('disconnect', () => {
  console.log('Disconnected from WebSocket');
});
```

### Status Events

**Event Name:** `status`

**Purpose:** Real-time progress updates during research mode

**Event Structure:**
```javascript
{
  "chat_id": "chat_xyz789",
  "description": "Turn 1 - Searching knowledge base...",
  "done": false,
  "hidden": false
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| chat_id | string | Associated chat ID |
| description | string | Human-readable status message |
| done | boolean | True when operation complete |
| hidden | boolean | True to hide status (usually with done=true) |

**Client-Side Listener:**
```javascript
socket.on('status', (event) => {
  console.log('Status update:', event.description);

  if (event.done) {
    // Operation complete, hide status
    hideStatus();
  } else {
    // Show status above message area
    showStatus(event.description);
  }
});
```

**Example Status Sequence:**
```javascript
// Turn 1
{chat_id: "chat_123", description: "Turn 1 - Searching knowledge base...", done: false, hidden: false}

{chat_id: "chat_123", description: "Turn 1 - Crawling web sources...", done: false, hidden: false}

{chat_id: "chat_123", description: "Turn 1 - Searching web...", done: false, hidden: false}

// Turn 2
{chat_id: "chat_123", description: "Turn 2 - Analyzing implementation...", done: false, hidden: false}

{chat_id: "chat_123", description: "Turn 2 - Searching knowledge base...", done: false, hidden: false}

// Complete - clear status
{chat_id: "chat_123", description: "Done", done: true, hidden: true}
```

### Chat Events

**Event Name:** `chat:message`

**Purpose:** Real-time message notifications

**Event Structure:**
```javascript
{
  "chat_id": "chat_xyz789",
  "message": {
    "id": "msg_123",
    "role": "assistant",
    "content": "Response text",
    "timestamp": 1234567890
  }
}
```

**Event Name:** `chat:typing`

**Purpose:** Typing indicators

**Event Structure:**
```javascript
{
  "chat_id": "chat_xyz789",
  "user_id": "user_abc123",
  "user_name": "Alice",
  "typing": true
}
```

## Metadata Structure

### Request Metadata

**Complete Metadata Object:**
```json
{
  "user_id": "user_abc123",
  "chat_id": "chat_xyz789",
  "session_id": "session_def456",
  "message_id": "msg_ghi789",
  "filter_ids": [],
  "tool_ids": [],
  "files": [
    {
      "id": "file_123",
      "name": "document.pdf",
      "type": "application/pdf",
      "size": 125467,
      "url": "/uploads/file_123.pdf"
    }
  ],
  "features": {
    "citations": false,
    "web_search": false,
    "code_execution": false
  },
  "variables": {}
}
```

**Field Descriptions:**

| Field | Type | Description |
|-------|------|-------------|
| user_id | string | Current user's unique ID |
| chat_id | string | Current conversation ID |
| session_id | string | Browser session ID |
| message_id | string | Current message ID |
| filter_ids | array | Applied filters (knowledge base filtering) |
| tool_ids | array | Enabled tools for this request |
| files | array | Uploaded file metadata |
| files[].id | string | Unique file ID |
| files[].name | string | Original filename |
| files[].type | string | MIME type |
| files[].size | integer | File size in bytes |
| files[].url | string | Download URL |
| features | object | Feature flags |
| features.citations | boolean | Include citations in response |
| features.web_search | boolean | Enable web search |
| features.code_execution | boolean | Allow code execution |
| variables | object | Custom variables (user-defined) |

### Response Metadata (Preserved)

**Metadata in Backend Request:**
```json
{
  "model": "Qwen3-30B",
  "messages": [...],
  "stream": true,
  "metadata": {
    "user_id": "user_abc123",
    "chat_id": "chat_xyz789",
    ...
  }
}
```

**Backend Access Pattern:**
```python
# robaiproxy/requestProxy.py

async def handle_chat_completion(request: Request):
    body = await request.json()
    metadata = body.get("metadata", {})

    # Access user context
    user_id = metadata.get("user_id")
    chat_id = metadata.get("chat_id")

    # Access uploaded files
    files = metadata.get("files", [])
    for file in files:
        file_url = file["url"]
        # Process file...

    # Access feature flags
    features = metadata.get("features", {})
    if features.get("web_search"):
        # Enable web search...
```

## Header Structure

### User Context Headers

**Headers Added by Patch 1:**

| Header | Example Value | Description |
|--------|---------------|-------------|
| X-OpenWebUI-User-Name | alice | Username |
| X-OpenWebUI-User-Id | user_abc123 | Unique user ID |
| X-OpenWebUI-User-Email | alice@example.com | User email |
| X-OpenWebUI-User-Role | admin | User role (admin/user) |
| X-OpenWebUI-Chat-Id | chat_xyz789 | Current chat ID |

**Backend Access Pattern:**
```python
# robaiproxy/requestProxy.py

async def handle_chat_completion(request: Request):
    # Access headers
    user_name = request.headers.get("X-OpenWebUI-User-Name")
    user_id = request.headers.get("X-OpenWebUI-User-Id")
    user_email = request.headers.get("X-OpenWebUI-User-Email")
    user_role = request.headers.get("X-OpenWebUI-User-Role")
    chat_id = request.headers.get("X-OpenWebUI-Chat-Id")

    # Use for rate limiting
    if user_role != "admin":
        if check_rate_limit(user_id):
            return {"error": "Rate limit exceeded"}

    # Use for logging
    logger.info(f"User {user_name} ({user_id}) in chat {chat_id}")
```

## Status Event Format

### Event Creation (Backend)

**Helper Function:**
```python
# robaimultiturn/common/streaming.py

def create_status_event(
    description: str,
    done: bool = False,
    hidden: bool = False
) -> str:
    """Create SSE status event for Open WebUI."""
    return f"data: {json.dumps({
        'type': 'status',
        'data': {
            'description': description,
            'done': done,
            'hidden': hidden
        }
    })}\n\n"
```

**Usage:**
```python
# Send status update
yield create_status_event("Turn 1 - Searching knowledge base...")

# Update status (replaces previous)
yield create_status_event("Turn 1 - Crawling sources...")

# Clear status (hide it)
yield create_status_event("Done", done=True, hidden=True)
```

**SSE Stream Example:**
```
data: {"type":"status","data":{"description":"Turn 1 - Searching...","done":false,"hidden":false}}

data: {"choices":[{"delta":{"content":"FastAPI"}}]}

data: {"type":"status","data":{"description":"Turn 1 - Crawling...","done":false,"hidden":false}}

data: {"choices":[{"delta":{"content":" is"}}]}

data: {"type":"status","data":{"done":true,"hidden":true}}

data: [DONE]
```

### Event Display (Frontend)

**JavaScript Handler:**
```javascript
let currentStatus = null;
let statusVisible = false;

// Socket.IO listener
socket.on('status', (event) => {
  if (event.done && event.hidden) {
    // Hide status box
    statusVisible = false;
    currentStatus = null;
    updateStatusUI();
  } else if (!event.done) {
    // Show/update status
    currentStatus = event.description;
    statusVisible = true;
    updateStatusUI();
  }
});

function updateStatusUI() {
  const statusBox = document.getElementById('status-box');
  if (statusVisible && currentStatus) {
    statusBox.textContent = currentStatus;
    statusBox.style.display = 'block';
  } else {
    statusBox.style.display = 'none';
  }
}
```

**Svelte Component:**
```svelte
<script>
  import { onMount } from 'svelte';
  import { io } from 'socket.io-client';

  let statusText = '';
  let statusVisible = false;

  onMount(() => {
    const socket = io();

    socket.on('status', (event) => {
      if (event.done && event.hidden) {
        statusVisible = false;
      } else if (!event.done) {
        statusText = event.description;
        statusVisible = true;
      }
    });

    return () => socket.disconnect();
  });
</script>

{#if statusVisible}
  <div class="status-box">
    {statusText}
  </div>
{/if}

<style>
  .status-box {
    padding: 12px 16px;
    margin-bottom: 16px;
    background-color: #f0f7ff;
    border-left: 4px solid #4A90E2;
    border-radius: 4px;
    font-size: 14px;
    color: #333;
  }
</style>
```

## Integration Examples

### Example 1: Send Chat Message with Research Mode

**Client-Side (JavaScript):**
```javascript
async function sendResearchMessage(message) {
  // Add research prefix
  const researchMessage = `<research_request>\n${message}`;

  // Send request
  const response = await fetch('http://localhost:8080/api/openai/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Cookie': document.cookie  // Session cookie
    },
    body: JSON.stringify({
      model: 'Qwen3-30B',
      messages: [
        { role: 'user', content: researchMessage }
      ],
      stream: true
    })
  });

  // Handle streaming response
  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.substring(6);
        if (data === '[DONE]') {
          console.log('Stream complete');
          return;
        }

        try {
          const parsed = JSON.parse(data);
          const content = parsed.choices[0]?.delta?.content;
          if (content) {
            console.log('Content:', content);
            appendToMessage(content);
          }
        } catch (e) {
          // Skip invalid JSON
        }
      }
    }
  }
}
```

### Example 2: Monitor Status Updates

**Client-Side (JavaScript):**
```javascript
import { io } from 'socket.io-client';

// Connect to WebSocket
const socket = io('http://localhost:80');

// Status update handler
socket.on('status', (event) => {
  const statusBox = document.getElementById('status-box');

  if (event.done && event.hidden) {
    // Hide status
    statusBox.style.display = 'none';
  } else if (!event.done) {
    // Show/update status
    statusBox.textContent = event.description;
    statusBox.style.display = 'block';
  }
});

// Send research request
sendResearchMessage('research FastAPI performance optimization');
```

### Example 3: Backend Processing with Metadata

**Backend (Python - robaiproxy):**
```python
from fastapi import Request, Response
import json

async def handle_chat_completion(request: Request):
    # Extract headers
    user_name = request.headers.get("X-OpenWebUI-User-Name")
    user_id = request.headers.get("X-OpenWebUI-User-Id")
    chat_id = request.headers.get("X-OpenWebUI-Chat-Id")

    # Extract body and metadata
    body = await request.json()
    metadata = body.get("metadata", {})
    messages = body.get("messages", [])

    # Check for research mode prefix
    last_message = messages[-1]["content"]
    is_research = last_message.startswith("<research_request>")

    if is_research:
        # Remove prefix
        query = last_message.replace("<research_request>\n", "")

        # Start research orchestration
        async for chunk in research_mode(query, user_id, chat_id):
            yield chunk
    else:
        # Standard RAG mode
        async for chunk in standard_rag(last_message, metadata):
            yield chunk
```

### Example 4: Upload File with Chat

**Client-Side (JavaScript):**
```javascript
async function uploadAndChat(file, message) {
  // Upload file first
  const formData = new FormData();
  formData.append('file', file);

  const uploadResponse = await fetch('http://localhost:8080/api/v1/files/upload', {
    method: 'POST',
    headers: {
      'Cookie': document.cookie
    },
    body: formData
  });

  const fileData = await uploadResponse.json();

  // Send chat message with file metadata
  const response = await fetch('http://localhost:8080/api/openai/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Cookie': document.cookie
    },
    body: JSON.stringify({
      model: 'Qwen3-30B',
      messages: [
        {
          role: 'user',
          content: message
        }
      ],
      metadata: {
        files: [
          {
            id: fileData.id,
            name: fileData.name,
            type: fileData.type,
            size: fileData.size,
            url: fileData.url
          }
        ]
      },
      stream: true
    })
  });

  // Handle response...
}
```

## Error Handling

### HTTP Error Responses

**Format:**
```json
{
  "error": {
    "message": "Detailed error description",
    "type": "error_type",
    "param": "parameter_name",
    "code": 400
  }
}
```

**Common Errors:**

**401 Unauthorized:**
```json
{
  "error": {
    "message": "Invalid API key",
    "type": "authentication_error",
    "code": 401
  }
}
```

**404 Not Found:**
```json
{
  "error": {
    "message": "Model 'invalid-model' not found",
    "type": "not_found_error",
    "param": "model",
    "code": 404
  }
}
```

**429 Rate Limit:**
```json
{
  "error": {
    "message": "Rate limit exceeded. Retry after 60 seconds.",
    "type": "rate_limit_exceeded",
    "code": 429
  }
}
```

**503 Service Unavailable:**
```json
{
  "error": {
    "message": "Backend service unavailable at http://192.168.10.50:8079",
    "type": "service_unavailable",
    "code": 503
  }
}
```

### WebSocket Error Handling

**Connection Error:**
```javascript
socket.on('connect_error', (error) => {
  console.error('WebSocket connection failed:', error.message);
  // Fallback to HTTP long-polling
});
```

**Disconnection Handling:**
```javascript
socket.on('disconnect', (reason) => {
  if (reason === 'io server disconnect') {
    // Server disconnected client, reconnect manually
    socket.connect();
  }
  // Other reasons: auto-reconnect handled by socket.io
});
```

## Performance Tips

**For HTTP API:**
1. Use streaming (`stream: true`) for better perceived performance
2. Reuse connections (keep-alive) for multiple requests
3. Implement client-side request queueing to avoid overwhelming backend
4. Set appropriate `max_tokens` to limit response size

**For WebSocket:**
1. Maintain single persistent connection (don't reconnect per message)
2. Use binary frames for large data transfers
3. Implement exponential backoff for reconnection attempts
4. Monitor connection health with ping/pong

**For Research Mode:**
1. Status updates arrive via WebSocket (faster than SSE)
2. Don't poll for status - use event-driven updates
3. Clear status promptly when `done: true` received
4. Limit concurrent research requests to avoid resource exhaustion

## Next Steps

1. **Getting Started:** Try [Getting Started](getting-started.md) for practical usage examples
2. **Architecture:** Review [Architecture](architecture.md) for technical implementation details
3. **Configuration:** Check [Configuration](configuration.md) for environment settings
4. **Integration:** Use code examples above to integrate with robaiwebui
