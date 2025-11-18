---
layout: default
title: Configuration
parent: robairagapi
nav_order: 4
---

# Configuration

Complete configuration reference for robairagapi with all environment variables and settings.

## Environment Variables

robairagapi is configured via environment variables loaded from `.env` file in the repo root.

### Authentication (Required)

At least ONE API key must be configured.

#### OPENAI_API_KEY
- **Required**: Yes (or OPENAI_API_KEY_2)
- **Default**: None
- **Description**: Primary API key for Bearer token authentication
- **Example**: `OPENAI_API_KEY=sk-your-key-here`
- **Security**: Use actual OpenAI API key or generate strong random key
- **Format**: String, any length
- **Used for**: Authentication on all endpoints except `/health`

#### OPENAI_API_KEY_2
- **Required**: No
- **Default**: None
- **Description**: Secondary API key for key rotation without downtime
- **Example**: `OPENAI_API_KEY_2=sk-secondary-key-here`
- **Use Case**:
  - Zero-downtime key rotation
  - Multiple client support
  - Rate limit multiplication (each key gets independent limit)

**Key rotation workflow**:
```bash
# Step 1: Add new key
OPENAI_API_KEY=old-key
OPENAI_API_KEY_2=new-key
# Deploy - both keys work

# Step 2: Clients switch to new key
# (gradual migration)

# Step 3: Remove old key
OPENAI_API_KEY=new-key
OPENAI_API_KEY_2=
# Deploy - only new key works
```

### Server Configuration

#### SERVER_HOST
- **Default**: `0.0.0.0`
- **Description**: Network interface to bind HTTP server
- **Options**:
  - `0.0.0.0` - All interfaces (default, production)
  - `127.0.0.1` - Localhost only (development, behind proxy)
  - Specific IP - Bind to one interface
- **Example**: `SERVER_HOST=0.0.0.0`
- **Security**: Use `127.0.0.1` if behind reverse proxy

#### SERVER_PORT
- **Default**: `8081`
- **Description**: Port number for HTTP server
- **Range**: 1-65535 (avoid 1-1023 without root)
- **Example**: `SERVER_PORT=8081`
- **Note**: Must match docker-compose.yml if using Docker

#### LOG_LEVEL
- **Default**: `INFO`
- **Description**: Logging verbosity
- **Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **Example**: `LOG_LEVEL=INFO`
- **Recommendations**:
  - Development: `DEBUG`
  - Production: `INFO`
  - High traffic: `WARNING`

### Rate Limiting

#### RATE_LIMIT_PER_MINUTE
- **Default**: `60`
- **Description**: Maximum requests per minute per API key
- **Range**: 1-10000
- **Example**: `RATE_LIMIT_PER_MINUTE=60`
- **Algorithm**: Sliding 60-second window
- **Per-key**: Each API key gets independent limit

**Calculation**:
```
Total capacity = RATE_LIMIT_PER_MINUTE × number_of_api_keys

Example:
- 2 API keys
- RATE_LIMIT_PER_MINUTE=60
- Total: 120 req/min
```

#### ENABLE_RATE_LIMIT
- **Default**: `true`
- **Description**: Enable/disable rate limiting globally
- **Options**: `true`, `false`
- **Example**: `ENABLE_RATE_LIMIT=true`
- **Use cases for `false`**:
  - Bulk operations
  - Trusted internal network
  - External rate limiter (nginx, etc.)
- **Security**: Keep `true` for internet-facing deployments

### CORS (Cross-Origin Resource Sharing)

#### ENABLE_CORS
- **Default**: `true`
- **Description**: Enable CORS middleware
- **Example**: `ENABLE_CORS=true`
- **Impact**: Adds CORS headers to responses

#### CORS_ORIGINS
- **Default**: `*`
- **Description**: Allowed CORS origins (comma-separated)
- **Examples**:
  - `CORS_ORIGINS=*` - All origins (development)
  - `CORS_ORIGINS=https://example.com` - Single origin
  - `CORS_ORIGINS=https://app1.com,https://app2.com` - Multiple origins
- **Security**: Always restrict in production

**Production example**:
```bash
ENABLE_CORS=true
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

### Backend Services

#### CRAWL4AI_URL
- **Default**: `http://localhost:11235`
- **Description**: URL of Crawl4AI service for web crawling
- **Example**: `CRAWL4AI_URL=http://localhost:11235`
- **Required for**: All crawl operations
- **Health check**: `curl $CRAWL4AI_URL/health`

