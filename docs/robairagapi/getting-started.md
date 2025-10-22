---
layout: default
title: Getting Started
parent: robairagapi
nav_order: 1
---

# Getting Started with robairagapi

Quick installation and setup guide for robairagapi.

## Prerequisites

- Python 3.11+
- robaimodeltools installed and configured
- Crawl4AI service running on port 11235
- SQLite database access
- Docker (optional, for containerized deployment)

## Installation

### Step 1: Navigate to Directory

```bash
cd /path/to/robaitools/robairagapi
```

### Step 2: Install Dependencies

```bash
# Install Python packages (7 packages)
pip install -r requirements.txt

# Install robaimodeltools dependencies
pip install -r ../robaimodeltools/requirements.txt
```

**Key Dependencies**:
- fastapi==0.115.6
- uvicorn==0.32.1
- pydantic==2.10.4
- python-dotenv==1.0.1
- httpx==0.28.1
- gunicorn==23.0.0

### Step 3: Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit with your settings
nano .env
```

**Minimum Required Configuration**:

```bash
# At least ONE API key required
LOCAL_API_KEY=your-secret-api-key-here

# Optional settings
SERVER_HOST=0.0.0.0
SERVER_PORT=8080
RATE_LIMIT_PER_MINUTE=60
ENABLE_RATE_LIMIT=true
ENABLE_CORS=true
LOG_LEVEL=INFO
```

### Step 4: Verify Dependencies

```bash
# Check Crawl4AI is running
curl http://localhost:11235/health

# Check robaimodeltools database exists
ls -lh ../robaimodeltools/crawl4ai_rag.db
```

### Step 5: Start the Service

**Development Mode**:
```bash
python main.py
```

**Production Mode** (single worker):
```bash
uvicorn api.server:app --host 0.0.0.0 --port 8080
```

**Production Mode** (multiple workers):
```bash
gunicorn api.server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8080
```

### Step 6: Verify Installation

```bash
# Check health
curl http://localhost:8080/health

# Expected response:
# {
#   "status": "healthy",
#   "timestamp": "2024-01-15T10:30:45.123456",
#   "mcp_connected": true,
#   "version": "1.0.0"
# }

# View API documentation
open http://localhost:8080/docs
```

## Basic Usage

### Authentication

All endpoints except `/health` and `/api/v1/help` require Bearer token authentication:

```bash
# Set your API key
export API_KEY="your-api-key-from-env-file"

# Use in requests
curl -H "Authorization: Bearer $API_KEY" \
  http://localhost:8080/api/v1/status
```

### Example 1: Crawl and Store URL

```bash
curl -X POST http://localhost:8080/api/v1/crawl/store \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://fastapi.tiangolo.com/tutorial/",
    "tags": "python,api,tutorial",
    "retention_policy": "permanent"
  }'
```

**Response**:
```json
{
  "success": true,
  "data": {
    "url": "https://fastapi.tiangolo.com/tutorial/",
    "title": "Tutorial - User Guide - FastAPI",
    "content": "Extracted text content...",
    "markdown": "# Tutorial...",
    "content_id": 123,
    "stored": true,
    "retention_policy": "permanent",
    "tags": ["python", "api", "tutorial"]
  },
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

### Example 2: Simple Search

```bash
curl -X POST http://localhost:8080/api/v1/search \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "FastAPI authentication patterns",
    "limit": 5,
    "tags": "python,api"
  }'
```

**Response**:
```json
{
  "success": true,
  "data": {
    "query": "FastAPI authentication patterns",
    "results": [
      {
        "content_id": 123,
        "url": "https://fastapi.tiangolo.com/tutorial/security/",
        "title": "Security - FastAPI",
        "chunk_text": "FastAPI provides several tools...",
        "similarity_score": 0.92,
        "tags": ["python", "api"]
      }
    ],
    "count": 5
  },
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

### Example 3: Deep Crawl

```bash
curl -X POST http://localhost:8080/api/v1/crawl/deep/store \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://docs.python.org/3/tutorial/",
    "max_depth": 2,
    "max_pages": 10,
    "include_external": false,
    "tags": "python,documentation",
    "retention_policy": "permanent"
  }'
