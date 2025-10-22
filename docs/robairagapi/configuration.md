---
layout: default
title: Configuration
parent: robairagapi
nav_order: 2
---

# Configuration

Complete configuration reference for robairagapi.

## Environment Variables

### Authentication (Required)

At least ONE API key must be configured.

#### LOCAL_API_KEY
- **Required**: Yes (or REMOTE_API_KEY_2)
- **Default**: None
- **Description**: Primary API key for Bearer token authentication
- **Example**: `LOCAL_API_KEY=your-secret-key-here-minimum-32-chars`
- **Security**: Use strong random key (e.g., `openssl rand -hex 32`)

#### REMOTE_API_KEY_2
- **Required**: No
- **Default**: None
- **Description**: Secondary API key for rotation/redundancy
- **Example**: `REMOTE_API_KEY_2=another-secret-key`
- **Use Case**: Zero-downtime key rotation

### Server Configuration

#### SERVER_HOST
- **Default**: `0.0.0.0`
- **Description**: Network interface to bind
- **Options**:
  - `0.0.0.0` - All interfaces (default)
  - `127.0.0.1` - Localhost only
- **Example**: `SERVER_HOST=0.0.0.0`

#### SERVER_PORT
- **Default**: `8080`
- **Description**: Port number for HTTP server
- **Example**: `SERVER_PORT=8080`

#### LOG_LEVEL
- **Default**: `INFO`
- **Description**: Logging verbosity
- **Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **Example**: `LOG_LEVEL=INFO`

### Rate Limiting

#### RATE_LIMIT_PER_MINUTE
- **Default**: `60`
- **Description**: Maximum requests per minute per API key
- **Range**: 1-10000
- **Example**: `RATE_LIMIT_PER_MINUTE=60`

#### ENABLE_RATE_LIMIT
- **Default**: `true`
- **Description**: Enable/disable rate limiting
- **Options**: `true`, `false`
- **Example**: `ENABLE_RATE_LIMIT=true`

### CORS

#### ENABLE_CORS
- **Default**: `true`
- **Description**: Enable Cross-Origin Resource Sharing
- **Example**: `ENABLE_CORS=true`

#### CORS_ORIGINS
- **Default**: `*`
- **Description**: Allowed CORS origins (comma-separated)
- **Examples**:
  - `CORS_ORIGINS=*` - All origins
  - `CORS_ORIGINS=http://localhost:3000,https://example.com`
- **Security**: Restrict in production

### Domain Blocking

#### BLOCKED_DOMAIN_KEYWORD
- **Default**: None
- **Description**: Authorization keyword for removing blocked domains
- **Example**: `BLOCKED_DOMAIN_KEYWORD=remove-auth-keyword`
- **Use**: Required for `DELETE /api/v1/blocked-domains`

## Complete Configuration Example

### Development Configuration

```bash
# Authentication
LOCAL_API_KEY=dev-key-for-testing-only-not-secure

# Server
SERVER_HOST=127.0.0.1
SERVER_PORT=8080
LOG_LEVEL=DEBUG

# Rate Limiting
RATE_LIMIT_PER_MINUTE=120
ENABLE_RATE_LIMIT=true

# CORS
ENABLE_CORS=true
CORS_ORIGINS=http://localhost:3000

# Domain Management
BLOCKED_DOMAIN_KEYWORD=dev-remove
```

### Production Configuration

```bash
# Authentication (use strong keys)
LOCAL_API_KEY=prod_key_1_generated_with_openssl_rand_hex_32
REMOTE_API_KEY_2=prod_key_2_for_rotation

# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8080
LOG_LEVEL=INFO

# Rate Limiting (adjust based on capacity)
RATE_LIMIT_PER_MINUTE=60
ENABLE_RATE_LIMIT=true

# CORS (restrict to your domains)
ENABLE_CORS=true
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Domain Management
BLOCKED_DOMAIN_KEYWORD=secure-prod-remove-keyword
```

### Docker Configuration

```bash
# Minimal for Docker deployment
LOCAL_API_KEY=your-docker-api-key
SERVER_PORT=8080
RATE_LIMIT_PER_MINUTE=60
LOG_LEVEL=INFO
```

## Configuration Validation

The service validates configuration on startup:

```python
# Required validation
if not LOCAL_API_KEY and not REMOTE_API_KEY_2:
    raise ValueError("At least one API key required")

# Optional validation (uses defaults)
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8080"))
```

## Security Best Practices

### API Key Security

**Generation**:
```bash
# Generate strong random keys
openssl rand -hex 32

# Or use Python
python -c "import secrets; print(secrets.token_hex(32))"
```

**Storage**:
- Never commit .env to version control
- Use environment variables in production
- Restrict file permissions: `chmod 600 .env`

**Rotation**:
```bash
# Add new key without downtime
REMOTE_API_KEY_2=new-key-here
# Deploy
# Remove old key
LOCAL_API_KEY=new-key-here
REMOTE_API_KEY_2=
```

### Network Security

**Localhost Only** (development):
```bash
SERVER_HOST=127.0.0.1
```

