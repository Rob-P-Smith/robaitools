---
layout: default
title: Configuration
parent: robaitragmcp
nav_order: 2
---

# Configuration

Complete configuration guide for robaitragmcp MCP Server.

## Environment Variables

### Database Configuration

#### ROBAI_DATABASE_MODE

**Default**: `disk`

**Description**: Storage backend mode

**Options**:
- `disk` - SQLite on disk (persistent)
- `ram` - In-memory SQLite (fast, volatile)

**Example**:
```bash
ROBAI_DATABASE_MODE=disk
```

#### ROBAI_DATABASE_PATH

**Default**: `./data/rag.db`

**Description**: SQLite database file location (disk mode only)

**Example**:
```bash
ROBAI_DATABASE_PATH=/var/lib/robai/rag.db
```

#### ROBAI_MAX_RAM_SIZE

**Default**: `1GB`

**Description**: Maximum memory for RAM mode

**Example**:
```bash
ROBAI_MAX_RAM_SIZE=4GB
```

### Crawl4AI Configuration

#### ROBAI_CRAWL4AI_URL

**Default**: `http://localhost:5037`

**Description**: Crawl4AI service endpoint

**Example**:
```bash
ROBAI_CRAWL4AI_URL=http://crawl4ai:5037
```

#### ROBAI_CRAWL4AI_TIMEOUT

**Default**: `30`

**Description**: Crawl timeout in seconds

**Example**:
```bash
ROBAI_CRAWL4AI_TIMEOUT=60
```

### Retention & Session Configuration

#### ROBAI_RETENTION_POLICY

**Default**: `permanent`

**Description**: How long to keep content

**Options**:
- `permanent` - Keep indefinitely
- `session` - Keep until session ends
- `30day` - Auto-delete after 30 days

**Example**:
```bash
ROBAI_RETENTION_POLICY=30day
```

#### ROBAI_SESSION_TIMEOUT

**Default**: `86400`

**Description**: Session timeout in seconds (24 hours)

**Example**:
```bash
ROBAI_SESSION_TIMEOUT=86400
```

### Knowledge Graph Configuration (Optional)

#### ROBAI_ENABLE_KNOWLEDGE_GRAPH

**Default**: `false`

**Description**: Enable Neo4j knowledge graph integration

**Example**:
```bash
ROBAI_ENABLE_KNOWLEDGE_GRAPH=true
```

#### NEO4J_URI

**Default**: `bolt://localhost:7687`

**Description**: Neo4j connection URI

**Example**:
```bash
NEO4J_URI=bolt://neo4j:7687
```

#### NEO4J_USER

**Default**: `neo4j`

**Description**: Neo4j username

**Example**:
```bash
NEO4J_USER=neo4j
```

#### NEO4J_PASSWORD

**Default**: `knowledge_graph_2024`

**Description**: Neo4j password

**Example**:
```bash
NEO4J_PASSWORD=secure_password
```

### Server Configuration

#### MCP_SERVER_NAME

**Default**: `robaitragmcp`

**Description**: MCP server identifier

**Example**:
```bash
MCP_SERVER_NAME=robaitragmcp
```

#### ROBAI_DEBUG

**Default**: `false`

**Description**: Enable debug logging

**Example**:
```bash
ROBAI_DEBUG=true
```

#### ROBAI_LOG_LEVEL

**Default**: `INFO`

**Description**: Logging verbosity

**Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`

**Example**:
```bash
ROBAI_LOG_LEVEL=DEBUG
```

## Configuration Examples

### Development Configuration

```bash
# Database
ROBAI_DATABASE_MODE=ram
ROBAI_MAX_RAM_SIZE=2GB

# Crawl4AI
ROBAI_CRAWL4AI_URL=http://localhost:5037
ROBAI_CRAWL4AI_TIMEOUT=30

# Session
ROBAI_RETENTION_POLICY=permanent
ROBAI_SESSION_TIMEOUT=86400

# Server
ROBAI_DEBUG=true
ROBAI_LOG_LEVEL=DEBUG
```

### Production Configuration

```bash
# Database
ROBAI_DATABASE_MODE=disk
ROBAI_DATABASE_PATH=/var/lib/robai/rag.db

