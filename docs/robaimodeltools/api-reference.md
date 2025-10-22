---
layout: default
title: API Reference
parent: robaimodeltools
nav_order: 3
---

# API Reference

Complete API documentation for robaimodeltools.

## Operations Layer API

### Crawl4AIRAG Class

Main entry point for all operations. Located in `robaimodeltools/operations/crawler.py`.

```python
from robaimodeltools.operations.crawler import Crawl4AIRAG

crawler = Crawl4AIRAG()
```

#### Crawling Operations

##### crawl_and_store()

Crawl a single URL and store in the knowledge base.

```python
def crawl_and_store(
    url: str,
    tags: Optional[List[str]] = None,
    retention_policy: str = "permanent",
    session_id: Optional[str] = None
) -> Dict[str, Any]
```

**Parameters:**
- `url` (str): The URL to crawl
- `tags` (List[str], optional): Tags for categorization
- `retention_policy` (str): One of `permanent`, `session_only`, `30_days` (default: `permanent`)
- `session_id` (str, optional): Session identifier for grouping

**Returns:**
Dictionary with:
- `success` (bool): Whether the operation succeeded
- `url` (str): The crawled URL
- `title` (str): Extracted page title
- `word_count` (int): Number of words in content
- `session_id` (str): Session identifier
- `error` (str, optional): Error message if failed

**Example:**
```python
result = crawler.crawl_and_store(
    url="https://fastapi.tiangolo.com/tutorial/",
    tags=["python", "api", "tutorial"],
    retention_policy="permanent"
)
print(f"Stored: {result['title']}")
```

##### crawl_and_store_batch()

Crawl multiple URLs concurrently.

```python
def crawl_and_store_batch(
    urls: List[str],
    tags: Optional[List[str]] = None,
    retention_policy: str = "permanent",
    max_concurrent: int = 5,
    session_id: Optional[str] = None
) -> Dict[str, Any]
```

**Parameters:**
- `urls` (List[str]): List of URLs to crawl
- `tags` (List[str], optional): Tags applied to all URLs
- `retention_policy` (str): Retention policy for all URLs
- `max_concurrent` (int): Maximum concurrent crawls (default: 5)
- `session_id` (str, optional): Session identifier

**Returns:**
Dictionary with:
- `success` (bool): Overall operation status
- `total` (int): Total URLs provided
- `successful` (int): Successfully crawled URLs
- `failed` (int): Failed URLs
- `results` (List[Dict]): Individual results per URL
- `session_id` (str): Session identifier

**Example:**
```python
result = crawler.crawl_and_store_batch(
    urls=[
        "https://docs.python.org/3/tutorial/",
        "https://fastapi.tiangolo.com/",
        "https://www.sqlalchemy.org/docs/"
    ],
    tags=["python", "documentation"],
    max_concurrent=3
)
print(f"Success: {result['successful']}/{result['total']}")
```

##### deep_crawl()

Recursively crawl a website using breadth-first search.

```python
def deep_crawl(
    start_url: str,
    max_depth: int = 2,
    max_pages: int = 50,
    same_domain_only: bool = True,
    tags: Optional[List[str]] = None,
    retention_policy: str = "permanent",
    rate_limit: float = 1.0
) -> Dict[str, Any]
```

**Parameters:**
- `start_url` (str): Starting URL for crawl
- `max_depth` (int): Maximum link depth (default: 2)
- `max_pages` (int): Maximum pages to crawl (default: 50)
- `same_domain_only` (bool): Restrict to same domain (default: True)
- `tags` (List[str], optional): Tags for all pages
- `retention_policy` (str): Retention policy
- `rate_limit` (float): Seconds between requests (default: 1.0)

**Returns:**
Dictionary with:
- `success` (bool): Overall status
- `total_crawled` (int): Pages successfully crawled
- `total_failed` (int): Pages that failed
- `max_depth_reached` (int): Maximum depth achieved
- `urls_crawled` (List[str]): Successfully crawled URLs
- `session_id` (str): Session identifier

