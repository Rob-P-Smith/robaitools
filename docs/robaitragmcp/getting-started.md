---
layout: default
title: Getting Started
parent: robaitragmcp
nav_order: 2
---

# Getting Started

Quick start guide for the robaitragmcp MCP server with dynamic tool discovery.

## Prerequisites

- Python 3.11+
- Docker and Docker Compose
- robaimodeltools library (shared dependency)
- 2GB+ RAM recommended

## Quick Start

### Docker Deployment (Recommended)

**Start the MCP server:**
```bash
cd /home/robiloo/Documents/robaitools
docker compose up -d robaitragmcp
```

**Verify it's running:**
```bash
docker compose ps robaitragmcp
# Should show: robaitragmcp   running   0.0.0.0:3000->3000/tcp

docker compose logs robaitragmcp | tail -20
# Look for: "✅ MCP Server listening on ('0.0.0.0', 3000)"
# Look for: "✅ Discovered N tools"
```

**Check logs for discovered tools:**
```bash
docker compose logs robaitragmcp | grep "Discovered"
# Output: "✓ Successfully discovered 25 tools from robaimodeltools"
```

### Local Development

**Run directly:**
```bash
cd robaitragmcp
python3 -u core/mcp_server.py
```

**Expected output:**
```
MCP Server created
🔍 Discovering tools and loading models...
Discovered Crawl4AIRAG method: crawler_crawl_url
Discovered Crawl4AIRAG method: crawler_search_knowledge
... (20+ more tools)
✓ Successfully discovered 25 tools from robaimodeltools
✅ MCP Server listening on ('0.0.0.0', 3000)
✅ Models loaded and ready for instant tool calling
```

## Testing the Server

### Test with netcat

```bash
# Connect to TCP server
nc localhost 3000

# Send initialize request (paste this line):
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","clientInfo":{"name":"test"}}}

# Expected response:
{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05","serverInfo":{"name":"robaimcp","version":"1.0.0"},"capabilities":{"tools":{}}}}

# List tools:
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}

# Call a tool:
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"crawler_search_knowledge","arguments":{"query":"python async"}}}
```

### Test with Python Script

```python
import socket
import json

# Connect to MCP server
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('localhost', 3000))

# Send initialize
init_msg = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "clientInfo": {"name": "test-client"}
    }
}
sock.sendall((json.dumps(init_msg) + "\n").encode())
response = sock.recv(4096)
print("Initialize:", json.loads(response))

# List tools
list_msg = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
sock.sendall((json.dumps(list_msg) + "\n").encode())
response = sock.recv(8192)
tools = json.loads(response)
print(f"Found {len(tools['result']['tools'])} tools")
print("First tool:", tools['result']['tools'][0]['name'])

sock.close()
```

## Integration with robairagapi

The robairagapi service uses robaitragmcp internally. To use it:

**Start robairagapi:**
```bash
docker compose up -d robairagapi
```

**Make REST API calls:**
```bash
# Search via REST API (uses robaitragmcp under the hood)
curl -X POST http://localhost:8081/api/v1/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{"query": "python async", "limit": 5}'
```

## Environment Variables

**Server Configuration:**
- `MCP_TCP_PORT`: TCP port (default: 3000)
- `DISCOVERY_INTERVAL`: Health check interval in seconds (default: 30)
- `MCP_TOOL_TIMEOUT`: Tool execution timeout in seconds (default: 60)