```

**Response**:
```json
{
  "success": true,
  "data": {
    "root_url": "https://docs.python.org/3/tutorial/",
    "pages_crawled": 10,
    "urls": [
      "https://docs.python.org/3/tutorial/introduction.html",
      "https://docs.python.org/3/tutorial/controlflow.html",
      ...
    ],
    "content_ids": [124, 125, 126, ...],
    "timestamp": "2024-01-15T10:35:20.654321"
  }
}
```

### Example 4: Enhanced Search (Full Pipeline)

```bash
curl -X POST http://localhost:8080/api/v1/search/enhanced \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "React performance optimization techniques",
    "tags": "javascript,react"
  }'
```

**Response** (returns exactly 3 results with full markdown):
```json
{
  "success": true,
  "data": {
    "query": "React performance optimization techniques",
    "rag_results": [
      {
        "content_id": 150,
        "url": "https://react.dev/learn/...",
        "title": "Optimizing Performance - React",
        "markdown": "# Full markdown content with all formatting...",
        "similarity_score": 0.95
      },
      ...
    ],
    "kg_results": [
      {
        "entity": "Virtual DOM",
        "type": "Concept",
        "confidence": 0.88,
        "referenced_chunks": [1, 3, 5]
      },
      ...
    ],
    "rag_count": 3,
    "kg_count": 5
  }
}
```

## Python Client Examples

### Installation

```bash
pip install requests
```

### Basic Crawling

```python
import requests

url = "http://localhost:8080/api/v1/crawl/store"
headers = {
    "Authorization": "Bearer your-api-key",
    "Content-Type": "application/json"
}
data = {
    "url": "https://example.com/article",
    "tags": "example,test",
    "retention_policy": "permanent"
}

response = requests.post(url, headers=headers, json=data)
result = response.json()

if result["success"]:
    print(f"Stored: {result['data']['title']}")
    print(f"Content ID: {result['data']['content_id']}")
else:
    print(f"Error: {result.get('error', 'Unknown error')}")
```

### Simple Search

```python
url = "http://localhost:8080/api/v1/search"
data = {
    "query": "machine learning basics",
    "limit": 10,
    "tags": "ai,tutorial"
}

response = requests.post(url, headers=headers, json=data)
results = response.json()

for item in results["data"]["results"]:
    print(f"[{item['similarity_score']:.2f}] {item['title']}")
    print(f"  URL: {item['url']}")
    print(f"  Preview: {item['chunk_text'][:100]}...")
    print()
```

### Memory Management

```python
# List all stored content
response = requests.get(
    "http://localhost:8080/api/v1/memory?limit=50",
    headers=headers
)
content = response.json()

print(f"Total items: {content['count']}")
for item in content["content"]:
    print(f"- {item['title']} ({item['word_count']} words)")

# Delete specific URL
response = requests.delete(
    "http://localhost:8080/api/v1/memory?url=https://example.com/old",
    headers=headers
)
print(response.json()["message"])
```

### Domain Blocking

```python
# Add block
data = {
    "pattern": "*.spam.com",
    "description": "Known spam domain"
}
response = requests.post(
    "http://localhost:8080/api/v1/blocked-domains",
    headers=headers,
    json=data
)
print(response.json()["message"])

# List blocks
response = requests.get(
    "http://localhost:8080/api/v1/blocked-domains",
    headers=headers
)
for block in response.json()["blocked_domains"]:
    print(f"- {block['pattern']}: {block['keyword']}")
```

## Docker Deployment

### Build Image

```bash
# From project root
cd /path/to/robaitools

docker build -t robairagapi:latest -f robairagapi/Dockerfile .
```

### Run Container

```bash
docker run -d \
  --name robairagapi \
  --network host \
  -e LOCAL_API_KEY=your-secret-key \
  -e SERVER_PORT=8080 \
  -e RATE_LIMIT_PER_MINUTE=60 \
  robairagapi:latest
