---
layout: default
title: Configuration
parent: robaiproxy
nav_order: 2
---

# Configuration

Complete configuration reference for robaiproxy.

## Overview

robaiproxy uses environment variables for configuration, loaded from a `.env` file in the robaiproxy directory. The configuration system includes validation, default values, and masked logging for security.

## Configuration File

### Location

```
robaiproxy/
  ├── .env              # Your configuration (not committed)
  ├── .env.example      # Template with documentation
  └── config.py         # Configuration loader
```

### Creating Configuration

```bash
# Copy template
cp .env.example .env

# Edit with your settings
nano .env
```

## Environment Variables

### vLLM Backend

Configure the vLLM language model backend.

#### VLLM_BASE_URL

**Default**: `http://localhost:8078/v1`

**Description**: Base URL for the vLLM backend API (including `/v1` suffix)

**Example**:
```bash
VLLM_BASE_URL=http://localhost:8078/v1
```

**Notes**:
- Must include the `/v1` path suffix
- Used for chat completions and model queries
- Derived value `VLLM_BACKEND_URL` automatically removes `/v1` for health checks

#### VLLM_TIMEOUT

**Default**: `300`

**Description**: Timeout in seconds for vLLM requests

**Example**:
```bash
VLLM_TIMEOUT=300
```

**Notes**:
- Applies to chat completions and streaming requests
- Set higher for complex research queries
- Lower values may cause timeouts during long generations

**Recommended Values**:
- Development: `300` (5 minutes)
- Production: `600` (10 minutes)
- Research mode: `900` (15 minutes)

### MCP RAG Server

Configure the MCP RAG server for knowledge base operations.

#### REST_API_URL

**Default**: `http://localhost:8080/api/v1`

**Description**: Base URL for the MCP RAG server API

**Example**:
```bash
REST_API_URL=http://localhost:8080/api/v1
```

**Notes**:
- Required for research mode
- Used for knowledge base search and URL crawling
- Must be accessible from robaiproxy

#### REST_API_KEY

**Default**: None (required)

**Description**: Bearer token for MCP RAG server authentication

**Example**:
```bash
REST_API_KEY=your_secure_api_key_here_minimum_32_chars
```

**Notes**:
- **REQUIRED** - Service will fail validation if missing
- Used as Bearer token in Authorization header
- Should be 32+ characters for security
- Same key configured in MCP RAG server
- Generate with: `openssl rand -hex 32`

#### MCP_TIMEOUT

**Default**: `60`

**Description**: Timeout in seconds for MCP RAG server requests

**Example**:
```bash
MCP_TIMEOUT=60
```

**Notes**:
- Applies to search and crawl operations
- Crawling may take longer than searches
- Increase if experiencing timeouts

**Recommended Values**:
- Knowledge base search: `30`
- URL crawling: `60-90`
- Deep research: `120`

### External APIs

Configure external web search services.

#### SERPER_API_KEY

**Default**: None (required)

**Description**: API key for Serper web search service

**Example**:
```bash
SERPER_API_KEY=your_serper_api_key_from_serper_dev
```

