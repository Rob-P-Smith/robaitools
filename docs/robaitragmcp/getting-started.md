---
layout: default
title: Getting Started
parent: robaitragmcp
nav_order: 1
---

# Getting Started with robaitragmcp

Complete setup guide for the MCP Server for RAG with web crawling and semantic search.

## Prerequisites

Before installing robaitragmcp, ensure you have:

- **Python 3.11+** installed
- **SQLite 3.35+** (built-in on most systems)
- **Node.js 18+** (for Claude Desktop integration)
- **Docker** (optional, for Crawl4AI)
- **At least 4GB RAM** (more for large searches)
- **Git** for cloning repository

## Installation

### Step 1: Navigate to Directory

```bash
cd /path/to/robaitools/robaitragmcp
```

### Step 2: Install Dependencies

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install MCP server package
pip install -e .
```

**Key Dependencies**:
- mcp - Model Context Protocol SDK
- httpx - Async HTTP client (for Crawl4AI)
- sqlite-vec - Vector search in SQLite
- pydantic - Data validation

### Step 3: Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit with your settings
nano .env
```

**Minimum Configuration**:

```bash
# Database Configuration
ROBAI_DATABASE_MODE=disk           # or 'ram' for in-memory
ROBAI_DATABASE_PATH=./data/rag.db  # SQLite database file
ROBAI_CRAWL4AI_URL=http://localhost:5037

# Retention Policy
ROBAI_RETENTION_POLICY=permanent   # permanent, session, 30day
ROBAI_SESSION_TIMEOUT=86400        # 24 hours in seconds

# Neo4j (optional)
ROBAI_ENABLE_KNOWLEDGE_GRAPH=false
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=knowledge_graph_2024
```

See [Configuration](configuration.html) for all options.

### Step 4: Start Crawl4AI (if using Docker)

```bash
# Start Crawl4AI service (required for web crawling)
docker run -d -p 5037:5037 crawl4ai/crawl4ai-server

# Verify it's running
curl http://localhost:5037/health
```

Or install locally:

```bash
pip install crawl4ai

# Start server
crawl4ai-server
```

### Step 5: Start robaitragmcp Server

**Development Mode**:

```bash
# Run with stdio output (for Claude Desktop)
mcp run robaitragmcp.server
```

**Production Mode** (Standalone):

```bash
# Run as background process
nohup mcp run robaitragmcp.server > robaitragmcp.log 2>&1 &
```

### Step 6: Integrate with Claude Desktop

Add to `~/.claude/config.json`:

```json
{
  "mcpServers": {
    "robaitragmcp": {
      "command": "mcp",
      "args": ["run", "robaitragmcp.server"],
      "env": {
        "ROBAI_DATABASE_MODE": "disk",
        "ROBAI_DATABASE_PATH": "/path/to/data/rag.db"
      }
    }
  }
}
```

Restart Claude Desktop to load the server.

## Database Modes

### RAM Mode (Fast)

```bash
ROBAI_DATABASE_MODE=ram
ROBAI_MAX_RAM_SIZE=1GB  # Maximum memory usage
```

**Features**:
- 10-50x faster than disk
- Differential sync to disk
- Fast session switching
- Good for interactive use

**Limitations**:
- Limited by available RAM
- Data lost on process restart (without sync)

**Best For**: Development, interactive sessions

### Disk Mode (Persistent)

```bash
ROBAI_DATABASE_MODE=disk
ROBAI_DATABASE_PATH=/path/to/rag.db
```

**Features**:
- Full data persistence
- Unlimited size
- Automatic backups
- Survives process restart

**Limitations**:
- Slightly slower than RAM mode
- More I/O operations

**Best For**: Production, long-term storage

## Basic Usage

### Using Claude Desktop

1. Start Claude Desktop after configuring robaitragmcp
2. MCP tools appear in the prompt area
3. Use natural language to request operations:

```
"Crawl https://docs.python.org and search for async patterns"
```

Available tools:
- `crawl_url` - Extract content from web page
- `search` - Search indexed content by text
- `vector_search` - Semantic similarity search
- `get_memory` - Retrieve stored content
- `create_tag` - Tag content for organization
- And more...

### Using Python Client

#### Extract Web Content

```python
import subprocess
import json

# Call MCP tool via subprocess
def call_mcp_tool(tool_name, **kwargs):
    cmd = ["mcp", "call", "robaitragmcp.server", tool_name]
    result = subprocess.run(cmd, capture_output=True, text=True, input=json.dumps(kwargs))
    return json.loads(result.stdout)

# Crawl a website
response = call_mcp_tool("crawl_url", url="https://example.com")
print(f"Extracted {len(response['content'])} characters")
```

#### Search Indexed Content

```python
# Search by text
search_result = call_mcp_tool("search",
    query="python async patterns",
    limit=5
)

for result in search_result['results']:
    print(f"- {result['title']}: {result['relevance']}")
```

#### Vector Search (Semantic)

```python
# Semantic similarity search
vector_result = call_mcp_tool("vector_search",
    query="how to use asyncio in Python",
    limit=10
)

print(f"Found {len(vector_result['results'])} semantically similar chunks")
```

### Using cURL (for testing)