```

### Check Status

```bash
# View logs
docker logs -f robairagapi

# Check health
curl http://localhost:8080/health

# Stop container
docker stop robairagapi

# Remove container
docker rm robairagapi
```

### Docker Compose

```yaml
services:
  robairagapi:
    build:
      context: .
      dockerfile: robairagapi/Dockerfile
    image: robairagapi:latest
    container_name: robairagapi
    network_mode: "host"
    restart: unless-stopped
    environment:
      - LOCAL_API_KEY=${LOCAL_API_KEY}
      - RATE_LIMIT_PER_MINUTE=60
      - SERVER_PORT=8080
      - LOG_LEVEL=INFO
```

**Start with compose**:
```bash
docker compose up -d robairagapi
```

## Testing Your Installation

### Health Check

```bash
# Should return immediately
curl http://localhost:8080/health

# Expected: {"status": "healthy", ...}
```

### API Documentation

Visit `http://localhost:8080/docs` for interactive API documentation (Swagger UI).

### Rate Limiting Test

```bash
# Send 61 requests quickly
for i in {1..61}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -H "Authorization: Bearer $API_KEY" \
    http://localhost:8080/api/v1/status
done

# Should see: 200 (60 times) then 429
```

### Full Workflow Test

```bash
# 1. Crawl and store
curl -X POST http://localhost:8080/api/v1/crawl/store \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://httpbin.org/html", "tags": "test"}'

# 2. Search for it
curl -X POST http://localhost:8080/api/v1/search \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "test content", "tags": "test", "limit": 5}'

# 3. List memory
curl -H "Authorization: Bearer $API_KEY" \
  "http://localhost:8080/api/v1/memory?limit=10"

# 4. Delete it
curl -X DELETE \
  -H "Authorization: Bearer $API_KEY" \
  "http://localhost:8080/api/v1/memory?url=https://httpbin.org/html"
```

## Troubleshooting

### Service Won't Start

**Problem**: `python main.py` fails

**Solutions**:
1. Check dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Verify .env file exists and has API key
3. Check port 8080 is not in use:
   ```bash
   lsof -i :8080
   ```

### Authentication Fails

**Problem**: 403 Forbidden or "Not authenticated"

**Solutions**:
1. Verify API key in .env:
   ```bash
   grep LOCAL_API_KEY .env
   ```
2. Use correct header:
   ```bash
   Authorization: Bearer your-api-key
   ```
3. Check key matches exactly (no extra spaces)

### Crawl4AI Connection Error

**Problem**: "Failed to connect to Crawl4AI service"

**Solutions**:
1. Verify Crawl4AI is running:
   ```bash
   curl http://localhost:11235/health
   ```
2. Start Crawl4AI if needed
3. Check network connectivity

### Rate Limit Issues

**Problem**: Getting 429 responses frequently

**Solutions**:
1. Increase limit in .env:
   ```bash
   RATE_LIMIT_PER_MINUTE=120
   ```
2. Use multiple API keys for higher throughput
3. Implement client-side rate limiting

### Database Errors

**Problem**: SQLite errors or missing data

**Solutions**:
1. Verify database exists:
   ```bash
   ls -lh ../robaimodeltools/crawl4ai_rag.db
   ```
2. Check file permissions
3. Ensure robaimodeltools is properly installed

## Performance Tips

1. **Use Simple Search** when possible (faster than KG/Enhanced)
2. **Enable Rate Limiting** to protect backend
3. **Use Multiple Workers** in production:
   ```bash
   gunicorn --workers 4 ...
   ```
4. **Tag Content** for faster filtered searches
5. **Use Docker** for consistent deployment

## Next Steps

- [Configuration](configuration.html) - Detailed configuration options
- [API Reference](api-reference.html) - Complete endpoint documentation
- [Architecture](architecture.html) - System design and patterns
