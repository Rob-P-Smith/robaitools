---
layout: default
title: Configuration
parent: robaiwebui
nav_order: 2
---

# Configuration

Complete configuration reference for robaiwebui including environment variables, Docker settings, and customization options.

## Environment Variables

All configuration is managed through environment variables in `.env` file at repository root.

### Server Configuration

**WEBUI_EXTERNAL_PORT**
- **Purpose:** Host port for accessing Open WebUI
- **Default:** `80`
- **Type:** Integer
- **Example:** `WEBUI_EXTERNAL_PORT=80`
- **Usage:** `http://localhost:80` in browser
- **Notes:** Standard HTTP port, may require sudo/admin on some systems

**WEBUI_INTERNAL_PORT**
- **Purpose:** Container internal port
- **Default:** `8080`
- **Type:** Integer
- **Example:** `WEBUI_INTERNAL_PORT=8080`
- **Usage:** Port uvicorn listens on inside container
- **Notes:** Rarely needs changing, mapped to WEBUI_EXTERNAL_PORT

**WEB_URL**
- **Purpose:** External URL for webhooks and notifications
- **Default:** `http://localhost:80`
- **Type:** URL
- **Example:** `WEB_URL=https://chat.example.com`
- **Usage:** Used in email notifications, OAuth redirects
- **Notes:** Set to public URL if hosting externally

###Backend Integration

**OPENAI_API_BASE_URL**
- **Purpose:** Backend LLM API endpoint
- **Default:** `http://192.168.10.50:8079/v1`
- **Type:** URL
- **Example:** `OPENAI_API_BASE_URL=http://localhost:8079/v1`
- **Usage:** Where Open WebUI sends chat completion requests
- **Notes:** Must point to robaiproxy for research mode and RAG integration
- **Critical:** robaiproxy must be running at this address

**OPENAI_API_KEY**
- **Purpose:** API authentication token
- **Default:** `sk-dummy-key`
- **Type:** String
- **Example:** `OPENAI_API_KEY=sk-abc123xyz789`
- **Usage:** Sent as `Authorization: Bearer {key}` header
- **Notes:** robaiproxy validates this key for access control
- **Multiple Keys:** Supports comma-separated list for rotation

### Metadata and Headers

**ENABLE_FORWARD_USER_INFO_HEADERS**
- **Purpose:** Forward user context to backend
- **Default:** `True` (patched from False)
- **Type:** Boolean
- **Example:** `ENABLE_FORWARD_USER_INFO_HEADERS=True`
- **Usage:** Adds X-OpenWebUI-* headers to backend requests
- **Headers Added:**
  - `X-OpenWebUI-User-Name`
  - `X-OpenWebUI-User-Id`
  - `X-OpenWebUI-User-Email`
  - `X-OpenWebUI-User-Role`
  - `X-OpenWebUI-Chat-Id`
- **Notes:** Enabled by default via Dockerfile patch

### Security and Authentication

**WEBUI_SECRET_KEY**
- **Purpose:** Session cookie encryption key
- **Default:** Auto-generated on first run
- **Type:** String (32+ characters recommended)
- **Example:** `WEBUI_SECRET_KEY=your-secret-key-here-minimum-32-chars`
- **Usage:** Encrypts session data and cookies
- **Notes:** Changing this invalidates all active sessions
- **Storage:** Saved to `/app/backend/data/` on first startup

**ENABLE_SIGNUP**
- **Purpose:** Allow new user registration
- **Default:** `True`
- **Type:** Boolean
- **Example:** `ENABLE_SIGNUP=False`
- **Usage:** Set to False to disable public signup (admin creates users)
- **Notes:** First user is always allowed (becomes admin)

**DEFAULT_USER_ROLE**
- **Purpose:** Role assigned to new users
- **Default:** `user`
- **Type:** String (`admin` or `user`)
- **Example:** `DEFAULT_USER_ROLE=user`
- **Usage:** Controls permissions for new signups
- **Notes:** First user gets admin regardless

**JWT_EXPIRES_IN**
- **Purpose:** Session token lifetime
- **Default:** `86400` (24 hours)
- **Type:** Integer (seconds)
- **Example:** `JWT_EXPIRES_IN=604800` (7 days)
- **Usage:** How long users stay logged in
- **Notes:** Set higher for convenience, lower for security

### Model and Backend Settings

**ENABLE_MODEL_FILTER**
- **Purpose:** Filter available models
- **Default:** `False`
- **Type:** Boolean
- **Example:** `ENABLE_MODEL_FILTER=True`
- **Usage:** Show only specific models to users
- **Notes:** Requires MODEL_FILTER_LIST if enabled

