---
layout: home
title: Home
nav_order: 1
description: "RobAI Tools - A comprehensive suite of AI-powered tools for web crawling, knowledge graph generation, and RAG-based question answering."
permalink: /
---

# RobAI Tools Documentation

Welcome to the RobAI Tools documentation. This ecosystem provides a complete pipeline for web content extraction, knowledge graph construction, and retrieval-augmented generation (RAG).

## System Overview

RobAI Tools is a microservices-based platform that combines:

- **Web Crawling** - Intelligent content extraction
- **Knowledge Graphs** - Entity and relationship mapping
- **Vector Retrieval** - Semantic search capabilities
- **LLM Integration** - AI-powered reasoning and response generation
- **REST APIs** - Easy integration with external systems
- **User Interfaces** - Chat-based interaction

## Architecture

The system consists of 10 interconnected services that work together to provide comprehensive AI capabilities:

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Web UI     │────▶│   RAG API    │────▶│  TRAG MCP   │
└─────────────┘     └──────────────┘     └─────────────┘
                                                  │
                           ┌──────────────────────┴─────────┐
                           ▼                                ▼
                    ┌─────────────┐                 ┌─────────────┐
                    │ KG Service  │                 │  Crawler    │
                    └─────────────┘                 └─────────────┘
                           │
                           ▼
                    ┌─────────────┐                 ┌─────────────┐
                    │   Neo4j     │                 │    vLLM     │
                    └─────────────┘                 └─────────────┘
```

## Projects

Explore the documentation for each component:

### Core Services

- [**robaivllm**](robaivllm/) - LLM inference service using vLLM
- [**robaicrawler**](robaicrawler/) - Web content extraction with Crawl4AI
- [**robaikg**](robaikg/) - Knowledge graph extraction and management
- [**robaitragmcp**](robaitragmcp/) - MCP server for RAG and knowledge graph integration

### API & Integration

- [**robairagapi**](robairagapi/) - REST API bridge for external integrations
- [**robairagmcpremoteclient**](robairagmcpremoteclient/) - Remote client for MCP server
- [**robaiproxy**](robaiproxy/) - Proxy service for request routing

### Supporting Components

- [**robaidata**](robaidata/) - Shared data management
- [**robaimodeltools**](robaimodeltools/) - Model utilities and tools
- [**robaiwebui**](robaiwebui/) - Web-based chat interface

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git
- At least 16GB RAM (32GB recommended for LLM)
- GPU with 12GB+ VRAM (for local LLM inference)

### Installation

```bash
# Clone the repository
git clone https://github.com/Rob-P-Smith/robaitools.git
cd robaitools

# Copy environment configuration
cp .env.example .env

# Start all services
docker compose up -d

# Check service status
docker compose ps
```

### Accessing Services

Once running, you can access:

- **Web UI**: http://localhost:80
- **RAG API**: http://localhost:8080
- **KG Service**: http://localhost:8088
- **Neo4j Browser**: http://localhost:7474
- **vLLM API**: http://localhost:8078

## Documentation Structure

Each project section contains:

- **Overview** - Purpose and capabilities
- **Getting Started** - Installation and setup
- **Configuration** - Environment variables and settings
- **API Reference** - Endpoints and usage examples
- **Architecture** - Design decisions and implementation details

## Contributing

Documentation contributions are welcome! To contribute:

1. Fork the repository
2. Create a feature branch
3. Add or update documentation in the `docs/` directory
4. Submit a pull request

## Support

- **Issues**: [GitHub Issues](https://github.com/Rob-P-Smith/robaitools/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Rob-P-Smith/robaitools/discussions)

---

**Note**: This documentation site is built with [Just the Docs](https://just-the-docs.github.io/just-the-docs/), a documentation theme for Jekyll.