**Notes**:
- **REQUIRED** - Service will fail validation if missing
- Obtain from [https://serper.dev](https://serper.dev)
- Required for research mode
- Free tier available with rate limits
- Paid tiers offer higher limits

#### SERPER_TIMEOUT

**Default**: `30`

**Description**: Timeout in seconds for Serper API requests

**Example**:
```bash
SERPER_TIMEOUT=30
```

**Notes**:
- Serper typically responds quickly (< 5 seconds)
- Increase if experiencing frequent timeouts
- Lower values fail faster on network issues

### Research Limits

Configure concurrent research request limits.

#### MAX_STANDARD_RESEARCH

**Default**: `3`

**Description**: Maximum concurrent standard research requests (2 iterations)

**Example**:
```bash
MAX_STANDARD_RESEARCH=3
```

**Notes**:
- Controls semaphore size for standard research
- Higher values = more concurrent requests
- Consider backend capacity
- Each request consumes significant resources

**Recommended Values**:
- Small systems: `1-2`
- Medium systems: `3-5`
- Large systems: `5-10`

#### MAX_DEEP_RESEARCH

**Default**: `1`

**Description**: Maximum concurrent deep research requests (4 iterations)

**Example**:
```bash
MAX_DEEP_RESEARCH=1
```

**Notes**:
- Controls semaphore size for deep research
- Deep research is resource-intensive
- Recommended to keep at `1` unless you have high capacity
- Each deep research can generate 100K+ token contexts

**Recommended Values**:
- Most systems: `1`
- High-capacity systems: `2`
- Cluster environments: `3+`

### Server Configuration

Configure the robaiproxy server itself.

#### HOST

**Default**: `0.0.0.0`

**Description**: Network interface to bind to

**Example**:
```bash
HOST=0.0.0.0
```

**Options**:
- `0.0.0.0` - All interfaces (default, recommended)
- `127.0.0.1` - Localhost only (development)
- Specific IP - Bind to specific interface

#### PORT

**Default**: `8079`

**Description**: Port number for the proxy service

**Example**:
```bash
PORT=8079
```

**Notes**:
- Must not conflict with other services
- Standard port: `8079`
- Ensure firewall allows traffic if remote access needed

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

### Feature Flags

Configure optional features and behaviors.

#### AUTO_DETECT_MODEL

**Default**: `true`

**Description**: Enable automatic model detection from vLLM

**Example**:
```bash
AUTO_DETECT_MODEL=true
```

**Notes**:
- When enabled, polls vLLM for model name
- Caches model name for fast access
- Disabling may speed up startup if model name known
- Background task monitors model availability

#### MODEL_POLL_INTERVAL

**Default**: `2`

**Description**: Interval in seconds for model availability polling

**Example**:
```bash
MODEL_POLL_INTERVAL=2
```

**Notes**:
- Used during startup until model loads
- Reduces to 10 seconds once model detected
- Lower values = faster model detection
- Higher values = less polling overhead

**Recommended Values**:
- Fast detection: `1-2`
- Balanced: `2-5`
- Low overhead: `5-10`

## Complete Configuration Example

### Production Configuration

```bash
# vLLM Backend Configuration
VLLM_BASE_URL=http://localhost:8078/v1
VLLM_TIMEOUT=600

# MCP RAG Server Configuration
REST_API_URL=http://localhost:8080/api/v1
REST_API_KEY=your_production_api_key_here_32plus_chars
MCP_TIMEOUT=90

# External APIs
SERPER_API_KEY=your_serper_production_key
SERPER_TIMEOUT=30

# Research Queue Limits
MAX_STANDARD_RESEARCH=5
MAX_DEEP_RESEARCH=2

# Server Configuration
HOST=0.0.0.0
PORT=8079
LOG_LEVEL=INFO

# Feature Flags
AUTO_DETECT_MODEL=true
MODEL_POLL_INTERVAL=2
```

### Development Configuration

```bash
# vLLM Backend Configuration
VLLM_BASE_URL=http://localhost:8078/v1
VLLM_TIMEOUT=300

# MCP RAG Server Configuration
REST_API_URL=http://localhost:8080/api/v1
REST_API_KEY=dev_api_key_for_testing_only
MCP_TIMEOUT=60

# External APIs
SERPER_API_KEY=your_serper_dev_key
SERPER_TIMEOUT=30

# Research Queue Limits (lower for dev)
MAX_STANDARD_RESEARCH=2
MAX_DEEP_RESEARCH=1

# Server Configuration
HOST=127.0.0.1
PORT=8079
LOG_LEVEL=DEBUG

# Feature Flags
AUTO_DETECT_MODEL=true
MODEL_POLL_INTERVAL=2
```

### High-Performance Configuration

```bash
# vLLM Backend Configuration
VLLM_BASE_URL=http://localhost:8078/v1
VLLM_TIMEOUT=900

# MCP RAG Server Configuration
REST_API_URL=http://localhost:8080/api/v1
REST_API_KEY=your_high_performance_key
MCP_TIMEOUT=120

# External APIs
SERPER_API_KEY=your_serper_premium_key
SERPER_TIMEOUT=30

# Research Queue Limits (higher for capacity)
MAX_STANDARD_RESEARCH=10
MAX_DEEP_RESEARCH=3

# Server Configuration
HOST=0.0.0.0
PORT=8079
LOG_LEVEL=INFO

# Feature Flags
AUTO_DETECT_MODEL=true
MODEL_POLL_INTERVAL=2
```

## Configuration Validation

The configuration system validates critical settings on startup.

### Required Variables

**Will fail if missing**:
- `REST_API_KEY` - MCP server authentication
- `SERPER_API_KEY` - Web search capability

**Error Example**:
```
ERROR: Missing required configuration:
  - REST_API_KEY is not set
  - SERPER_API_KEY is not set

Please set these in your .env file.
```

### Optional Variables

All other variables have defaults and will use them if not specified.

### Validation at Startup

```python
# config.py performs validation
config = Config()
config.validate()  # Raises error if required vars missing
config.display()   # Shows configuration (secrets masked)
```

## Logging Configuration

robaiproxy uses dual logging: console and file.

### Console Logging

**Level**: `LOG_LEVEL` or INFO

**Format**: `%(levelname)-8s | %(message)s`

**Output**: stdout

**Example**:
```
INFO     | Starting robaiproxy on 0.0.0.0:8079
INFO     | Model detected: Qwen3-30B
DEBUG    | Research mode detected for request abc123
```

### File Logging

**Level**: DEBUG (always)

**Format**: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`

**File**: `proxy.log` in robaiproxy directory

**Rotation**: Manual (no auto-rotation)

**Example**:
```
2024-01-15 10:30:00,123 - requestProxy - INFO - Starting server
2024-01-15 10:30:01,456 - researchAgent - DEBUG - Searching knowledge base
```

### Log Viewing

```bash
# View recent logs
tail -f proxy.log

# Search logs
grep "ERROR" proxy.log

# View last 100 lines
tail -n 100 proxy.log
```

## Security Considerations

### API Key Security

**Storage**:
```bash
# Never commit .env to version control
# .gitignore already excludes it

# Use secure key generation
openssl rand -hex 32
```

**Logging**:
```bash
# API keys are masked in logs
# Shows only last 8 characters
REST_API_KEY: ********...abc12345
SERPER_API_KEY: ********...xyz67890
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
- Use `HOST=127.0.0.1` for local-only access
- Use firewall rules for remote access
- Consider reverse proxy with TLS for production
- Implement authentication if exposed to internet

### Service Security

**Best Practices**:
- Rotate API keys regularly
- Use different keys for dev/staging/production
- Monitor `proxy.log` for suspicious activity
- Limit concurrent requests appropriately
- Keep dependencies updated

## Configuration Management

### Environment-Specific Configs

```bash
# Create environment-specific configs
.env.development
.env.staging
.env.production

# Use appropriate config
cp .env.production .env
```

### Configuration Versioning

```bash
# Version .env.example with documentation
# Never version actual .env files

# In .gitignore
.env
.env.*
!.env.example
```

### Configuration Validation Script

```bash
# Check configuration without starting server
python -c "from config import Config; c = Config(); c.validate(); c.display()"
```

Expected output:
```
Configuration:
  VLLM_BASE_URL: http://localhost:8078/v1
  VLLM_TIMEOUT: 300
  REST_API_URL: http://localhost:8080/api/v1
  REST_API_KEY: ********...abc12345
  SERPER_API_KEY: ********...xyz67890
  MAX_STANDARD_RESEARCH: 3
  MAX_DEEP_RESEARCH: 1
  HOST: 0.0.0.0
  PORT: 8079
  LOG_LEVEL: INFO
```

## Troubleshooting Configuration

### Missing Required Keys

**Problem**: Startup fails with missing configuration error

**Solution**:
```bash
# Check .env exists
ls -la .env

# Verify required keys present
grep "REST_API_KEY" .env
grep "SERPER_API_KEY" .env

# Add missing keys
nano .env
```

### Connection Failures

**Problem**: Cannot connect to vLLM or MCP server

**Solution**:
```bash
# Verify URLs are correct
curl http://localhost:8078/v1/models
curl -H "Authorization: Bearer your_key" \
  http://localhost:8080/api/v1/health

# Update URLs in .env if needed
VLLM_BASE_URL=http://correct_host:8078/v1
REST_API_URL=http://correct_host:8080/api/v1
```

### Timeout Issues

**Problem**: Frequent request timeouts

**Solution**:
```bash
# Increase timeout values
VLLM_TIMEOUT=900        # 15 minutes
MCP_TIMEOUT=120         # 2 minutes
SERPER_TIMEOUT=60       # 1 minute
```

### Queue Overload

**Problem**: Too many "queue full" messages

**Solution**:
```bash
# Increase queue limits
MAX_STANDARD_RESEARCH=5
MAX_DEEP_RESEARCH=2

# Or reduce concurrent usage
# Monitor: python check_connections.py
```

### Log File Growing

**Problem**: `proxy.log` becoming very large

**Solution**:
```bash
# Rotate logs manually
mv proxy.log proxy.log.old
gzip proxy.log.old

# Or implement logrotate
# Create /etc/logrotate.d/robaiproxy
/path/to/robaiproxy/proxy.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
```

## Advanced Configuration

### Custom Service URLs

For distributed deployments:

```bash
# Remote vLLM
VLLM_BASE_URL=http://gpu-server-1.local:8078/v1

# Remote MCP server
REST_API_URL=http://rag-server-1.local:8080/api/v1

# Remote knowledge graph
# (Configured in MCP server, not proxy)
```

### Load Balancing

For multiple backend instances:

```bash
# Use load balancer URL
VLLM_BASE_URL=http://vllm-loadbalancer:8078/v1

# Increase queue limits for higher capacity
MAX_STANDARD_RESEARCH=10
MAX_DEEP_RESEARCH=5
```

### Performance Tuning

For optimal performance:

```bash
# Reduce polling overhead
MODEL_POLL_INTERVAL=5

# Optimize timeouts for your network
VLLM_TIMEOUT=600
MCP_TIMEOUT=90
SERPER_TIMEOUT=30

# Balance queue depth with capacity
MAX_STANDARD_RESEARCH=3  # Adjust based on GPU capacity
MAX_DEEP_RESEARCH=1      # Keep low for stability
```

## Next Steps

- [API Reference](api-reference.html) - Complete API documentation
- [Architecture](architecture.html) - System design and patterns
- [Getting Started](getting-started.html) - Installation and usage
