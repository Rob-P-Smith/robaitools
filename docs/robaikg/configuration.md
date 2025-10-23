---
layout: default
title: Configuration
parent: robaikg
nav_order: 2
---

# Configuration

Complete configuration reference for robaikg Knowledge Graph service.

## Overview

robaikg uses environment variables for configuration, loaded from a `.env` file in the robaikg directory. The configuration system includes validation, default values, and integrates with FastAPI and Neo4j.

## Configuration File

### Location

```
robaikg/
  ├── .env              # Your configuration (not committed)
  ├── .env.example      # Template with documentation
  └── kg-service/
      └── config.py     # Configuration loader
```

### Creating Configuration

```bash
# Copy template
cp .env.example .env

# Edit with your settings
nano .env
```

## Environment Variables

### Service Configuration

Configure service identification and runtime mode.

#### SERVICE_NAME

**Default**: `kg-service`

**Description**: Service identifier (used in logs and API responses)

**Example**:
```bash
SERVICE_NAME=kg-service
```

#### SERVICE_VERSION

**Default**: `1.0.0`

**Description**: Service version string

**Example**:
```bash
SERVICE_VERSION=1.0.0
```

#### DEBUG

**Default**: `false`

**Description**: Enable debug mode (verbose logging, auto-reload)

**Example**:
```bash
DEBUG=true  # Development only
```

#### LOG_LEVEL

**Default**: `INFO`

**Description**: Logging verbosity level

**Example**:
```bash
LOG_LEVEL=INFO
```

**Options**:
- `DEBUG` - Detailed debugging information
- `INFO` - General informational messages (recommended)
- `WARNING` - Warning messages only
- `ERROR` - Error messages only
- `CRITICAL` - Critical errors only

**Recommended Values**:
- Development: `DEBUG`
- Production: `INFO`
- Troubleshooting: `DEBUG`

### API Configuration

Configure HTTP server settings.

#### API_HOST

**Default**: `0.0.0.0`

**Description**: Network interface to bind to

**Example**:
```bash
API_HOST=0.0.0.0
```

**Options**:
- `0.0.0.0` - All interfaces (default)
- `127.0.0.1` - Localhost only (development)
- Specific IP - Bind to specific interface

#### API_PORT

**Default**: `8088`

**Description**: Port number for the service

**Example**:
```bash
API_PORT=8088
```

**Notes**:
- Must not conflict with other services
- Ensure firewall allows traffic if remote access needed

### Neo4j Configuration

Configure Neo4j graph database connection.

#### NEO4J_URI

**Default**: `bolt://neo4j-kg:7687`

**Description**: Neo4j connection URI (Bolt protocol)

**Example**:
```bash
NEO4J_URI=bolt://localhost:7687
```

**Notes**:
- Include `bolt://` protocol prefix
- For remote Neo4j: `bolt://neo4j-host:7687`
- For TLS: Use `bolt+s://` instead of `bolt://`

#### NEO4J_USER

**Default**: `neo4j`

**Description**: Neo4j database username

**Example**:
```bash
NEO4J_USER=neo4j
```

#### NEO4J_PASSWORD

**Default**: `knowledge_graph_2024`

**Description**: Neo4j database password

**Example**:
```bash
NEO4J_PASSWORD=knowledge_graph_2024
```

**Security Note**: Always override in production via environment variable

#### NEO4J_DATABASE

**Default**: `neo4j`

**Description**: Neo4j database name

**Example**:
```bash
NEO4J_DATABASE=neo4j
```

#### NEO4J_MAX_CONNECTION_LIFETIME

**Default**: `3600`

**Description**: Connection lifetime in seconds before recreation

**Example**:
```bash
NEO4J_MAX_CONNECTION_LIFETIME=3600
```

**Notes**: Not configurable via environment (fixed in config.py)

#### NEO4J_MAX_CONNECTION_POOL_SIZE

**Default**: `50`

**Description**: Maximum connections in pool

**Example**:
```bash
NEO4J_MAX_CONNECTION_POOL_SIZE=50
```

**Recommended Values**:
- Small systems: 10-20
- Medium systems: 30-50
- Large systems: 50-100

