---
layout: default
title: Configuration
parent: robaitragmcp
nav_order: 3
---

# Configuration

Environment configuration for robaitragmcp MCP server.

## Environment Variables

### Server Configuration

**MCP_TCP_PORT**
- Type: Integer
- Default: `3000`
- Description: TCP port for MCP server
- Example: `MCP_TCP_PORT=3000`

**DISCOVERY_INTERVAL**
- Type: Integer (seconds)
- Default: `30`
- Description: Health check interval for container monitoring
- Example: `DISCOVERY_INTERVAL=60`

**MCP_TOOL_TIMEOUT**
- Type: Integer (seconds)
- Default: `60`
- Description: Timeout for tool execution
- Example: `MCP_TOOL_TIMEOUT=120`

### Dependency Configuration

**CRAWL4AI_URL**
- Type: String
- Default: `http://localhost:11235`
- Description: Crawl4AI service URL (passed to discovered tools)
- Example: `CRAWL4AI_URL=http://192.168.10.50:11235`

**USE_MEMORY_DB**
- Type: Boolean
- Default: `true`
- Description: RAM mode for SQLite (via robaimodeltools)
- Example: `USE_MEMORY_DB=false`

### Logging Configuration

**LOG_LEVEL**
- Type: String
- Default: `INFO`
- Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`
- Description: Logging verbosity
- Example: `LOG_LEVEL=DEBUG`

**Log Locations:**
- Main log: `/tmp/robaimcp.log`
- Also logs to stderr (Docker logs)
- MCP action logging included

## Configuration Profiles

### Development Profile

```bash
# Server
MCP_TCP_PORT=3000
LOG_LEVEL=DEBUG

# Discovery
DISCOVERY_INTERVAL=60  # Check less frequently
MCP_TOOL_TIMEOUT=120   # Allow more time for debugging

# Dependencies
CRAWL4AI_URL=http://localhost:11235
USE_MEMORY_DB=false    # Disk mode for easier debugging
```

### Production Profile

```bash
# Server
MCP_TCP_PORT=3000
LOG_LEVEL=INFO

# Discovery
DISCOVERY_INTERVAL=30  # Normal frequency
MCP_TOOL_TIMEOUT=60    # Standard timeout

# Dependencies
CRAWL4AI_URL=http://localhost:11235
USE_MEMORY_DB=true     # RAM mode for performance
```

### Testing Profile

```bash
# Server
MCP_TCP_PORT=3001      # Different port for testing
LOG_LEVEL=DEBUG

# Discovery
DISCOVERY_INTERVAL=10  # Faster checks for testing
MCP_TOOL_TIMEOUT=30    # Shorter timeout for quick feedback

# Dependencies
CRAWL4AI_URL=http://localhost:11235
USE_MEMORY_DB=true
```

## Docker Compose Configuration

**Container Settings:**
```yaml
robaitragmcp:
  container_name: robaitragmcp
  network_mode: host
  ports:
    - "3000:3000"
  volumes:
    - ../robaivenv:/robaivenv
    - ../robaimodeltools:/robaimodeltools
  environment:
    - MCP_TCP_PORT=3000
    - DISCOVERY_INTERVAL=30
    - MCP_TOOL_TIMEOUT=60
```

## Health Monitoring Configuration

**Monitored Containers:**
- robaicrawler (Crawl4AI service)
- robaineo4j (Neo4j database)
- robaikg (KG extraction service)
- robairagapi (REST API wrapper)

**Health Check Behavior:**
- Interval: DISCOVERY_INTERVAL (default 30s)
- Detects container restarts via Docker API
- Triggers tool refresh on restart
- Graceful degradation if Docker unavailable

**To Disable Monitoring:**
- Health monitor auto-disables if Docker unavailable
- No configuration needed - handles gracefully

## Performance Tuning

### Optimize for Speed

```bash
MCP_TOOL_TIMEOUT=30        # Faster timeout
DISCOVERY_INTERVAL=60      # Less frequent checks
USE_MEMORY_DB=true         # RAM mode
```

### Optimize for Large Operations

```bash
MCP_TOOL_TIMEOUT=180       # 3-minute timeout for deep crawling
DISCOVERY_INTERVAL=30      # Normal monitoring
USE_MEMORY_DB=true         # RAM mode
```

### Optimize for Debugging

```bash
LOG_LEVEL=DEBUG            # Verbose logging
MCP_TOOL_TIMEOUT=300       # Long timeout to prevent interruption
DISCOVERY_INTERVAL=60      # Less noise in logs
```

## Troubleshooting Configuration

### Issue: Tools timeout frequently

**Solution:**
```bash
MCP_TOOL_TIMEOUT=120
```

### Issue: Health monitor too noisy

**Solution:**
```bash
DISCOVERY_INTERVAL=60
LOG_LEVEL=WARNING
```

### Issue: Memory usage too high

**Solution:**
```bash
USE_MEMORY_DB=false
```

## Next Steps

- **Architecture:** See [Architecture](architecture.md)
- **API Reference:** Review [API Reference](api-reference.md)