**Example:**
```python
result = crawler.deep_crawl(
    start_url="https://fastapi.tiangolo.com/",
    max_depth=2,
    max_pages=20,
    same_domain_only=True,
    tags=["fastapi", "docs"],
    rate_limit=0.5
)
print(f"Crawled {result['total_crawled']} pages")
```

#### Search Operations

##### search_knowledge()

Perform semantic search with vector similarity (simple search).

```python
def search_knowledge(
    query: str,
    top_k: int = 10,
    tags: Optional[str] = None,
    session_id: Optional[str] = None
) -> List[Dict[str, Any]]
```

**Parameters:**
- `query` (str): Search query
- `top_k` (int): Maximum results to return (default: 10)
- `tags` (str, optional): Filter by tags (comma-separated)
- `session_id` (str, optional): Filter by session

**Returns:**
List of dictionaries with:
- `url` (str): Document URL
- `title` (str): Document title
- `preview` (str): Content preview
- `similarity` (float): Cosine similarity score (0-1)
- `tags` (List[str]): Document tags

**Example:**
```python
results = crawler.search_knowledge(
    query="How to handle authentication in FastAPI?",
    top_k=10,
    tags="python,api"
)

for result in results:
    print(f"{result['similarity']:.2f} - {result['title']}")
    print(f"  {result['preview']}")
```

##### advanced_search()

5-phase RAG pipeline search with knowledge graph enhancement.

```python
def advanced_search(
    query: str,
    top_k: int = 10,
    tags: Optional[str] = None
) -> Dict[str, Any]
```

**Parameters:**
- `query` (str): Search query
- `top_k` (int): Maximum results (default: 10)
- `tags` (str, optional): Filter by tags

**Returns:**
Comprehensive dictionary with:
- `success` (bool): Operation status
- `query` (Dict): Query analysis
  - `original` (str): Original query
  - `normalized` (str): Normalized query
  - `entities` (List[Dict]): Extracted entities
  - `intent` (str): Query intent
  - `confidence` (float): Overall confidence
- `exploration` (Dict): Entity expansion details
  - `original_entity_count` (int)
  - `expanded_entity_count` (int)
  - `expansion_relationships` (List)
  - `discovered_entities` (List)
- `results` (List[Dict]): Search results
  - `rank` (int): Result position
  - `url` (str): Document URL
  - `title` (str): Document title
  - `preview` (str): Relevant excerpt
  - `score` (float): Overall score
  - `score_breakdown` (Dict): Individual signal scores
  - `timestamp` (str): Document timestamp
  - `tags` (List[str]): Document tags
  - `source` (str): Retrieval source
  - `entity_mentions` (List[str]): Entities found
- `result_count` (int): Total results returned
- `total_time_ms` (int): Query execution time
- `suggested_queries` (List[str]): Related searches
- `related_entities` (List[Dict]): Related entities

**Example:**
```python
response = crawler.advanced_search(
    query="FastAPI dependency injection with database sessions",
    top_k=10
)

print(f"Query Intent: {response['query']['intent']}")
print(f"Extracted Entities: {[e['text'] for e in response['query']['entities']]}")
print(f"Found {response['result_count']} results in {response['total_time_ms']}ms")

for result in response['results']:
    print(f"\n{result['rank']}. {result['title']} (Score: {result['score']:.3f})")
    print(f"   Vector: {result['score_breakdown']['vector']:.2f} | "
          f"Graph: {result['score_breakdown']['graph']:.2f} | "
          f"BM25: {result['score_breakdown']['bm25']:.2f}")
    print(f"   {result['preview']}")
```

#### Content Management

##### list_memory()

List stored content with filtering.

```python
def list_memory(
    session_id: Optional[str] = None,
    retention_policy: Optional[str] = None,
    tags: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]
```

**Parameters:**
- `session_id` (str, optional): Filter by session
- `retention_policy` (str, optional): Filter by retention policy
- `tags` (str, optional): Filter by tags (comma-separated)
- `limit` (int): Maximum results (default: 100)