#### NEO4J_CONNECTION_TIMEOUT

**Default**: `30`

**Description**: Connection timeout in seconds

**Example**:
```bash
NEO4J_CONNECTION_TIMEOUT=30
```

### vLLM Configuration

Configure vLLM inference server for relationship extraction.

#### VLLM_BASE_URL

**Default**: `http://localhost:8078`

**Description**: vLLM API base URL

**Example**:
```bash
VLLM_BASE_URL=http://localhost:8078
```

**Notes**:
- Required for relationship extraction
- Used for LLM inference (relationship discovery)

#### VLLM_TIMEOUT

**Default**: `1800`

**Description**: Timeout in seconds for vLLM requests

**Example**:
```bash
VLLM_TIMEOUT=1800
```

**Notes**:
- 1800 seconds = 30 minutes
- Set higher for large documents
- Lower values fail faster on network issues

**Recommended Values**:
- Entity extraction only: `300` (5 minutes)
- Standard operation: `1800` (30 minutes)
- Deep analysis: `3600` (1 hour)

#### VLLM_MAX_RETRIES

**Default**: `3`

**Description**: Number of retry attempts on failure

**Example**:
```bash
VLLM_MAX_RETRIES=3
```

#### VLLM_RETRY_INTERVAL

**Default**: `30`

**Description**: Seconds between retry attempts

**Example**:
```bash
VLLM_RETRY_INTERVAL=30
```

### GLiNER Configuration

Configure GLiNER model for entity extraction.

#### GLINER_MODEL

**Default**: `urchade/gliner_large-v2.1`

**Description**: HuggingFace model ID for entity extraction

**Example**:
```bash
GLINER_MODEL=urchade/gliner_large-v2.1
```

**Notes**:
- Model automatically downloaded on first use
- ~4GB download, requires 4GB RAM
- Alternative: `urchade/gliner_base-v0.9` (smaller, faster)

#### GLINER_THRESHOLD

**Default**: `0.45`

**Description**: Confidence threshold for entity extraction (0.0-1.0)

**Example**:
```bash
GLINER_THRESHOLD=0.45
```

**Recommended Values**:
- High recall (more entities): `0.3`
- Balanced (default): `0.45`
- High precision (fewer entities): `0.6`

#### GLINER_BATCH_SIZE

**Default**: `8`

**Description**: Batch size for model processing

**Example**: Not configurable via environment (fixed at 8)

#### GLINER_MAX_LENGTH

**Default**: `384`

**Description**: Maximum token length for GLiNER (model limit)

**Example**: Not configurable via environment (fixed at 384)

### Entity Extraction Settings

#### ENTITY_MIN_CONFIDENCE

**Default**: `0.4` (linked to GLINER_THRESHOLD)

**Description**: Minimum confidence for extracted entities

**Example**:
```bash
GLINER_THRESHOLD=0.4
```

**Notes**: Uses same value as GLINER_THRESHOLD

#### ENTITY_DEDUPLICATION

**Default**: `True`

**Description**: Enable entity deduplication

**Example**: Not configurable via environment (always enabled)

### Relationship Extraction Settings

#### RELATION_MIN_CONFIDENCE

**Default**: `0.45`

**Description**: Minimum confidence for relationships (0.0-1.0)

**Example**:
```bash
RELATION_MIN_CONFIDENCE=0.45
```

**Recommended Values**:
- High recall: `0.3`
- Balanced (default): `0.45`
- High precision: `0.7`

#### RELATION_MAX_DISTANCE

**Default**: `3`

**Description**: Maximum sentence distance for relationships

**Example**: Not configurable via environment (fixed at 3)

#### RELATION_CONTEXT_WINDOW

**Default**: `200`

**Description**: Characters of context for relationship extraction

**Example**: Not configurable via environment (fixed at 200)

### Processing Settings

#### MAX_CONCURRENT_REQUESTS

**Default**: `8`

**Description**: Maximum parallel document processing requests

**Example**: Not configurable via environment (fixed at 8)

**Recommended Values**:
- Single machine: 2-4
- High-capacity machine: 4-8
- Cluster: 8-16

