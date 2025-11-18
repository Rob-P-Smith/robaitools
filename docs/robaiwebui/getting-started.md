---
layout: default
title: Getting Started
parent: robaiwebui
nav_order: 1
---

# Getting Started with robaiwebui

Learn how to access the web interface, start chatting with LLMs, use research mode, and leverage the integrated RAG system for intelligent conversations.

## Understanding robaiwebui

robaiwebui is **the web-based chat interface** you access in your browser. It's a customized version of Open WebUI that provides:

- **Familiar Chat Interface** - ChatGPT-like experience with streaming responses
- **Research Mode** - Click the flask icon to enable autonomous multi-turn research
- **Multi-Model Support** - Select different models for different conversations
- **Session Management** - Your chat history is saved and persistent
- **Real-Time Feedback** - Watch status updates as research progresses

**No installation needed!** Open WebUI runs as a Docker container. Once the services are started, just open your browser.

## Prerequisites

**Required:**
- Docker and Docker Compose running
- robaitools services started (robaiproxy must be running)
- Web browser (Chrome, Firefox, Safari, Edge)
- Port 80 accessible on your system

**Optional:**
- User account (created on first access)
- Modern browser for best experience (WebSocket support)

## Quick Start: First Chat

### Step 1: Access Open WebUI

```bash
# Open in your browser
http://localhost:80

# Or from another machine on your network
http://192.168.10.50:80
```

**Expected:** Open WebUI login/signup page loads

### Step 2: Create User Account

**First-time users:**
1. Click "Sign Up" on the login page
2. Enter email, username, password
3. Click "Create Account"
4. You're automatically logged in

**Note:** First user created becomes admin with full privileges

### Step 3: Start a Conversation

1. You'll see the chat interface with an empty message box
2. Select a model from the dropdown (top of page) - default is usually fine
3. Type your first message: "Hello! What can you help me with?"
4. Press Enter or click Send
5. Watch the response stream in real-time

**Expected output:**
```
Assistant responds with available capabilities, including:
- Answering questions from knowledge base
- Crawling and indexing web content
- Searching for information
- Research mode for comprehensive topic exploration
```

### Step 4: Try a Knowledge Base Query

```
You: What is FastAPI?
```

**What happens:**
1. robaiwebui sends your message to robaiproxy
2. robaiproxy routes to RAG system (robairagapi + robaitragmcp)
3. Vector search finds relevant documents from knowledge base
4. Response is generated with context from indexed content
5. Answer streams back to your browser in real-time

**Expected response:** Information about FastAPI from indexed documentation

### Step 5: Try Research Mode

**Enable research mode:**
1. Look for the **flask/beaker icon** in the message input toolbar (bottom right)
2. Click it once - icon turns blue (research mode enabled)
3. Type your question: "research python async programming best practices"
4. Send the message

**What happens:**
1. Message gets `<research_request>` prefix automatically
2. robaiproxy detects prefix and triggers research orchestration
3. Status updates appear ABOVE the message area:
   - "Turn 1 - Searching knowledge base..."
   - "Turn 1 - Crawling web sources..."
   - "Turn 2 - Analyzing implementation details..."
4. Final comprehensive response generated with accumulated context
5. Status auto-clears when done

**Expected response:** Comprehensive research report with multiple sources, practical examples, and detailed explanations

## Basic Usage

### Pattern 1: Standard Question-Answer

**Use case:** Quick questions with short answers from knowledge base

**Steps:**
1. Ensure research mode is OFF (flask icon is gray)
2. Type your question
3. Press Enter
4. Read streaming response

**Example:**
```
You: How do I install Docker?

Response:  Here's a step-by-step guide to install Docker...
[Streaming response with installation instructions from knowledge base]
```

**Performance:** Typical response time 1-3 seconds

### Pattern 2: Research Mode (2 Iterations)

**Use case:** Comprehensive research on a topic with web search and source crawling

**Steps:**
1. Click flask icon once (turns blue)
2. Type your research question
3. Send message
4. Watch status updates in real-time
5. Read comprehensive final report

**Example:**
```
You: research FastAPI performance optimization techniques

Status updates you'll see:
- Turn 1 - Searching knowledge base... (3 results found)
- Turn 1 - Crawling web sources... (2 URLs indexed)
- Turn 1 - Searching web... (5 external results)
- Turn 2 - Analyzing implementation details...
- Turn 2 - Searching knowledge base... (6 results found)
- Generating comprehensive answer...

Final Response: [10-20 paragraphs covering FastAPI performance optimization with:
- Best practices from documentation
- Real-world examples from crawled sources
- Performance benchmarks
- Code patterns and anti-patterns
- Tool recommendations]
```

**Performance:** Typical research time 30-60 seconds (2 iterations)

### Pattern 3: Deep Research Mode (4 Iterations)