```bash
# Check server health
curl http://localhost:8088/health

# List available tools (MCP protocol)
curl -X POST http://localhost:8088/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
  }'
```

## Understanding Content Organization

### Tags

Organize content hierarchically:

```
// Create tags
python
  - asyncio
  - fastapi
  - pydantic

documentation
  - tutorials
  - api-reference
  - architecture
```

Tools tagged for easy discovery:

```python
call_mcp_tool("create_tag",
    name="python/asyncio",
    description="Python async/await patterns"
)
```

### Memory System

Content stored in memory with:
- **Full content**: Original text from crawled pages
- **Chunks**: Split for vector search (500-2000 chars)
- **Embeddings**: Vector representations for semantic search
- **Metadata**: URL, title, tags, timestamps

### Retention Policies

**Permanent**:
- Content kept indefinitely
- Manual deletion only
- Best for reference documents

**Session**:
- Content valid for current session only
- Auto-deleted after timeout
- Best for temporary searches

**30-day**:
- Auto-deleted after 30 days
- Good balance of retention and cleanup
- Best for time-sensitive content

## Testing Installation

### Test 1: MCP Server Health

```bash
# Check if server is responsive
python -c "from robaitragmcp.server import MCP_SERVER; print('Server OK')"
```

### Test 2: Database Operations

```python
from robaitragmcp.database import Database

db = Database(mode='disk')
db.connect()

# Test write
db.store_content(
    url="https://test.example.com",
    title="Test Page",
    content="This is test content"
)

# Test search
results = db.search("test content", limit=5)
print(f"Found {len(results)} results")

db.close()
```

### Test 3: Vector Search

```python
from robaitragmcp.embeddings import EmbeddingModel

model = EmbeddingModel()
results = model.search(
    query="python async patterns",
    limit=3
)

print(f"Found {len(results)} semantic matches")
```

## Common Operations

### Bulk Crawl Multiple URLs

```python
import asyncio

async def crawl_urls(urls):
    results = []
    for url in urls:
        response = call_mcp_tool("crawl_url", url=url)
        results.append(response)
    return results

urls = [
    "https://docs.python.org",
    "https://fastapi.tiangolo.com",
    "https://pydantic-docs.helpmanual.io"
]

results = asyncio.run(crawl_urls(urls))
```

### Search with Filters

```python
# Search within specific tags
search_result = call_mcp_tool("search",
    query="async patterns",
    tags=["python", "asyncio"],
    limit=10
)
```

### Export Content

```python
# Export all stored content
export = call_mcp_tool("export_content",
    format="markdown",
    tags=["python"]
)

with open("python_docs.md", "w") as f:
    f.write(export['content'])
```

## Troubleshooting

### MCP Server Won't Start

**Problem**: Server fails to initialize

**Solutions**:
1. Check Python version:
   ```bash
   python --version  # Must be 3.11+
   ```

2. Verify dependencies:
   ```bash
   pip list | grep mcp
   ```

3. Check configuration:
   ```bash
   cat .env
   ```

### Crawl4AI Connection Failed

**Problem**: Cannot reach Crawl4AI service

**Solutions**:
1. Verify service is running:
   ```bash
   curl http://localhost:5037/health
   ```

2. Check URL in configuration:
   ```bash
   grep CRAWL4AI .env
   ```

3. If using Docker:
   ```bash
   docker ps | grep crawl4ai
   docker logs crawl4ai
   ```

### Vector Search Not Working

**Problem**: Semantic search returns no results

**Solutions**:
1. Verify embeddings are generated:
   ```bash
   sqlite3 data/rag.db "SELECT COUNT(*) FROM embeddings"
   ```

2. Check embedding model is loaded:
   ```python
   from robaitragmcp.embeddings import EmbeddingModel
   model = EmbeddingModel()
   print(model.model_name)
   ```

3. Index may need rebuilding:
   ```bash
   python -m robaitragmcp.tools.reindex
   ```

### Out of Memory

**Problem**: RAM mode consuming too much memory

**Solutions**:
1. Switch to disk mode:
   ```bash
   ROBAI_DATABASE_MODE=disk
   ```

2. Reduce max RAM:
   ```bash
   ROBAI_MAX_RAM_SIZE=512MB
   ```

3. Enable cleanup:
   ```bash
   ROBAI_RETENTION_POLICY=30day
   ```

## Integration Examples

### With Claude API

```python
import anthropic
import json
from robaitragmcp.server import create_client

# Create MCP client
mcp_client = create_client("robaitragmcp")

# Use with Claude
client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    tools=[
        {
            "name": "search",
            "description": "Search indexed content",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer"}
                }
            }
        }
    ],
    messages=[
        {
            "role": "user",
            "content": "Search for information about Python asyncio"
        }
    ]
)
```

### With LM-Studio

1. Open LM-Studio settings
2. Add MCP server:
   ```
   Server: robaitragmcp
   Command: mcp run robaitragmcp.server
   ```

3. Load model and use tools in chat

## Next Steps

- [Configuration](configuration.html) - Advanced settings and tuning
- [API Reference](api-reference.html) - Complete MCP tools documentation
- [Architecture](architecture.html) - System design and internals