**Returns:**
List of dictionaries with:
- `url` (str): Document URL
- `title` (str): Document title
- `word_count` (int): Content word count
- `timestamp` (str): Storage timestamp
- `session_id` (str): Session identifier
- `retention_policy` (str): Retention policy
- `tags` (List[str]): Document tags

**Example:**
```python
# List all permanent content
content = crawler.list_memory(retention_policy="permanent")

# List session-specific content
session_content = crawler.list_memory(session_id="abc123")

# List by tags
tagged = crawler.list_memory(tags="python,tutorial", limit=50)
```

##### delete_url()

Delete a specific URL from the knowledge base.

```python
def delete_url(url: str) -> Dict[str, Any]
```

**Parameters:**
- `url` (str): URL to delete

**Returns:**
Dictionary with:
- `success` (bool): Whether deletion succeeded
- `url` (str): The deleted URL
- `error` (str, optional): Error message if failed

**Example:**
```python
result = crawler.delete_url("https://example.com/old-page")
print(f"Deleted: {result['success']}")
```

##### clear_session()

Delete all content from a session.

```python
def clear_session(session_id: str) -> Dict[str, Any]
```

**Parameters:**
- `session_id` (str): Session to clear

**Returns:**
Dictionary with:
- `success` (bool): Operation status
- `session_id` (str): Cleared session
- `deleted_count` (int): Number of items deleted

**Example:**
```python
result = crawler.clear_session("temp_research_session")
print(f"Deleted {result['deleted_count']} items")
```

#### Domain Management

##### add_blocked_domain()

Block a domain pattern from crawling.

```python
def add_blocked_domain(pattern: str) -> Dict[str, Any]
```

**Parameters:**
- `pattern` (str): Domain pattern (supports wildcards)

**Returns:**
Dictionary with:
- `success` (bool): Operation status
- `pattern` (str): Added pattern

**Example:**
```python
crawler.add_blocked_domain("*.spam-site.com")
crawler.add_blocked_domain("*malicious*")
```

##### list_blocked_domains()

List all blocked domain patterns.

```python
def list_blocked_domains() -> List[str]
```

**Returns:**
List of blocked domain patterns.

**Example:**
```python
blocked = crawler.list_blocked_domains()
print(f"Blocked domains: {blocked}")
```

##### remove_blocked_domain()

Remove a domain from the blocklist.

```python
def remove_blocked_domain(pattern: str) -> Dict[str, Any]
```

**Parameters:**
- `pattern` (str): Pattern to remove

**Returns:**
Dictionary with:
- `success` (bool): Operation status
- `pattern` (str): Removed pattern

#### Session Management

##### create_session()

Create a new crawling session.

```python
def create_session() -> str
```

**Returns:**
Session ID (str): UUID-based session identifier

**Example:**
```python
session_id = crawler.create_session()
crawler.crawl_and_store(
    url="https://example.com",
    session_id=session_id,
    retention_policy="session_only"
)
```

##### list_sessions()

List all active sessions.

```python
def list_sessions() -> List[Dict[str, Any]]
```

**Returns:**
List of dictionaries with:
- `session_id` (str): Session identifier
- `created_at` (str): Creation timestamp
- `content_count` (int): Items in session

##### get_database_stats()

Get database statistics.

```python
def get_database_stats() -> Dict[str, Any]
```

**Returns:**
Dictionary with:
- `total_urls` (int): Total stored URLs
- `total_sessions` (int): Active sessions
- `permanent_content` (int): Permanent items
- `session_only_content` (int): Session-only items
- `30_day_content` (int): 30-day retention items
- `blocked_domains` (int): Blocked domain count

## Search Layer API

### SearchHandler Class

High-level interface for the 5-phase RAG pipeline. Singleton pattern.

```python
from robaimodeltools.search.search_handler import SearchHandler
from robaimodeltools.data.storage import GLOBAL_DB

handler = SearchHandler(
    db=GLOBAL_DB,
    kg_service_url="http://kg-service:8088"
)
```