**MODEL_FILTER_LIST**
- **Purpose:** Allowed model names
- **Default:** Empty (all models shown)
- **Type:** Comma-separated list
- **Example:** `MODEL_FILTER_LIST=Qwen3-30B,gpt-4`
- **Usage:** Only listed models appear in dropdown
- **Notes:** Must match exact model names from backend

**ENABLE_RAG_WEB_SEARCH**
- **Purpose:** Enable web search integration
- **Default:** `False`
- **Type:** Boolean
- **Example:** `ENABLE_RAG_WEB_SEARCH=True`
- **Usage:** Allows web search from chat (if backend supports)
- **Notes:** robaiproxy handles web search via Serper API

### File Upload and Storage

**ENABLE_IMAGE_GENERATION**
- **Purpose:** Allow image generation requests
- **Default:** `False`
- **Type:** Boolean
- **Example:** `ENABLE_IMAGE_GENERATION=True`
- **Usage:** Enable image generation features
- **Notes:** Requires backend with image generation support

**ENABLE_RAG_WEB_LOADER_SSL_VERIFICATION**
- **Purpose:** Verify SSL certificates for web content
- **Default:** `True`
- **Type:** Boolean
- **Example:** `ENABLE_RAG_WEB_LOADER_SSL_VERIFICATION=False`
- **Usage:** Set False to allow self-signed certificates
- **Notes:** Insecure, use only for development

**UPLOAD_DIR**
- **Purpose:** Directory for uploaded files
- **Default:** `/app/backend/data/uploads`
- **Type:** Path
- **Example:** `UPLOAD_DIR=/data/uploads`
- **Usage:** Where user-uploaded files are stored
- **Notes:** Must be within Docker volume for persistence

### Logging and Debugging

**LOG_LEVEL**
- **Purpose:** Logging verbosity
- **Default:** `INFO`
- **Type:** String (`DEBUG`, `INFO`, `WARNING`, `ERROR`)
- **Example:** `LOG_LEVEL=DEBUG`
- **Usage:** Controls log detail level
- **Notes:** DEBUG useful for troubleshooting, INFO for production

**ENABLE_WEBSOCKET_LOGGING**
- **Purpose:** Log WebSocket traffic
- **Default:** `False`
- **Type:** Boolean
- **Example:** `ENABLE_WEBSOCKET_LOGGING=True`
- **Usage:** Logs Socket.IO events for debugging
- **Notes:** Very verbose, use only when debugging status events

### Database and Performance

**DATABASE_URL**
- **Purpose:** SQLite database path
- **Default:** `sqlite:////app/backend/data/webui.db`
- **Type:** Database URL
- **Example:** `DATABASE_URL=sqlite:////data/webui.db`
- **Usage:** Where chat history and users are stored
- **Notes:** Must be within Docker volume

**POOL_PRE_PING**
- **Purpose:** Test database connections before use
- **Default:** `True`
- **Type:** Boolean
- **Example:** `POOL_PRE_PING=True`
- **Usage:** Prevents stale connection errors
- **Notes:** Recommended to keep enabled

**POOL_SIZE**
- **Purpose:** Database connection pool size
- **Default:** `10`
- **Type:** Integer
- **Example:** `POOL_SIZE=20`
- **Usage:** Max concurrent database connections
- **Notes:** Increase for high-traffic deployments

## Docker Compose Settings

### Port Mapping

**Standard Configuration:**
```yaml
ports:
  - "80:8080"  # External 80 → Internal 8080
```

**Alternative Ports:**
```yaml
# Run on different port
ports:
  - "3000:8080"  # Access via localhost:3000

# Or use environment variable
ports:
  - "${WEBUI_EXTERNAL_PORT:-80}:${WEBUI_INTERNAL_PORT:-8080}"
```

### Volume Configuration

**Persistent Data Volume:**
```yaml
volumes:
  - open-webui_open-webui:/app/backend/data
```

**What Gets Stored:**
- `webui.db` - SQLite database (chat history, users)
- `uploads/` - User uploaded files
- `cache/` - Embedding cache (if local embedding enabled)
- `WEBUI_SECRET_KEY` - Session encryption key

**Backup Volume:**
```bash
# Create backup
docker run --rm \
  -v open-webui_open-webui:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/open-webui-backup-$(date +%Y%m%d).tar.gz /data

# Restore backup
docker run --rm \
  -v open-webui_open-webui:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/open-webui-backup-20250118.tar.gz -C /
```

### Resource Limits

**Memory Limits:**
```yaml
deploy:
  resources:
    limits:
      memory: 1G
    reservations:
      memory: 512M
```

**CPU Limits:**
```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
    reservations:
      cpus: '1.0'
```

### Health Check