**Public Access** (production with reverse proxy):
```bash
SERVER_HOST=0.0.0.0
# Use nginx/caddy with TLS in front
```

### CORS Security

**Development** (allow all):
```bash
CORS_ORIGINS=*
```

**Production** (restrict):
```bash
CORS_ORIGINS=https://yourdomain.com
```

## Rate Limiting Configuration

### Determining Limits

**Low Traffic**:
```bash
RATE_LIMIT_PER_MINUTE=30
```

**Medium Traffic**:
```bash
RATE_LIMIT_PER_MINUTE=60  # Default
```

**High Traffic**:
```bash
RATE_LIMIT_PER_MINUTE=120
```

**Disable** (not recommended):
```bash
ENABLE_RATE_LIMIT=false
```

### Per-Client Limits

Rate limits are per API key. Multiple keys = multiplied capacity:

```bash
# 2 keys = 120 req/min total
LOCAL_API_KEY=key1      # 60 req/min
REMOTE_API_KEY_2=key2   # 60 req/min
RATE_LIMIT_PER_MINUTE=60
```

## Logging Configuration

### Log Levels

**DEBUG** (verbose):
```bash
LOG_LEVEL=DEBUG
```
- All API requests
- Parameter validation
- Database queries
- External service calls

**INFO** (normal):
```bash
LOG_LEVEL=INFO
```
- Startup/shutdown
- API requests summary
- Errors

**WARNING** (minimal):
```bash
LOG_LEVEL=WARNING
```
- Only warnings and errors

**ERROR** (critical only):
```bash
LOG_LEVEL=ERROR
```
- Only errors

### Log Format

```
2024-01-15 10:30:45,123 - INFO - Starting server on 0.0.0.0:8080
2024-01-15 10:30:46,456 - INFO - POST /api/v1/crawl/store - 200
2024-01-15 10:30:47,789 - ERROR - Failed to crawl URL: Connection timeout
```

## Troubleshooting Configuration

### Missing API Key Error

**Error**:
```
ValueError: At least one API key (LOCAL_API_KEY or REMOTE_API_KEY_2) must be set
```

**Solution**:
```bash
# Add to .env
LOCAL_API_KEY=your-api-key-here
```

### Port Already in Use

**Error**:
```
OSError: [Errno 98] Address already in use
```

**Solution**:
```bash
# Change port
SERVER_PORT=8081

# Or kill existing process
lsof -ti:8080 | xargs kill -9
```

### Invalid Rate Limit

**Error**:
```
ValueError: RATE_LIMIT_PER_MINUTE must be positive integer
```

**Solution**:
```bash
# Use valid value
RATE_LIMIT_PER_MINUTE=60
```

### CORS Issues

**Problem**: Browser blocks requests

**Solution**:
```bash
# Allow your frontend origin
CORS_ORIGINS=http://localhost:3000

# Or allow all (dev only)
CORS_ORIGINS=*
```

## Advanced Configuration

### Multiple Workers

Not configured via .env, but via startup command:

```bash
# Gunicorn with 4 workers
gunicorn api.server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8080
```

### Behind Reverse Proxy

**nginx example**:
```nginx
server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Configuration**:
```bash
# Bind to localhost
SERVER_HOST=127.0.0.1
SERVER_PORT=8080

# Trust proxy headers
# (handled automatically by FastAPI)
```

### Docker Compose Configuration

```yaml
services:
  robairagapi:
    image: robairagapi:latest
    environment:
      - LOCAL_API_KEY=${LOCAL_API_KEY}
      - SERVER_PORT=8080
      - RATE_LIMIT_PER_MINUTE=60
      - LOG_LEVEL=INFO
      - ENABLE_CORS=true
      - CORS_ORIGINS=https://yourdomain.com
    ports:
      - "8080:8080"
```

## Configuration Hierarchy

Priority (highest to lowest):

1. Environment variables
2. .env file
3. Default values in code

Example:
```bash
# .env file
SERVER_PORT=8080

# Override with environment variable
export SERVER_PORT=9000

# Result: 9000 (env var wins)
```

## Validation Reference

| Variable | Type | Required | Default | Validation |
|----------|------|----------|---------|------------|
| LOCAL_API_KEY | str | Yes* | None | Length > 0 |
| REMOTE_API_KEY_2 | str | No | None | Length > 0 |
| SERVER_HOST | str | No | 0.0.0.0 | Valid IP/hostname |
| SERVER_PORT | int | No | 8080 | 1-65535 |
| LOG_LEVEL | str | No | INFO | Valid log level |
| RATE_LIMIT_PER_MINUTE | int | No | 60 | > 0 |
| ENABLE_RATE_LIMIT | bool | No | true | true/false |
| ENABLE_CORS | bool | No | true | true/false |
| CORS_ORIGINS | str | No | * | Valid URLs or * |
| BLOCKED_DOMAIN_KEYWORD | str | No | None | Any string |

*At least one of LOCAL_API_KEY or REMOTE_API_KEY_2 required

## Next Steps

- [API Reference](api-reference.html) - Complete endpoint documentation
- [Architecture](architecture.html) - System design
- [Getting Started](getting-started.html) - Installation guide