# Crawl4AI
ROBAI_CRAWL4AI_URL=http://crawl4ai:5037
ROBAI_CRAWL4AI_TIMEOUT=60

# Session
ROBAI_RETENTION_POLICY=30day
ROBAI_SESSION_TIMEOUT=86400

# Knowledge Graph
ROBAI_ENABLE_KNOWLEDGE_GRAPH=true
NEO4J_URI=bolt://neo4j:7687
NEO4J_PASSWORD=<secure-password>

# Server
ROBAI_DEBUG=false
ROBAI_LOG_LEVEL=INFO
```

### High-Performance Configuration

```bash
# Database (RAM for speed)
ROBAI_DATABASE_MODE=ram
ROBAI_MAX_RAM_SIZE=8GB

# Crawl4AI
ROBAI_CRAWL4AI_TIMEOUT=120

# Aggressive session management
ROBAI_RETENTION_POLICY=session
ROBAI_SESSION_TIMEOUT=3600

# Knowledge Graph with caching
ROBAI_ENABLE_KNOWLEDGE_GRAPH=true
```

## Configuration Validation

Check configuration on startup:

```bash
python -c "from robaitragmcp.config import settings; print(f'Mode: {settings.database_mode}')"
```

## Common Configuration Patterns

### Multiple Environments

Create environment-specific files:

```bash
.env.development
.env.staging
.env.production

# Use appropriate one
cp .env.production .env
```

### Docker Deployment

Pass via environment variables:

```bash
docker run -e ROBAI_DATABASE_MODE=disk \
           -e ROBAI_DATABASE_PATH=/data/rag.db \
           robaitragmcp:latest
```

### Claude Desktop Integration

Store in `~/.claude/config.json`:

```json
{
  "mcpServers": {
    "robaitragmcp": {
      "command": "mcp",
      "args": ["run", "robaitragmcp.server"],
      "env": {
        "ROBAI_DATABASE_MODE": "disk",
        "ROBAI_DATABASE_PATH": "/home/user/.robai/rag.db",
        "ROBAI_DEBUG": "false"
      }
    }
  }
}
```

## Troubleshooting Configuration

### Invalid Mode

**Problem**: `ROBAI_DATABASE_MODE=invalid`

**Solution**:
```bash
ROBAI_DATABASE_MODE=disk  # or 'ram'
```

### Path Permissions

**Problem**: Cannot write to `ROBAI_DATABASE_PATH`

**Solution**:
```bash
# Check permissions
ls -la /var/lib/robai/

# Fix if needed
chmod 755 /var/lib/robai/
```

### Neo4j Connection

**Problem**: Cannot connect to Neo4j

**Solution**:
```bash
# Verify URI format
NEO4J_URI=bolt://localhost:7687  # Correct

# Test connection
python -c "from neo4j import GraphDatabase; GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password')).verify_connectivity()"
```

### Memory Issues

**Problem**: Out of memory with RAM mode

**Solution**:
```bash
# Reduce RAM allocation
ROBAI_MAX_RAM_SIZE=512MB

# Or switch to disk
ROBAI_DATABASE_MODE=disk
```

## Performance Tuning

### For Speed

```bash
ROBAI_DATABASE_MODE=ram
ROBAI_MAX_RAM_SIZE=8GB
ROBAI_SESSION_TIMEOUT=1800  # Shorter sessions
```

### For Persistence

```bash
ROBAI_DATABASE_MODE=disk
ROBAI_RETENTION_POLICY=permanent
ROBAI_DATABASE_PATH=/mnt/shared/rag.db  # Fast storage
```

### For Scale

```bash
# Multiple instances with shared Neo4j
ROBAI_DATABASE_MODE=disk
ROBAI_ENABLE_KNOWLEDGE_GRAPH=true
NEO4J_URI=bolt://neo4j-cluster:7687
```

## Next Steps

- [Getting Started](getting-started.html) - Installation and usage
- [API Reference](api-reference.html) - MCP tools documentation
- [Architecture](architecture.html) - System design