#### search()

Execute the full 5-phase pipeline.

```python
def search(
    query: str,
    top_k: int = 10,
    tags: Optional[str] = None
) -> Dict[str, Any]
```

Returns the same comprehensive response structure as `Crawl4AIRAG.advanced_search()`.

### QueryParser Class

Phase 1: Entity extraction and query understanding.

```python
from robaimodeltools.search.query_parser import get_query_parser

parser = get_query_parser()  # Singleton
parsed = parser.parse(query="FastAPI with SQLAlchemy")
```

**Output:**
```python
{
    "original_query": "FastAPI with SQLAlchemy",
    "normalized_query": "fastapi with sqlalchemy",
    "entities": [
        {"text": "FastAPI", "type": "FRAMEWORK", "confidence": 0.95},
        {"text": "SQLAlchemy", "type": "LIBRARY", "confidence": 0.92}
    ],
    "intent": "informational",
    "confidence": 0.88,
    "variants": [
        "fastapi with sqlalchemy",
        "FastAPI SQLAlchemy",
        "fastapi sqlalchemy"
    ]
}
```

### VectorRetriever Class

Phase 2: Vector similarity search.

```python
from robaimodeltools.search.vector_retriever import VectorRetriever

retriever = VectorRetriever(db=GLOBAL_DB)
results = retriever.retrieve(
    query="FastAPI authentication",
    top_k=10,
    tags="python"
)
```

### GraphRetriever Class

Phase 2: Knowledge graph retrieval.

```python
from robaimodeltools.search.graph_retriever import GraphRetriever

retriever = GraphRetriever(
    db=GLOBAL_DB,
    kg_service_url="http://kg-service:8088"
)

results = await retriever.retrieve_async(
    entities=[{"text": "FastAPI", "type": "FRAMEWORK"}],
    top_k=10
)
```

### EntityExpander Class

Phase 3: Entity relationship expansion.

```python
from robaimodeltools.search.entity_expander import EntityExpander

expander = EntityExpander(kg_service_url="http://kg-service:8088")
expanded = await expander.expand_entities(
    entities=[{"text": "FastAPI", "type": "FRAMEWORK"}]
)
```

**Output:**
```python
{
    "original_entities": [...],
    "expanded_entities": [
        {"text": "Pydantic", "type": "LIBRARY", "confidence": 0.85},
        {"text": "Starlette", "type": "FRAMEWORK", "confidence": 0.80}
    ],
    "relationships": [
        {"source": "FastAPI", "target": "Pydantic", "type": "USES"},
        {"source": "FastAPI", "target": "Starlette", "type": "DEPENDS_ON"}
    ]
}
```

### AdvancedRanker Class

Phase 4: Multi-signal ranking.

```python
from robaimodeltools.search.advanced_ranker import AdvancedRanker

ranker = AdvancedRanker(
    vector_weight=0.35,
    graph_weight=0.25,
    bm25_weight=0.20,
    recency_weight=0.10,
    title_weight=0.10
)

ranked = ranker.rank(
    results=combined_results,
    query="FastAPI authentication",
    entities=[...]
)
```

### ResponseFormatter Class

Phase 5: Response structuring.

```python
from robaimodeltools.search.response_formatter import get_response_formatter

formatter = get_response_formatter()  # Singleton
response = formatter.format_response(
    query_info={...},
    results=[...],
    exploration={...},
    total_time_ms=1234
)
```

## Data Layer API

### RAGDatabase Class

Core database abstraction.

```python
from robaimodeltools.data.storage import RAGDatabase

db = RAGDatabase(
    db_path="/path/to/database.db",
    use_memory=True,
    chunk_size=1000
)
```

#### store_crawled_content()

Store crawled content with embeddings.

```python
def store_crawled_content(
    url: str,
    title: str,
    content: str,
    markdown: str,
    session_id: str,
    tags: Optional[List[str]] = None,
    retention_policy: str = "permanent"
) -> Dict[str, Any]
```