#### REQUEST_TIMEOUT

**Default**: `300`

**Description**: Timeout for individual requests in seconds

**Example**: Not configurable via environment (fixed at 300)

#### ENABLE_ASYNC_PROCESSING

**Default**: `True`

**Description**: Enable async/await throughout service

**Example**: Not configurable via environment (always enabled)

### Document Processing

#### MAX_DOCUMENT_LENGTH

**Default**: `100000`

**Description**: Maximum document size in characters

**Example**: Not configurable via environment (fixed at 100,000)

#### CHUNK_SIZE

**Default**: `2000`

**Description**: Character size for document chunks in GLiNER processing

**Example**: Not configurable via environment (fixed at 2000)

#### CHUNK_OVERLAP

**Default**: `200`

**Description**: Character overlap between chunks

**Example**: Not configurable via environment (fixed at 200)

## Complete Configuration Examples

### Development Configuration

```bash
# Service
SERVICE_NAME=kg-service
SERVICE_VERSION=1.0.0
DEBUG=true
LOG_LEVEL=DEBUG

# API
API_HOST=127.0.0.1
API_PORT=8088

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=knowledge_graph_2024
NEO4J_DATABASE=neo4j
NEO4J_MAX_CONNECTION_POOL_SIZE=10

# vLLM
VLLM_BASE_URL=http://localhost:8078
VLLM_TIMEOUT=300

# GLiNER
GLINER_MODEL=urchade/gliner_large-v2.1
GLINER_THRESHOLD=0.45

# Relationships
RELATION_MIN_CONFIDENCE=0.45
```

### Production Configuration

```bash
# Service
SERVICE_NAME=kg-service
SERVICE_VERSION=1.0.0
DEBUG=false
LOG_LEVEL=INFO

# API
API_HOST=0.0.0.0
API_PORT=8088

# Neo4j
NEO4J_URI=bolt://neo4j-cluster:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<secure-password-here>
NEO4J_DATABASE=neo4j
NEO4J_MAX_CONNECTION_POOL_SIZE=50

# vLLM
VLLM_BASE_URL=http://vllm-service:8078
VLLM_TIMEOUT=1800

# GLiNER
GLINER_MODEL=urchade/gliner_large-v2.1
GLINER_THRESHOLD=0.45

# Relationships
RELATION_MIN_CONFIDENCE=0.5
```

### High-Precision Configuration

For fewer, higher-confidence entities and relationships:

```bash
# Stricter thresholds
GLINER_THRESHOLD=0.60
RELATION_MIN_CONFIDENCE=0.70

# Longer timeouts for thorough analysis
VLLM_TIMEOUT=3600

# Connection pool for high concurrency
NEO4J_MAX_CONNECTION_POOL_SIZE=80
```

### High-Recall Configuration

For more entities and relationships:

```bash
# Lenient thresholds
GLINER_THRESHOLD=0.30
RELATION_MIN_CONFIDENCE=0.30

# Faster processing
VLLM_TIMEOUT=900

# Standard connection pool
NEO4J_MAX_CONNECTION_POOL_SIZE=50
```

## Configuration Validation

The configuration system validates critical settings on startup.

### Required Variables

**Service starts only if set**:
- None (all have defaults)

**Recommended to set**:
- `NEO4J_PASSWORD` - Override production default
- `VLLM_BASE_URL` - If vLLM on different host

### Validation at Startup

```python
# config.py performs validation
from kg-service.config import settings

# Access configuration
print(settings.NEO4J_URI)
print(settings.VLLM_BASE_URL)
print(settings.GLINER_THRESHOLD)
```

### Common Configuration Issues

**Issue**: "Connection refused" to Neo4j
```bash
# Verify URI format
NEO4J_URI=bolt://localhost:7687  # Correct
NEO4J_URI=http://localhost:7474  # Wrong (wrong protocol)
```

**Issue**: vLLM not found
```bash
# Verify URL format
VLLM_BASE_URL=http://localhost:8078  # Correct
VLLM_BASE_URL=http://localhost:8078/v1  # Wrong
```