**Use case:** Exhaustive research with advanced features and ecosystem exploration

**Steps:**
1. Click flask icon TWICE (turns darker blue)
2. Type your question with "thoroughly", "comprehensive", or "deep"
3. Send message
4. Wait for 4-iteration research cycle
5. Review extensive final report

**Example:**
```
You: thoroughly research kubernetes deployment strategies

Status updates (4 iterations):
- Turn 1 - Main concepts research...
- Turn 2 - Practical implementation...
- Turn 3 - Advanced features...
- Turn 4 - Ecosystem exploration...

Final Response: [30-50 paragraphs covering:
- Deployment strategy overview
- Step-by-step implementation guides
- Advanced features (rolling updates, canary deployments, blue-green)
- Tool ecosystem (Helm, Kustomize, ArgoCD)
- Comparison of approaches
- Real-world case studies]
```

**Performance:** Typical research time 90-180 seconds (4 iterations)

**Note:** Deep research auto-reduces to 2 iterations if context overflow occurs

## Common Workflows

### Workflow 1: Exploring a New Technology

**Goal:** Learn about a technology from scratch

**Steps:**
1. Start with standard chat: "What is Kubernetes?"
   - Get quick overview
2. Follow up with targeted questions:
   - "How does Kubernetes networking work?"
   - "What are Kubernetes deployments?"
3. Enable research mode (1 click)
4. Ask comprehensive question:
   - "research kubernetes deployment best practices"
5. Review detailed report
6. Ask follow-ups in same conversation for context

**Result:** Solid understanding of technology with practical knowledge

### Workflow 2: Troubleshooting an Issue

**Goal:** Debug a specific problem

**Steps:**
1. Describe the problem in chat:
   - "My FastAPI app is slow, how do I optimize it?"
2. Get initial suggestions
3. Try suggested solutions
4. If needed, enable research mode:
   - "research FastAPI performance profiling tools"
5. Get comprehensive troubleshooting guide
6. Apply solutions and report back

**Result:** Problem solved with understanding of root cause

### Workflow 3: Building Something New

**Goal:** Implement a feature or project

**Steps:**
1. Ask for architecture guidance:
   - "How should I structure a FastAPI microservice?"
2. Get code examples from knowledge base
3. Enable deep research mode (2 clicks)
4. Ask for comprehensive implementation guide:
   - "thoroughly research building production-ready FastAPI services"
5. Review extensive guide covering:
   - Project structure
   - Security best practices
   - Testing strategies
   - Deployment options
   - Monitoring and observability
6. Ask follow-ups as you implement

**Result:** Production-ready implementation with industry best practices

### Workflow 4: Comparing Technologies

**Goal:** Make an informed technology choice

**Steps:**
1. Enable research mode
2. Ask comparison question:
   - "research FastAPI vs Flask for REST APIs"
3. Get detailed comparison covering:
   - Performance benchmarks
   - Feature comparison
   - Developer experience
   - Ecosystem maturity
   - Use case fit
4. Ask follow-ups about specific concerns:
   - "What about async support in Flask?"
5. Make informed decision

**Result:** Data-driven technology choice with trade-off understanding

## Interface Features

### Chat Management

**Creating New Chats:**
- Click "+ New Chat" button (top left)
- Each chat has independent context
- Chats are saved automatically

**Accessing Chat History:**
- Sidebar shows all previous chats (click hamburger menu if hidden)
- Search chats by content
- Organize into folders (premium feature)

**Editing Messages:**
- Hover over any message
- Click edit icon
- Modify and resend
- Creates new branch in conversation

**Deleting Chats:**
- Right-click chat in sidebar
- Select "Delete"
- Confirmation required

### Model Selection

**Changing Models:**
1. Click model dropdown (top of chat)
2. Select from available models
3. Model applies to current conversation only

**Model Persistence:**
- Each chat remembers its model selection
- New chats use default model
- Can change model mid-conversation

### Research Mode Controls

**Research Mode States:**
1. **Off** (gray flask) - Standard chat with RAG
2. **Research** (blue flask) - 2-iteration research
3. **Deep Research** (darker blue flask) - 4-iteration research

**Toggling:**
- Click to cycle through states
- State persists in sessionStorage
- Reset with Escape key

**Resetting:**
- Press Escape key to clear all input settings
- Includes: research mode, file attachments, text content

### Status Updates

**Where They Appear:**
- ABOVE the message area (not inside the message)
- Replace each other (not stacked)
- Auto-clear when `done: true` received

**What They Show:**
- Current iteration (Turn 1, Turn 2, etc.)
- Current operation (Searching, Crawling, Analyzing)
- Time elapsed (updates every 10s)