#### KG_SERVICE_URL
- **Default**: `http://localhost:8088`
- **Description**: URL of knowledge graph service
- **Example**: `KG_SERVICE_URL=http://localhost:8088`
- **Required for**: `/api/v1/search/kg` and `/api/v1/search/enhanced` endpoints
- **Optional**: Simple search works without KG service

### Database Configuration

#### USE_MEMORY_DB
- **Default**: `true`
- **Description**: Use in-memory SQLite with differential sync to disk
- **Options**: `true`, `false`
- **Example**: `USE_MEMORY_DB=true`
- **Impact**:
  - `true`: ~10x faster, RAM usage higher, differential sync
  - `false`: Slower, lower RAM, direct disk writes

**Performance comparison**:
```
USE_MEMORY_DB=true:  50-100ms search
USE_MEMORY_DB=false: 100-300ms search

RAM usage:
true:  Database size + overhead (e.g., 250MB DB = 350MB RAM)
false: Minimal (SQLite cache only)
```

#### DB_PATH
- **Default**: `/data/crawl4ai_rag.db`
- **Description**: Path to SQLite database file
- **Example**: `DB_PATH=/data/crawl4ai_rag.db`
- **Note**: Usually set via robaimodeltools, not here

### Security - Advanced

#### ENABLE_MAC_VALIDATION
- **Default**: `false`
- **Description**: Enable MAC address validation for client requests
- **Example**: `ENABLE_MAC_VALIDATION=false`
- **Use case**: Prevent IP spoofing attacks
- **Requirements**: Linux, root privileges for ARP table access
- **Recommendation**: Enable in high-security environments

#### STRICT_AUTH_FOR_PFSENSE
- **Default**: `false`
- **Description**: Enable strict security mode for pfSense proxy requests
- **Example**: `STRICT_AUTH_FOR_PFSENSE=false`
- **Impact**: Enables additional security checks (path traversal, method override, etc.)
- **Use case**: When behind pfSense proxy/firewall

#### PFSENSE_IP
- **Default**: `192.168.10.1`
- **Description**: IP address of pfSense proxy/firewall
- **Example**: `PFSENSE_IP=192.168.10.1`
- **Used for**: Identifying pfSense requests to apply strict mode

#### PFSENSE_MAC
- **Default**: `00:00:00:00:00:00`
- **Description**: MAC address of pfSense proxy/firewall
- **Example**: `PFSENSE_MAC=aa:bb:cc:dd:ee:ff`
- **Used for**: Validating pfSense identity (prevents spoofing)
- **Format**: Colon-separated hex (xx:xx:xx:xx:xx:xx)

#### TRUSTED_LAN_SUBNET
- **Default**: `192.168.10.0/24`
- **Description**: Trusted LAN subnet for relaxed security mode
- **Example**: `TRUSTED_LAN_SUBNET=192.168.10.0/24`
- **Format**: CIDR notation (IP/mask)
- **Impact**: Requests from this subnet get relaxed security checks

**Security modes**:

**STRICT MODE** (pfSense requests):
- Triggered when: IP = PFSENSE_IP and MAC = PFSENSE_MAC
- Checks: Path traversal, method override, protocol downgrade, suspicious headers
- Returns: 404 on any security violation

**RELAXED MODE** (LAN requests):
- Triggered when: IP in TRUSTED_LAN_SUBNET
- Checks: Basic security only
- More permissive for internal tools

**Example configuration**:
```bash
# Enable advanced security
ENABLE_MAC_VALIDATION=true
STRICT_AUTH_FOR_PFSENSE=true
PFSENSE_IP=192.168.10.1
PFSENSE_MAC=52:54:00:12:34:56
TRUSTED_LAN_SUBNET=192.168.10.0/24
```

### Domain Management

#### BLOCKED_DOMAIN_KEYWORD
- **Default**: None
- **Description**: Authorization keyword for removing blocked domains
- **Example**: `BLOCKED_DOMAIN_KEYWORD=remove-auth-keyword`
- **Required for**: `DELETE /api/v1/blocked-domains`
- **Security**: Use strong, secret value

## Configuration Profiles

### Development Profile

**Purpose**: Local development with debugging.