**Default Configuration:**
```yaml
healthcheck:
  test: ["CMD-SHELL", "curl -f http://localhost:8080/ || exit 1"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 30s
```

**Custom Health Check:**
```yaml
healthcheck:
  test: ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"]
  interval: 60s  # Check every minute
  timeout: 5s    # Fail after 5s
  retries: 5     # Try 5 times before marking unhealthy
  start_period: 60s  # Allow 60s for initial startup
```

## Configuration Profiles

### Development Profile

**Purpose:** Local development with debugging enabled

**.env Settings:**
```bash
# Server
WEBUI_EXTERNAL_PORT=3000
LOG_LEVEL=DEBUG
ENABLE_WEBSOCKET_LOGGING=True

# Backend (localhost)
OPENAI_API_BASE_URL=http://localhost:8079/v1
OPENAI_API_KEY=sk-dev-key

# Security (relaxed)
ENABLE_SIGNUP=True
JWT_EXPIRES_IN=604800  # 7 days
ENABLE_RAG_WEB_LOADER_SSL_VERIFICATION=False

# Features
ENABLE_RAG_WEB_SEARCH=True
```

**Use Case:** Developer testing, debugging, local experimentation

### Production Profile

**Purpose:** Production deployment with security and performance

**.env Settings:**
```bash
# Server
WEBUI_EXTERNAL_PORT=80
WEB_URL=https://chat.example.com
LOG_LEVEL=INFO
ENABLE_WEBSOCKET_LOGGING=False

# Backend (internal network)
OPENAI_API_BASE_URL=http://robaiproxy:8079/v1
OPENAI_API_KEY=sk-prod-key-with-long-random-string

# Security (strict)
ENABLE_SIGNUP=False  # Admin creates users
DEFAULT_USER_ROLE=user
JWT_EXPIRES_IN=43200  # 12 hours
WEBUI_SECRET_KEY=<strong-random-32-character-key>

# Features (selective)
ENABLE_RAG_WEB_SEARCH=True
ENABLE_MODEL_FILTER=True
MODEL_FILTER_LIST=Qwen3-30B
```

**docker-compose.yml Settings:**
```yaml
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '2.0'
  restart_policy:
    condition: on-failure
    max_attempts: 3
```

**Use Case:** Public-facing deployment, multi-user environment

### High-Traffic Profile

**Purpose:** Handle many concurrent users

**.env Settings:**
```bash
# Performance
POOL_SIZE=50  # Larger connection pool
POOL_PRE_PING=True
LOG_LEVEL=WARNING  # Reduce log overhead

# Backend (load balanced)
OPENAI_API_BASE_URL=http://robaiproxy-lb:8079/v1

# Security
JWT_EXPIRES_IN=28800  # 8 hours (reduce active sessions)
```

**docker-compose.yml Settings:**
```yaml
deploy:
  replicas: 3  # Run 3 instances
  resources:
    limits:
      memory: 4G
      cpus: '4.0'
```

**Additional Setup:**
- Nginx load balancer in front of Open WebUI instances
- Shared volume for uploads (NFS or object storage)
- External database (PostgreSQL instead of SQLite)

### Low-Resource Profile

**Purpose:** Minimal resource usage for small deployments

**.env Settings:**
```bash
# Performance
POOL_SIZE=5  # Smaller connection pool
LOG_LEVEL=WARNING  # Minimal logging

# Features (disabled)
ENABLE_IMAGE_GENERATION=False
ENABLE_RAG_WEB_SEARCH=False
```

**docker-compose.yml Settings:**
```yaml
deploy:
  resources:
    limits:
      memory: 512M
      cpus: '1.0'
```

**Use Case:** Personal use, single user, limited hardware

## Customization Options

### Frontend Customization

**Branding:**
- Logo: Replace `/app/frontend/build/assets/logo.svg`
- Favicon: Replace `/app/frontend/build/favicon.ico`
- Title: Set via `WEB_UI_NAME` environment variable

**Theme:**
- CSS: Modify `/app/frontend/build/assets/*.css`
- Colors: Edit theme variables in CSS
- Note: Requires rebuilding Docker image

**Research Mode Button:**
- Already customized with flask icon
- Color: Gray (off), Blue (research), Dark Blue (deep)
- Can modify in `MessageInput.svelte` (requires rebuild)

### Backend Customization

**Custom Endpoints:**
- Add to `/app/backend/open_webui/routers/`
- Register in `/app/backend/open_webui/main.py`
- Requires Docker image rebuild

**Authentication Providers:**
- OAuth: Configure via `OAUTH_*` environment variables
- LDAP: Configure via `LDAP_*` environment variables
- SSO: Requires custom integration

### Patch Customization

**Modify Existing Patches:**
1. Edit Dockerfile RUN commands
2. Rebuild image: `docker compose build open-webui`
3. Restart: `docker compose up -d open-webui`