**Example Status Sequence:**
```
Turn 1 - Searching knowledge base... (5s)
Turn 1 - Crawling web sources... (15s)
Turn 1 - Searching web... (20s)
Turn 2 - Analyzing implementation... (30s)
[Status clears, final response streams]
```

## Troubleshooting

### Interface Won't Load

**Symptom:** Browser shows "Unable to connect" or timeout

**Check:**
```bash
# Verify service is running
docker ps | grep open-webui

# Check health
curl http://localhost:8080/health
```

**Solution:**
- Ensure Docker services are running: `docker compose ps`
- Check port 80 is not in use by another service
- Try accessing via localhost:80 instead of IP address
- Check firewall isn't blocking port 80

### Can't Create Account

**Symptom:** Signup page fails or shows error

**Cause:** Database initialization issue or existing admin

**Solution:**
```bash
# Check Open WebUI logs
docker compose logs -f open-webui

# Look for database errors
# If needed, remove volume and restart (LOSES DATA!)
docker compose down
docker volume rm open-webui_open-webui
docker compose up -d open-webui
```

### No Response From Backend

**Symptom:** Message sent but no response appears

**Check:**
```bash
# Verify robaiproxy is running
curl http://localhost:8079/health

# Check logs
cd robaiproxy
tail -f proxy.log
```

**Solution:**
- Ensure robaiproxy is started (non-Docker service)
- Verify OPENAI_API_BASE_URL points to robaiproxy
- Check robaiproxy logs for errors
- Try standard chat before research mode

### Research Mode Button Missing

**Symptom:** Flask icon doesn't appear in message input

**Cause:** Frontend customization patches not applied

**Solution:**
```bash
# Rebuild container with patches
docker compose build open-webui
docker compose up -d open-webui

# Verify patches in Dockerfile
cat robaiwebui/Dockerfile | grep PATCH
```

### Status Updates Not Showing

**Symptom:** Research mode works but no status appears above message

**Cause:** Status Event Bridge patch not applied or WebSocket connection failed

**Check:**
```bash
# Check browser console (F12) for WebSocket errors
# Look for Socket.IO connection messages

# Verify middleware patch
docker compose logs open-webui | grep "status event"
```

**Solution:**
- Rebuild container to apply middleware patch
- Check browser supports WebSocket (all modern browsers do)
- Try different browser to rule out extension interference

### Slow Research Mode

**Symptom:** Research takes longer than expected (>5 minutes)

**Causes:**
- Web crawling slow sites
- Many URLs to index
- LLM backend slow
- Network issues

**Check:**
```bash
# Monitor research progress in proxy logs
cd robaiproxy
tail -f proxy.log | grep "research"

# Check system resources
docker stats
```

**Solutions:**
- Reduce max_pages in deep crawl configuration
- Check internet connection speed
- Monitor CPU/memory usage
- Wait for completion (research can take 1-3 minutes for complex topics)

### Chat History Lost

**Symptom:** Previous chats disappeared

**Cause:** Docker volume removed or data corruption

**Check:**
```bash
# Verify volume exists
docker volume ls | grep open-webui

# Check volume data
docker run --rm -v open-webui_open-webui:/data alpine ls -la /data
```

**Prevention:**
```bash
# Backup chat data periodically
docker run --rm -v open-webui_open-webui:/data -v $(pwd):/backup alpine \
  tar czf /backup/open-webui-backup-$(date +%Y%m%d).tar.gz /data
```

**Recovery:**
- Restore from backup if available
- Chats are lost if volume removed without backup

## Tips and Best Practices

**For Best Results:**
1. Use specific, detailed questions in research mode
2. Start with standard chat for quick clarifications
3. Use research mode for comprehensive topics
4. Use deep research for complex, multi-faceted topics
5. Ask follow-ups in same conversation for context continuity

**Research Mode Tips:**
1. Include keywords like "research", "thoroughly", "comprehensive" in question
2. Be specific about what you want to know
3. Wait for status updates to complete before expecting response
4. Review intermediate status to see what's being searched

**Performance Tips:**
1. Keep conversations focused on one topic
2. Start new chat for different topics
3. Use deep research sparingly (4 iterations is resource-intensive)
4. Close unused chat tabs to free browser memory

**Chat Organization:**
1. Name your chats descriptively (right-click to rename)
2. Delete old test chats periodically
3. Create new chat for each major topic
4. Use search to find old conversations

## Next Steps

1. **Learn the Architecture:** Review [Architecture](architecture.md) for technical details on patches and integration
2. **Configure Settings:** Check [Configuration](configuration.md) for environment variables and customization options
3. **Explore API:** See [API Reference](api-reference.md) for endpoint documentation and metadata structure
4. **Try Advanced Features:** Experiment with file uploads, model selection, and deep research mode

Congratulations! You now know how to use robaiwebui for interactive chat, comprehensive research, and knowledge base exploration!
