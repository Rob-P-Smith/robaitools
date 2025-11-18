---
layout: default
title: robairagapi
nav_order: 7
has_children: true
---

# robairagapi

FastAPI REST bridge providing HTTP access to robaimodeltools via direct Python imports.

## Overview

robairagapi (port 8081) wraps robaimodeltools with a REST API. Direct library access - no MCP overhead.

**Key Features:**
- Direct Python imports from robaimodeltools
- REST endpoints for crawl, search, KG operations
- API key authentication + rate limiting
- CORS support
- Security middleware

## Quick Start

```bash
docker compose up -d robairagapi

curl -X POST http://localhost:8081/api/v1/search \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{"query": "python", "limit": 5}'
```

## Architecture

HTTP → FastAPI (8081) → robaimodeltools (direct import) → Crawl4AI/SQLite/Neo4j

## Main Endpoints

- POST /api/v1/search
- POST /api/v1/crawl
- POST /api/v1/deep-crawl
- POST /api/v1/kg/search
- GET /health

## Next Steps

- [Getting Started](getting-started.md)
- [API Reference](api-reference.md)
- [Configuration](configuration.md)