**Issue**: Slow entity extraction
```bash
# Increase threshold to reduce entities
GLINER_THRESHOLD=0.60  # Was 0.45
```

## Security Considerations

### API Key Security

**Storage**:
```bash
# Never commit .env to version control
# .gitignore already excludes it

# Use secure password generation
openssl rand -hex 32
```

**Environment**:
```bash
# Restrict file permissions
chmod 600 .env

# Verify not committed
git status  # .env should not appear
```

### Network Security

**Recommendations**:
- Use `API_HOST=127.0.0.1` for local-only access
- Configure firewall for remote Neo4j access
- Use TLS for Neo4j in production (`bolt+s://`)
- Keep vLLM on internal network
- Implement API gateway for authentication

### Service Security

**Best Practices**:
- Rotate NEO4J_PASSWORD regularly
- Use different configs for dev/staging/production
- Monitor service logs for suspicious activity
- Limit concurrent requests appropriately
- Keep dependencies updated

## Environment-Specific Configs

### Create Environment-Specific Files

```bash
# Create configs for each environment
.env.development
.env.staging
.env.production

# Use appropriate config
cp .env.production .env
```

### Docker Deployment

Pass configuration via environment variables:

```bash
docker run -e GLINER_THRESHOLD=0.45 \
           -e VLLM_BASE_URL=http://vllm:8078 \
           -e NEO4J_PASSWORD=secure-password \
           kg-service
```

### Docker Compose

Define in `docker-compose.yml`:

```yaml
kg-service:
  image: kg-service:latest
  environment:
    GLINER_THRESHOLD: "0.45"
    VLLM_BASE_URL: "http://vllm:8078"
    NEO4J_URI: "bolt://neo4j:7687"
```

## Performance Tuning

### For Large-Scale Processing

```bash
# Increase Neo4j connections
NEO4J_MAX_CONNECTION_POOL_SIZE=100

# Higher timeout for large documents
VLLM_TIMEOUT=3600

# Lenient entity extraction
GLINER_THRESHOLD=0.35
```

### For Speed (Fewer Entities)

```bash
# Reduce Neo4j connections
NEO4J_MAX_CONNECTION_POOL_SIZE=10

# Shorter timeout
VLLM_TIMEOUT=600

# Strict entity extraction
GLINER_THRESHOLD=0.65
```

### For Memory Optimization

```bash
# Lower threshold to reduce stored entities
GLINER_THRESHOLD=0.50

# Reduce relationship confidence
RELATION_MIN_CONFIDENCE=0.60

# Minimize Neo4j connections
NEO4J_MAX_CONNECTION_POOL_SIZE=20
```

## Configuration Validation Script

Check configuration without starting service:

```bash
# Validate .env file exists and is readable
python3 -c "from kg-service.config import settings; print('Config OK')"
```

## Logging Configuration

### Console Output Format

```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

Example:
```
2025-10-17 14:32:18,234 - kg-service - INFO - Service starting
```

### File Logging

**Location**: `kg-service.log`

**Format**: Detailed with function names and line numbers

**Rotation**: 10MB files with 5 backups (50MB max)

## Troubleshooting Configuration

### Missing Configuration

**Problem**: Service fails to start with config error

**Solution**:
```bash
# Check .env exists
ls -la .env

# Verify required settings
grep NEO4J_URI .env
grep VLLM_BASE_URL .env

# Generate from example if missing
cp .env.example .env
```

### Connection Failures

**Problem**: Cannot connect to Neo4j or vLLM

**Solution**:
```bash
# Verify URLs are correct
curl bolt://localhost:7687 2>&1 | head -5
curl http://localhost:8078/v1/models

# Update .env if needed
nano .env
```

### Performance Issues

**Problem**: Slow entity/relationship extraction

**Solution**:
```bash
# Increase thresholds
GLINER_THRESHOLD=0.60
RELATION_MIN_CONFIDENCE=0.60

# Reduce timeout if stuck
VLLM_TIMEOUT=600
```

## Next Steps

- [Getting Started](getting-started.html) - Installation and usage
- [API Reference](api-reference.html) - Complete API documentation
- [Architecture](architecture.html) - Understanding the system design