**Dependencies:**
- `CRAWL4AI_URL`: Crawl4AI service URL (default: http://localhost:11235)
- `USE_MEMORY_DB`: RAM mode for SQLite (default: true)

**Example .env:**
```bash
MCP_TCP_PORT=3000
DISCOVERY_INTERVAL=30
MCP_TOOL_TIMEOUT=60
CRAWL4AI_URL=http://localhost:11235
USE_MEMORY_DB=true
```

## Common Workflows

### Workflow 1: Direct TCP Connection

**Use case:** Testing, debugging, or custom MCP client integration.

**Steps:**
1. Start MCP server: `docker compose up -d robaitragmcp`
2. Connect via TCP: `nc localhost 3000` or custom client
3. Send JSON-RPC 2.0 messages (newline-delimited)
4. Receive responses

### Workflow 2: Via robairagapi REST API

**Use case:** HTTP-based access to MCP tools.

**Steps:**
1. Start both services: `docker compose up -d robaitragmcp robairagapi`
2. Make REST API calls to http://localhost:8081
3. robairagapi forwards to robaitragmcp internally
4. Get JSON responses

### Workflow 3: Container Restart Handling

**What happens when monitored containers restart:**

1. Health monitor detects container restart (checks every 30s)
2. Triggers tool refresh automatically
3. Re-discovers all tools from robaimodeltools
4. Logs changes (added/removed tools)
5. Server continues running without interruption

**Monitored containers:**
- robaicrawler (port 11235)
- robaineo4j (port 7687)
- robaikg (port 8088)
- robairagapi (port 8081)

**Example log output:**
```
Container robaicrawler restarted - triggering tool refresh
Refreshing tool discovery...
✓ Successfully discovered 25 tools from robaimodeltools
No changes to tool list
```

## Discovered Tools Reference

**Crawler Tools** (from Crawl4AIRAG class):
- `crawler_crawl_url` - Crawl single URL
- `crawler_crawl_urls_batch` - Crawl multiple URLs
- `crawler_deep_crawl` - Recursive crawling with depth limit
- `crawler_search_knowledge` - Semantic search in knowledge base
- `crawler_add_blocked_domain` - Block domain patterns
- `crawler_remove_blocked_domain` - Unblock domains
- `crawler_get_blocked_domains` - List blocked domains
- `crawler_clear_blocked_domains` - Clear all blocked domains
- Plus ~10-15 more methods

**Search Tools** (from SearchHandler class):
- `search_handler_search` - Basic semantic search
- `search_handler_hybrid_search` - Vector + graph search
- Plus other SearchHandler methods

**Dynamic Discovery:**
- Exact tool list depends on robaimodeltools version
- New methods automatically become tools
- Check logs for complete list: `docker compose logs robaitragmcp | grep "Discovered"`

## Troubleshooting

### Issue: Server won't start

**Symptoms:**
```
Error during tool discovery: ModuleNotFoundError: No module named 'robaimodeltools'
```

**Solution:**
```bash
# Verify robaimodeltools is mounted
docker compose exec robaitragmcp ls -la /robaimodeltools

# Check if Python can import it
docker compose exec robaitragmcp python3 -c "import robaimodeltools; print('OK')"

# Restart with fresh build
docker compose down robaitragmcp
docker compose up -d --build robaitragmcp
```

### Issue: "Discovered 0 tools"

**Symptoms:**
```
✓ Successfully discovered 0 tools from robaimodeltools
```

**Cause:** robaimodeltools not available or import failed.

**Solution:**
1. Check logs for import errors: `docker compose logs robaitragmcp | grep -i error`
2. Verify volume mounts in docker-compose.yml
3. Check PYTHONPATH includes robaimodeltools
4. Restart service: `docker compose restart robaitragmcp`

### Issue: Tool timeout

**Symptoms:**
```
ERROR - Tool crawler_deep_crawl timed out after 60s
```

**Solution:**
```bash
# Increase timeout in .env
MCP_TOOL_TIMEOUT=120

# Restart service
docker compose restart robaitragmcp
```

### Issue: Health monitor warnings

**Symptoms:**
```
WARNING - Some monitored containers not found: {'robaikg', 'robaineo4j'}
```

**Explanation:** This is OK - containers may be stopped or not needed.

**Solution:** Ignore if you're not using KG features. Otherwise:
```bash
docker compose up -d robaikg robaineo4j
```

### Issue: Connection refused on port 3000

**Symptoms:**
```
nc localhost 3000
Connection refused
```

**Solution:**
1. Check service is running: `docker compose ps robaitragmcp`
2. Check port binding: `docker compose port robaitragmcp 3000`
3. Check logs: `docker compose logs robaitragmcp`
4. Verify port not in use: `lsof -i :3000`

## Log Locations

**Main log file:**
```bash
docker compose exec robaitragmcp cat /tmp/robaimcp.log
```

**Docker logs:**
```bash
docker compose logs robaitragmcp
docker compose logs robaitragmcp -f  # Follow mode
docker compose logs robaitragmcp --tail 50
```

**MCP action logs:**
```bash
# Filter for specific actions
docker compose logs robaitragmcp | grep "MCP_ACTION"
docker compose logs robaitragmcp | grep "tools/call"
docker compose logs robaitragmcp | grep "Discovered"
```

## Next Steps

1. **Architecture:** See [Architecture](architecture.md) for technical details
2. **Configuration:** Review [Configuration](configuration.md) for environment tuning
3. **API Reference:** Check [API Reference](api-reference.md) for available tools
4. **Integration:** Learn about integrating with AI assistants and REST API