**.env file**:
```bash
# Authentication
OPENAI_API_KEY=dev-key-for-testing-only

# Server
SERVER_HOST=127.0.0.1
SERVER_PORT=8081
LOG_LEVEL=DEBUG

# Rate Limiting (high limit for testing)
RATE_LIMIT_PER_MINUTE=120
ENABLE_RATE_LIMIT=true

# CORS (allow local frontend)
ENABLE_CORS=true
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Backend Services
CRAWL4AI_URL=http://localhost:11235
KG_SERVICE_URL=http://localhost:8088

# Database (fast mode)
USE_MEMORY_DB=true

# Security (disabled for dev)
ENABLE_MAC_VALIDATION=false
STRICT_AUTH_FOR_PFSENSE=false
```

### Production Profile

**Purpose**: Internet-facing deployment.

**.env file**:
```bash
# Authentication (use real keys)
OPENAI_API_KEY=sk-prod-key-1-with-real-openai-format
OPENAI_API_KEY_2=sk-prod-key-2-for-rotation

# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8081
LOG_LEVEL=INFO

# Rate Limiting (protect backend)
RATE_LIMIT_PER_MINUTE=60
ENABLE_RATE_LIMIT=true

# CORS (restrict to your domains)
ENABLE_CORS=true
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Backend Services
CRAWL4AI_URL=http://localhost:11235
KG_SERVICE_URL=http://localhost:8088

# Database (performance mode)
USE_MEMORY_DB=true

# Security (disabled unless behind pfSense)
ENABLE_MAC_VALIDATION=false
STRICT_AUTH_FOR_PFSENSE=false
```

### Docker Profile

**Purpose**: Docker Compose deployment.

**.env file** (repo root):
```bash
# Authentication
OPENAI_API_KEY=your-api-key-here

# Server (Docker handles networking)
SERVER_PORT=8081
LOG_LEVEL=INFO

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60

# CORS
ENABLE_CORS=true
CORS_ORIGINS=*

# Backend Services (Docker service names)
CRAWL4AI_URL=http://localhost:11235
KG_SERVICE_URL=http://localhost:8088

# Database
USE_MEMORY_DB=true
```

**docker-compose.yml snippet**:
```yaml
services:
  robairagapi:
    image: robairagapi:latest
    network_mode: "host"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - SERVER_PORT=${SERVER_PORT:-8081}
      - RATE_LIMIT_PER_MINUTE=${RATE_LIMIT_PER_MINUTE:-60}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    volumes:
      - ./robaimodeltools:/robaimodeltools
      - ./robaidata:/data
```

### High-Security Profile

**Purpose**: Behind pfSense with MAC validation.

**.env file**:
```bash
# Authentication
OPENAI_API_KEY=secure-key-1
OPENAI_API_KEY_2=secure-key-2

# Server (localhost only, behind pfSense)
SERVER_HOST=127.0.0.1
SERVER_PORT=8081
LOG_LEVEL=WARNING

# Rate Limiting (strict)
RATE_LIMIT_PER_MINUTE=30
ENABLE_RATE_LIMIT=true

# CORS (restrictive)
ENABLE_CORS=true
CORS_ORIGINS=https://secure.yourdomain.com

# Backend Services
CRAWL4AI_URL=http://localhost:11235
KG_SERVICE_URL=http://localhost:8088

# Database
USE_MEMORY_DB=true

# Security (ENABLED)
ENABLE_MAC_VALIDATION=true
STRICT_AUTH_FOR_PFSENSE=true
PFSENSE_IP=192.168.10.1
PFSENSE_MAC=52:54:00:12:34:56
TRUSTED_LAN_SUBNET=192.168.10.0/24
```

## Configuration Validation

### Startup Validation

robairagapi validates configuration on startup and fails fast on errors.

**Required validation**:
```python
# At least one API key
if not OPENAI_API_KEY and not OPENAI_API_KEY_2:
    raise ValueError("At least one API key required")
```

**Optional validation** (uses defaults):
```python
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8081"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
```

**Type validation**:
- SERVER_PORT: Must be integer 1-65535
- RATE_LIMIT_PER_MINUTE: Must be integer > 0
- ENABLE_RATE_LIMIT: Must be "true" or "false"
- ENABLE_CORS: Must be "true" or "false"

### Runtime Validation

**Health checks**:
```bash
# Validate service is running
curl http://localhost:8081/health
# Returns: {"status": "healthy", ...}

# Validate authentication works
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  http://localhost:8081/api/v1/status
# Returns: {"api_status": "running", ...}
```

