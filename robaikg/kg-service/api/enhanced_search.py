"""
Enhanced KG Search Endpoint

Implements sophisticated entity expansion with co-occurrence analysis
and relationship traversal for comprehensive document retrieval.
"""

import logging
from typing import List, Dict, Optional, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from storage.neo4j_client import get_neo4j_client

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1", tags=["Enhanced Search"])


# ============================================================================
# Request/Response Models
# ============================================================================

class EnhancedSearchRequest(BaseModel):
    """Request for enhanced KG search with entity expansion"""

    query: str = Field(..., description="Original search query text")
    search_term_entities: List[str] = Field(
        ...,
        description="Extracted entities from search query",
        min_items=1
    )
    max_chunks: int = Field(
        100,
        description="Maximum chunks to return",
        ge=1,
        le=500
    )

    class Config:
        schema_extra = {
            "example": {
                "query": "How does Neo4j integrate with Python FastAPI?",
                "search_term_entities": ["Neo4j", "Python", "FastAPI"],
                "max_chunks": 100
            }
        }


class ChunkScore(BaseModel):
    """Scored chunk result"""

    chunk_id: str = Field(..., description="Neo4j element ID")
    vector_rowid: int = Field(..., description="SQLite vector rowid")
    chunk_index: int = Field(..., description="Chunk index in document")
    chunk_text: str = Field(..., description="Chunk text content")
    document_url: str = Field(..., description="Source document URL")
    expansion_score: float = Field(..., description="Computed relevance score")
    search_entity_count: int = Field(..., description="Number of search term entities")
    expanded_entity_count: int = Field(..., description="Number of co-occurring entities")
    relationship_count: int = Field(..., description="Number of entity relationships found")


class EnhancedSearchResponse(BaseModel):
    """Response from enhanced search"""

    success: bool = True
    query: str = Field(..., description="Original query")
    chunks: List[ChunkScore] = Field(..., description="Scored chunks")
    total_chunks: int = Field(..., description="Total chunks returned")
    search_entities_found: int = Field(..., description="Search term entities found in graph")
    expanded_entities_found: int = Field(..., description="Co-occurring entities discovered")
    stats: Dict[str, Any] = Field(..., description="Query statistics")


# ============================================================================
# Enhanced Search Implementation
# ============================================================================

@router.post("/search/enhanced", response_model=EnhancedSearchResponse)
async def enhanced_kg_search(request: EnhancedSearchRequest):
    """
    Enhanced KG search with entity expansion and co-occurrence analysis

    Algorithm:
    1. Find search term entities in graph
    2. Get chunks mentioning search terms
    3. Find co-occurring entities (same chunks)
    4. Find relationships between search term entities
    5. Get chunks from expanded entities
    6. Score and rank all chunks
    7. Return top N unique chunks
    """
    try:
        neo4j_client = get_neo4j_client()

        logger.info(
            f"Enhanced search: query='{request.query}', "
            f"entities={request.search_term_entities}"
        )

        # Execute comprehensive graph query
        query_result = await _execute_enhanced_query(
            neo4j_client,
            request.search_term_entities,
            request.max_chunks
        )

        # Score and rank chunks
        scored_chunks = _score_and_rank_chunks(
            query_result,
            request.search_term_entities
        )

        # Limit to max_chunks
        top_chunks = scored_chunks[:request.max_chunks]

        stats = {
            "cypher_execution_time_ms": query_result.get("execution_time_ms", 0),
            "total_chunks_found": len(scored_chunks),
            "chunks_returned": len(top_chunks),
            "multi_entity_chunks": sum(1 for c in top_chunks if c["search_entity_count"] >= 2),
            "single_entity_chunks": sum(1 for c in top_chunks if c["search_entity_count"] == 1),
            "expansion_only_chunks": sum(1 for c in top_chunks if c["search_entity_count"] == 0)
        }

        logger.info(
            f"Enhanced search complete: {len(top_chunks)} chunks, "
            f"{stats['multi_entity_chunks']} multi-entity matches"
        )

        return EnhancedSearchResponse(
            success=True,
            query=request.query,
            chunks=[ChunkScore(**chunk) for chunk in top_chunks],
            total_chunks=len(top_chunks),
            search_entities_found=query_result.get("search_entities_count", 0),
            expanded_entities_found=query_result.get("expanded_entities_count", 0),
            stats=stats
        )

    except Exception as e:
        logger.error(f"Enhanced search failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Enhanced search failed: {str(e)}"
        )