**Returns:**
Dictionary with:
- `content_rowid` (int): Database row ID
- `chunk_count` (int): Number of chunks created
- `word_count` (int): Content word count

#### search_similar()

Vector similarity search.

```python
def search_similar(
    query: str,
    top_k: int = 10,
    tags: Optional[List[str]] = None,
    session_id: Optional[str] = None
) -> List[Dict[str, Any]]
```

#### get_content_by_url()

Retrieve content by URL.

```python
def get_content_by_url(url: str) -> Optional[Dict[str, Any]]
```

#### delete_by_url()

Delete content and associated data.

```python
def delete_by_url(url: str) -> int
```

**Returns:**
Number of rows deleted.

### SyncManager Class

Differential sync for RAM mode.

```python
from robaimodeltools.data.sync_manager import SyncManager

sync_manager = SyncManager(
    memory_db=memory_connection,
    disk_db_path="/path/to/disk.db",
    idle_seconds=5,
    periodic_minutes=5
)

sync_manager.start()  # Start background sync

# Get metrics
metrics = sync_manager.get_metrics()
# {
#   'total_syncs': 42,
#   'last_sync_time': '2024-01-15T10:30:00',
#   'last_sync_duration_ms': 123,
#   'rows_synced': 15
# }
```

### ContentCleaner Class

Post-crawl content processing.

```python
from robaimodeltools.data.content_cleaner import ContentCleaner

cleaner = ContentCleaner()
cleaned = cleaner.clean_content(raw_content)

# Get quality metrics
metrics = cleaner.get_cleaning_metrics(cleaned)
# {
#   'original_lines': 500,
#   'cleaned_lines': 350,
#   'removed_navigation': 80,
#   'removed_short_lines': 70,
#   'quality_score': 0.85
# }
```

## Global Singletons

### GLOBAL_DB

Single database instance shared across operations.

```python
from robaimodeltools.data.storage import GLOBAL_DB

# Direct access
stats = GLOBAL_DB.get_stats()
content = GLOBAL_DB.get_content_by_url("https://example.com")
```

### Model Singletons

Shared model instances to avoid repeated loading.

```python
from robaimodeltools.search.query_parser import get_query_parser
from robaimodeltools.search.embeddings import get_query_embedder
from robaimodeltools.search.response_formatter import get_response_formatter

parser = get_query_parser()        # GLiNER model
embedder = get_query_embedder()    # SentenceTransformer
formatter = get_response_formatter()
```

## Return Types Reference

### Search Result

```python
{
    "rank": int,
    "url": str,
    "title": str,
    "preview": str,              # 200-character excerpt
    "score": float,              # 0-1 combined score
    "score_breakdown": {
        "vector": float,         # 0-1 normalized
        "graph": float,
        "bm25": float,
        "recency": float,
        "title": float
    },
    "timestamp": str,            # ISO 8601
    "tags": List[str],
    "source": str,               # "vector", "graph", "hybrid"
    "entity_mentions": List[str]
}
```

### Entity

```python
{
    "text": str,                 # Entity surface form
    "type": str,                 # One of 119 types
    "confidence": float          # 0-1 confidence score
}
```

### Session

```python
{
    "session_id": str,           # UUID
    "created_at": str,           # ISO 8601
    "content_count": int
}
```

## Error Handling

All methods return dictionaries with `success` boolean and optional `error` message.

```python
result = crawler.crawl_and_store("https://invalid-url")

if not result["success"]:
    print(f"Error: {result['error']}")
else:
    print(f"Success: {result['url']}")
```

Common error scenarios:
- Invalid URL format
- Network timeout
- Blocked domain
- Database write failure
- KG service unavailable (graceful degradation)

## Next Steps

- [Architecture](architecture.html) - Understand system design
- [Configuration](configuration.html) - Configure the system
- [Getting Started](getting-started.html) - Basic usage examples
