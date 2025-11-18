---
layout: default
title: API Reference
parent: robaitragmcp
nav_order: 5
---

# API Reference

MCP protocol methods and dynamically discovered tools.

## MCP Protocol Methods

### initialize

Initialize MCP connection.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "clientInfo": {"name": "client-name"}
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "serverInfo": {
      "name": "robaimcp",
      "version": "1.0.0"
    },
    "capabilities": {"tools": {}}
  }
}
```

### tools/list

List all available tools.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {}
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "crawler_crawl_url",
        "description": "Crawl a URL and extract content",
        "inputSchema": {
          "type": "object",
          "properties": {
            "url": {"type": "string"},
            "tags": {"type": "string"}
          },
          "required": ["url"]
        }
      }
      // ... all discovered tools
    ]
  }
}
```

### tools/call

Execute a tool.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "crawler_search_knowledge",
    "arguments": {
      "query": "python async",
      "limit": 5
    }
  }
}
```

**Response (Success):**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Found 5 results: ..."
      }
    ],
    "isError": false
  }
}
```

**Response (Error):**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Error: Tool timeout after 60s"
      }
    ],
    "isError": true
  }
}
```

## Dynamically Discovered Tools

Tools are discovered from robaimodeltools at startup. Exact list depends on robaimodeltools version.

### Crawler Tools (from Crawl4AIRAG)

**crawler_crawl_url**
- Description: Crawl single URL and extract content
- Parameters: url (required), tags, retention_policy
- Returns: Success message with chunk count

**crawler_search_knowledge**
- Description: Search knowledge base with semantic search
- Parameters: query (required), limit, tags
- Returns: Search results with scores

**crawler_add_blocked_domain**
- Description: Block domain pattern from crawling
- Parameters: pattern (required)
- Returns: Confirmation message

**crawler_deep_crawl**
- Description: Recursively crawl from starting URL
- Parameters: start_url (required), max_depth, max_pages
- Returns: Crawl summary with URLs processed

### Search Tools (from SearchHandler)

**search_handler_search**
- Description: Semantic search in knowledge base
- Parameters: query (required), limit
- Returns: Search results with relevance scores

**search_handler_hybrid_search**
- Description: Combined vector + graph search
- Parameters: query (required), limit
- Returns: Enhanced search results

### Complete Tool List

To get the exact current tool list:
```bash
# Connect and list tools
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | nc localhost 3000
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | nc localhost 3000

# Or check logs
docker compose logs robaitragmcp | grep "Discovered"
```

## Error Codes

JSON-RPC 2.0 standard error codes:

- `-32700`: Parse error (invalid JSON)
- `-32600`: Invalid request
- `-32601`: Method not found
- `-32602`: Invalid params
- `-32603`: Internal error (includes timeout)

MCP-specific error codes:

- `-32000`: Tool not found
- `-32001`: Tool execution error
- `-32002`: Discovery error

## Integration Examples

### Python TCP Client

```python
import socket, json

sock = socket.socket()
sock.connect(('localhost', 3000))

# Initialize
sock.sendall(b'{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}\n')
print(sock.recv(4096).decode())

# List tools
sock.sendall(b'{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}\n')
print(sock.recv(8192).decode())

# Call tool
msg = {
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
        "name": "crawler_search_knowledge",
        "arguments": {"query": "python", "limit": 3}
    }
}
sock.sendall((json.dumps(msg) + '\n').encode())
print(sock.recv(4096).decode())

sock.close()
```

### Via robairagapi REST API

```bash
# robairagapi uses robaitragmcp internally
curl -X POST http://localhost:8081/api/v1/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{"query": "python async", "limit": 5}'
```

## Next Steps

- **Getting Started:** See [Getting Started](getting-started.md)
- **Architecture:** Review [Architecture](architecture.md)
- **Configuration:** Check [Configuration](configuration.md)