async def _execute_enhanced_query(
    client,
    search_term_entities: List[str],
    max_chunks: int
) -> Dict[str, Any]:
    """
    Execute comprehensive Cypher query for entity expansion

    Single query strategy for optimal performance
    """

    cypher = """
    // Step 1: Find search term entities
    MATCH (search_entity:Entity)
    WHERE search_entity.text IN $search_terms

    // Step 2: Get chunks where search entities are mentioned
    OPTIONAL MATCH (search_entity)-[:MENTIONED_IN]->(search_chunk:Chunk)-[:PART_OF]->(doc:Document)

    // Step 3: Find co-occurring entities (same chunks as search terms)
    OPTIONAL MATCH (search_chunk)<-[:MENTIONED_IN]-(cooccur_entity:Entity)
    WHERE NOT cooccur_entity.text IN $search_terms

    // Step 4: Find relationships between search term entities
    OPTIONAL MATCH (search_entity)-[rel]-(related_search_entity:Entity)
    WHERE related_search_entity.text IN $search_terms
      AND id(search_entity) < id(related_search_entity)  // Avoid duplicates

    // Step 5: Get chunks mentioning co-occurring entities
    OPTIONAL MATCH (cooccur_entity)-[:MENTIONED_IN]->(expanded_chunk:Chunk)-[:PART_OF]->(expanded_doc:Document)

    // Aggregate results
    WITH
        collect(DISTINCT {
            entity: search_entity.text,
            mention_count: search_entity.mention_count,
            type: search_entity.type_primary
        }) as search_entities_found,

        collect(DISTINCT {
            chunk_id: elementId(search_chunk),
            vector_rowid: search_chunk.vector_rowid,
            chunk_index: search_chunk.chunk_index,
            text: search_chunk.text,
            doc_url: doc.url,
            search_entities: [e IN collect(DISTINCT search_entity.text) WHERE e IS NOT NULL],
            chunk_type: 'search_term'
        }) as search_chunks_data,

        collect(DISTINCT {
            entity: cooccur_entity.text,
            mention_count: cooccur_entity.mention_count,
            type: cooccur_entity.type_primary,
            cooccurs_in_chunks: count(DISTINCT search_chunk)
        }) as cooccurring_entities,

        collect(DISTINCT {
            from_entity: search_entity.text,
            to_entity: related_search_entity.text,
            relationship_type: type(rel),
            strength: 1.0
        }) as entity_relationships,

        collect(DISTINCT {
            chunk_id: elementId(expanded_chunk),
            vector_rowid: expanded_chunk.vector_rowid,
            chunk_index: expanded_chunk.chunk_index,
            text: expanded_chunk.text,
            doc_url: expanded_doc.url,
            expanded_entities: [e IN collect(DISTINCT cooccur_entity.text) WHERE e IS NOT NULL],
            chunk_type: 'expanded'
        }) as expanded_chunks_data

    RETURN
        search_entities_found,
        search_chunks_data,
        cooccurring_entities,
        entity_relationships,
        expanded_chunks_data
    """

    params = {
        "search_terms": search_term_entities,
        "max_chunks": max_chunks
    }

    import time
    start_time = time.time()

    async with client.driver.session(database=client.database) as session:
        result = await session.run(cypher, params)
        record = await result.single()

        execution_time_ms = (time.time() - start_time) * 1000

        if not record:
            return {
                "search_entities": [],
                "search_chunks": [],
                "cooccurring_entities": [],
                "relationships": [],
                "expanded_chunks": [],
                "search_entities_count": 0,
                "expanded_entities_count": 0,
                "execution_time_ms": execution_time_ms
            }

        return {
            "search_entities": record["search_entities_found"] or [],
            "search_chunks": record["search_chunks_data"] or [],
            "cooccurring_entities": record["cooccurring_entities"] or [],
            "relationships": record["entity_relationships"] or [],
            "expanded_chunks": record["expanded_chunks_data"] or [],
            "search_entities_count": len(record["search_entities_found"] or []),
            "expanded_entities_count": len(record["cooccurring_entities"] or []),
            "execution_time_ms": execution_time_ms
        }


def _score_and_rank_chunks(
    query_result: Dict[str, Any],
    search_term_entities: List[str]
) -> List[Dict]:
    """
    Score and rank chunks based on entity matches and relationships

    Scoring tiers:
    1.0 - Multiple search term entities in chunk
    0.8 - 1 search term + expanded entities in same document
    0.6 - Single search term entity
    0.4 - Expanded entities only
    """

    scored_chunks = []
    chunk_dedup = set()  # Deduplicate by vector_rowid

    # Process search term chunks (higher priority)
    for chunk in query_result.get("search_chunks", []):
        if not chunk or chunk.get("vector_rowid") is None:
            continue

        vector_rowid = chunk["vector_rowid"]
        if vector_rowid in chunk_dedup:
            continue
        chunk_dedup.add(vector_rowid)

        search_entities_in_chunk = chunk.get("search_entities", [])
        search_entity_count = len(search_entities_in_chunk)

        # Calculate base score
        if search_entity_count >= 2:
            base_score = 1.0  # Multiple search terms (highest priority)
        elif search_entity_count == 1:
            base_score = 0.6  # Single search term
        else:
            base_score = 0.4  # Fallback

        scored_chunks.append({
            "chunk_id": chunk.get("chunk_id", ""),
            "vector_rowid": vector_rowid,
            "chunk_index": chunk.get("chunk_index", 0),
            "chunk_text": chunk.get("text", "")[:500],  # Truncate for response
            "document_url": chunk.get("doc_url", ""),
            "expansion_score": base_score,
            "search_entity_count": search_entity_count,
            "expanded_entity_count": 0,
            "relationship_count": 0
        })

    # Process expanded chunks (lower priority)
    for chunk in query_result.get("expanded_chunks", []):
        if not chunk or chunk.get("vector_rowid") is None:
            continue

        vector_rowid = chunk["vector_rowid"]
        if vector_rowid in chunk_dedup:
            continue
        chunk_dedup.add(vector_rowid)

        expanded_entities_in_chunk = chunk.get("expanded_entities", [])
        expanded_entity_count = len(expanded_entities_in_chunk)

        # Calculate score for expansion-only chunks
        if expanded_entity_count > 3:
            base_score = 0.8  # Many co-occurring entities
        elif expanded_entity_count > 1:
            base_score = 0.6  # Some co-occurring entities
        else:
            base_score = 0.4  # Few co-occurring entities

        scored_chunks.append({
            "chunk_id": chunk.get("chunk_id", ""),
            "vector_rowid": vector_rowid,
            "chunk_index": chunk.get("chunk_index", 0),
            "chunk_text": chunk.get("text", "")[:500],
            "document_url": chunk.get("doc_url", ""),
            "expansion_score": base_score,
            "search_entity_count": 0,
            "expanded_entity_count": expanded_entity_count,
            "relationship_count": 0
        })

    # Sort by score (descending)
    scored_chunks.sort(key=lambda x: x["expansion_score"], reverse=True)

    return scored_chunks