**Configuration checks**:
```bash
# Check rate limiter is active
for i in {1..65}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -H "Authorization: Bearer $OPENAI_API_KEY" \
    http://localhost:8081/api/v1/status
done
# First 60: 200
# After 60: 404 (rate limited)

# Check CORS headers
curl -v http://localhost:8081/health
# Should see: Access-Control-Allow-Origin header
```

## Security Best Practices

### API Key Security

**Generate strong keys**:
```bash
# Use OpenAI API key format
OPENAI_API_KEY=sk-your-actual-openai-key

# Or generate random key
python3 -c "import secrets; print('sk-' + secrets.token_urlsafe(32))"
# Output: sk-randomstring...
```

**Protect .env file**:
```bash
# Restrict permissions
chmod 600 .env

# Never commit to git
echo ".env" >> .gitignore

# Use environment variables in CI/CD
export OPENAI_API_KEY="$SECRET_KEY"
```

**Key rotation strategy**:
1. Add OPENAI_API_KEY_2 with new key
2. Deploy - both keys work
3. Update clients to use new key
4. After migration: Remove old key, promote new key to OPENAI_API_KEY

### Network Security

**Production checklist**:
- [ ] SERVER_HOST=0.0.0.0 (or 127.0.0.1 if behind proxy)
- [ ] Use reverse proxy with TLS (nginx, Caddy)
- [ ] Firewall rules restrict port 8081 access
- [ ] CORS_ORIGINS restricted to your domains
- [ ] Rate limiting enabled
- [ ] Strong API keys

**Example nginx config**:
```nginx
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Authorization $http_authorization;
    }
}
```

### CORS Security

**Development** (permissive):
```bash
CORS_ORIGINS=*
```

**Production** (restrictive):
```bash
# Single origin
CORS_ORIGINS=https://yourdomain.com

# Multiple origins
CORS_ORIGINS=https://app.yourdomain.com,https://admin.yourdomain.com

# Subdomain wildcard (not supported, list explicitly)
```

## Performance Tuning

### Rate Limit Tuning

**Determine capacity**:
```
Backend capacity: 100 req/s (hypothetical)
Safety margin: 50%
Target throughput: 50 req/s = 3000 req/min

Per-key calculation:
- 1 key: RATE_LIMIT_PER_MINUTE=3000
- 2 keys: RATE_LIMIT_PER_MINUTE=1500
- 5 keys: RATE_LIMIT_PER_MINUTE=600
```

**Recommendations by load**:

| Traffic Level | Keys | RATE_LIMIT_PER_MINUTE | Total Capacity |
|---------------|------|----------------------|----------------|
| Low | 1 | 30 | 30 req/min |
| Medium | 1 | 60 | 60 req/min |
| High | 2 | 120 | 240 req/min |
| Very High | 5 | 120 | 600 req/min |

### Database Tuning

**RAM mode (default)**:
```bash
USE_MEMORY_DB=true
```
- Pros: ~10x faster queries
- Cons: Higher RAM usage
- Best for: Production, frequent searches

**Disk mode**:
```bash
USE_MEMORY_DB=false
```
- Pros: Lower RAM usage
- Cons: Slower queries
- Best for: Resource-constrained, infrequent searches

### Logging Tuning

**Reduce log volume in production**:
```bash
LOG_LEVEL=WARNING
```

**Debug performance issues**:
```bash
LOG_LEVEL=DEBUG
# Adds X-Process-Time to logs
# Shows all API calls with timing
```

### Worker Tuning

**Single worker** (default):
```bash
python main.py
```
- Throughput: Limited by single process
- Best for: Development, low traffic

**Multiple workers** (production):
```bash
gunicorn api.server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8081 \
  --timeout 120
```
- Throughput: ~4x single worker
- Workers: `nproc` or `2 * num_cores + 1`
- Note: Rate limiter is per-process (not shared)

## Troubleshooting

### Common Configuration Errors

#### Error: No API keys configured

**Error message**:
```
ERROR - Server configuration error: No API keys configured
```

**Cause**: Neither OPENAI_API_KEY nor OPENAI_API_KEY_2 is set.

**Solution**:
```bash
# Add to .env
OPENAI_API_KEY=your-key-here

# Or export
export OPENAI_API_KEY=your-key-here
```

#### Error: Port already in use

**Error message**:
```
OSError: [Errno 98] Address already in use
```

**Cause**: Port 8081 is already bound.

