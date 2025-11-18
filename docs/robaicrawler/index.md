---
layout: default
title: robaicrawler
nav_order: 3
has_children: true
---

# robaicrawler

Web content extraction service powered by Crawl4AI for intelligent RAG data ingestion.

## Overview

robaicrawler is the **foundational data ingestion layer** for the robaitools RAG system. It transforms raw HTML from any URL into clean, AI-ready markdown content through JavaScript rendering, content extraction, and boilerplate removal. The service operates as a stateless microservice with no upstream dependencies, making it the critical first step in the content processing pipeline.

**Key Capabilities:**
- **Web Scraping** - Fetches and extracts content from any URL
- **JavaScript Rendering** - Handles dynamic pages via headless Chrome
- **Content Extraction** - Converts HTML to clean, structured markdown
- **Boilerplate Removal** - Eliminates navigation, ads, and low-value content
- **Metadata Extraction** - Captures titles, descriptions, images, and links
- **Security Defense** - SSRF protection, SQL injection prevention, domain blocking

## Service Identity

- **Container Name:** robaicrawl4ai
- **Docker Image:** unclecode/crawl4ai:latest
- **Port:** 11235 (HTTP REST API)
- **Network Mode:** Host networking for low-latency communication
- **Status:** Stateless (no persistent storage)

## Architecture Position

robaicrawler sits at **Level 0** in the service dependency tree with zero upstream dependencies. All downstream services depend on it:

```
robaicrawler (Level 0) ← YOU ARE HERE
    ↓
neo4j (Level 1) - Graph database
    ↓
kg-service (Level 2) - Knowledge graph extraction
    ↓
robaitragmcp (Level 2) - MCP server with tool discovery
    ↓
robairagapi (Level 3) - REST API bridge
    ↓
open-webui (Level 4) - Chat interface
```

## Quick Links

- [Getting Started](getting-started.md) - Installation and basic usage
- [Configuration](configuration.md) - Environment variables and options
- [API Reference](api-reference.md) - HTTP endpoints and parameters
- [Architecture](architecture.md) - Data flow and integration patterns

## Use Cases

**Standard Crawling:**
- Research mode: Fetch reference documentation
- Autonomous mode: Retrieve specific URLs for analysis
- Direct tool use: One-off content extraction

**Deep Crawling:**
- Multi-page documentation sites
- Blog archives and article series
- Comprehensive topic research (up to 250 pages)

**Integration Patterns:**
- MCP tool calls from robaitragmcp
- REST API calls from robairagapi
- Research orchestration from robaiproxy

## Data Flow Summary

```
User Request → robaiproxy/robairagapi
    ↓
MCP Server (robaitragmcp)
    ↓
Crawl4AIRAG Facade (robaimodeltools)
    ↓
robaicrawler Service (Port 11235)
    ↓ (Returns markdown + metadata)
Security Checks + Content Cleaning
    ↓
SQLite Storage (crawled_content table)
    ↓
Embedding Generation (384-dim vectors)
    ↓
Knowledge Graph Queue (kg-service)
```

## Performance Characteristics

- **Single URL crawl:** 2-10 seconds
- **Content cleaning:** 100-500ms
- **Embedding generation:** 500ms-2 seconds
- **Deep crawl (50 pages):** 30-60 seconds with rate limiting
- **Concurrent requests:** Supported (multiple simultaneous crawls)

## Next Steps

1. **New Users:** Start with [Getting Started](getting-started.md) for installation and first crawl
2. **Integrators:** Review [Architecture](architecture.md) for data flow and integration points
3. **Operators:** Check [Configuration](configuration.md) for environment variables and tuning
4. **Developers:** See [API Reference](api-reference.md) for endpoint details and parameters