**Add New Patches:**
```dockerfile
# In robaiwebui/Dockerfile
RUN sed -i 's/old_text/new_text/g' /app/backend/path/to/file.py
```

## Monitoring Configuration

### Application Metrics

**Prometheus Integration:**
```yaml
environment:
  - ENABLE_PROMETHEUS_METRICS=True
  - PROMETHEUS_PORT=9090
```

**Metrics Exposed:**
- Request count and latency
- Active users and sessions
- Database connection pool usage
- WebSocket connection count

### Log Aggregation

**Docker Logging Driver:**
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

**External Log Shipping:**
```yaml
logging:
  driver: "syslog"
  options:
    syslog-address: "tcp://logserver:514"
    tag: "open-webui"
```

### Health Monitoring

**External Health Check:**
```bash
# Add to monitoring system (Nagios, Zabbix, etc.)
curl -f http://localhost:80/ || alert "Open WebUI down"
```

**Database Health:**
```bash
# Check database size
docker exec open-webui ls -lh /app/backend/data/webui.db

# Check for corruption
docker exec open-webui sqlite3 /app/backend/data/webui.db "PRAGMA integrity_check"
```

## Troubleshooting Configuration

### Configuration Verification

**Check Environment Variables:**
```bash
# View active configuration
docker exec open-webui env | grep -E "(WEBUI|OPENAI|ENABLE)"

# Check specific variable
docker exec open-webui printenv OPENAI_API_BASE_URL
```

**Verify Patches Applied:**
```bash
# Metadata headers patch
docker exec open-webui grep ENABLE_FORWARD_USER_INFO_HEADERS \
  /app/backend/open_webui/env.py

# Should show: "True" default
```

### Common Configuration Issues

**Port Already in Use:**
```bash
# Symptom: Can't start on port 80
# Solution: Change WEBUI_EXTERNAL_PORT
WEBUI_EXTERNAL_PORT=8080  # Use different port
```

**Backend Not Reachable:**
```bash
# Symptom: No responses in chat
# Check: OPENAI_API_BASE_URL points to running service
curl http://192.168.10.50:8079/health

# If fails: Verify robaiproxy is running
cd robaiproxy
python requestProxy.py  # Start if needed
```

**Session Expiration Too Short:**
```bash
# Symptom: Users logged out frequently
# Solution: Increase JWT_EXPIRES_IN
JWT_EXPIRES_IN=86400  # 24 hours instead of default
```

**Volume Not Persistent:**
```bash
# Symptom: Chat history lost on restart
# Check: Volume properly mounted
docker inspect open-webui | grep -A 10 Mounts

# Should show: /app/backend/data mapped to volume
```

### Reset Configuration

**Reset to Defaults:**
```bash
# 1. Stop service
docker compose stop open-webui

# 2. Remove volume (LOSES ALL DATA!)
docker volume rm open-webui_open-webui

# 3. Clear environment overrides
# Edit .env, remove custom settings

# 4. Restart fresh
docker compose up -d open-webui
```

**Partial Reset (Keep Data):**
```bash
# Remove only secret key (forces regeneration)
docker exec open-webui rm /app/backend/data/WEBUI_SECRET_KEY

# Restart
docker compose restart open-webui
```

## Performance Tuning

### Database Optimization

**Enable WAL Mode:**
```bash
# Better concurrency for SQLite
docker exec open-webui sqlite3 /app/backend/data/webui.db \
  "PRAGMA journal_mode=WAL"
```

**Vacuum Database:**
```bash
# Reclaim space and optimize
docker exec open-webui sqlite3 /app/backend/data/webui.db \
  "VACUUM; ANALYZE;"
```

### Connection Pool Tuning

**High Traffic:**
```bash
# Increase pool for many concurrent users
POOL_SIZE=50
POOL_MAX_OVERFLOW=10
```

**Low Resource:**
```bash
# Minimize connections for small deployments
POOL_SIZE=5
POOL_MAX_OVERFLOW=2
```

### Logging Optimization

**Reduce Log Volume:**
```bash
LOG_LEVEL=WARNING  # Only log warnings and errors
ENABLE_WEBSOCKET_LOGGING=False  # Disable verbose WebSocket logs
```

**Structured Logging:**
```bash
# JSON format for log aggregation
LOG_FORMAT=json
```

## Next Steps

1. **Getting Started:** Try [Getting Started](getting-started.md) for initial setup and usage
2. **Architecture:** Review [Architecture](architecture.md) for technical implementation details
3. **API Reference:** See [API Reference](api-reference.md) for endpoint documentation
4. **Deployment:** Apply appropriate configuration profile for your use case