**Solution**:
```bash
# Change port
SERVER_PORT=8082

# Or kill existing process
lsof -ti:8081 | xargs kill -9

# Or use different service
docker compose stop robairagapi
```

#### Error: Authentication fails (404)

**Symptoms**: All authenticated requests return 404.

**Cause**: API key mismatch, whitespace, or typo.

**Solution**:
```bash
# Verify key in .env
cat .env | grep OPENAI_API_KEY

# Test with exact key
curl -H "Authorization: Bearer $(grep OPENAI_API_KEY .env | cut -d '=' -f2)" \
  http://localhost:8081/api/v1/status

# Check logs for SECURITY warnings
docker compose logs robairagapi | grep SECURITY
```

#### Error: CORS blocked

**Browser error**: "CORS policy: No 'Access-Control-Allow-Origin' header"

**Cause**: CORS_ORIGINS doesn't include frontend URL.

**Solution**:
```bash
# Add frontend origin
CORS_ORIGINS=http://localhost:3000

# Or allow all (dev only)
CORS_ORIGINS=*

# Restart service
docker compose restart robairagapi
```

#### Error: Rate limit unexpectedly low

**Symptoms**: Getting 404 after fewer than expected requests.

**Cause**: Multiple API keys sharing the same value, or rate limit too low.

**Solution**:
```bash
# Increase limit
RATE_LIMIT_PER_MINUTE=120

# Or disable temporarily
ENABLE_RATE_LIMIT=false

# Or use different API keys
OPENAI_API_KEY=key1
OPENAI_API_KEY_2=key2  # Different value!
```

#### Error: Crawl4AI connection failed

**Error message**: "Failed to connect to Crawl4AI service"

**Cause**: CRAWL4AI_URL incorrect or service not running.

**Solution**:
```bash
# Verify URL
echo $CRAWL4AI_URL

# Test connection
curl http://localhost:11235/health

# Start service if needed
docker compose up -d crawl4ai

# Update URL if needed
CRAWL4AI_URL=http://localhost:11235
```

## Configuration Hierarchy

**Priority** (highest to lowest):

1. **Environment variables** (shell exports)
2. **.env file** (in repo root)
3. **Default values** (in code)

**Example**:
```bash
# .env file
SERVER_PORT=8081

# Override with environment variable
export SERVER_PORT=9000

# Result: Server starts on port 9000 (env var wins)
```

**Docker override**:
```yaml
# docker-compose.yml
environment:
  - SERVER_PORT=8082
# This overrides .env file value
```

## Complete Configuration Reference

| Variable | Type | Required | Default | Range/Options |
|----------|------|----------|---------|---------------|
| OPENAI_API_KEY | str | Yes* | None | Any string |
| OPENAI_API_KEY_2 | str | No | None | Any string |
| SERVER_HOST | str | No | 0.0.0.0 | Valid IP/hostname |
| SERVER_PORT | int | No | 8081 | 1-65535 |
| LOG_LEVEL | str | No | INFO | DEBUG/INFO/WARNING/ERROR/CRITICAL |
| RATE_LIMIT_PER_MINUTE | int | No | 60 | 1-10000 |
| ENABLE_RATE_LIMIT | bool | No | true | true/false |
| ENABLE_CORS | bool | No | true | true/false |
| CORS_ORIGINS | str | No | * | Comma-separated URLs or * |
| CRAWL4AI_URL | str | No | http://localhost:11235 | Valid HTTP URL |
| KG_SERVICE_URL | str | No | http://localhost:8088 | Valid HTTP URL |
| USE_MEMORY_DB | bool | No | true | true/false |
| ENABLE_MAC_VALIDATION | bool | No | false | true/false |
| STRICT_AUTH_FOR_PFSENSE | bool | No | false | true/false |
| PFSENSE_IP | str | No | 192.168.10.1 | Valid IP address |
| PFSENSE_MAC | str | No | 00:00:00:00:00:00 | MAC address (xx:xx:xx:xx:xx:xx) |
| TRUSTED_LAN_SUBNET | str | No | 192.168.10.0/24 | CIDR notation |
| BLOCKED_DOMAIN_KEYWORD | str | No | None | Any string |

*At least one of OPENAI_API_KEY or OPENAI_API_KEY_2 required

## Next Steps

- [Getting Started](getting-started.md) - Installation and usage guide
- [Architecture](architecture.md) - System design and internals
- [API Reference](api-reference.md) - Complete endpoint documentation
