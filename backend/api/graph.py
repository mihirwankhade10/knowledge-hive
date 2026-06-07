"""
KnowledgeHive - Graph API

Provides graph visualization data from Neo4j for the Knowledge Graph page.
"""

import logging

from fastapi import APIRouter, Request

from backend.core.rate_limit import limiter
from backend.core.dependencies import get_graph_store

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/graph/data")
@limiter.limit("30/minute")
async def get_graph_data(request: Request):
    """
    Fetch graph nodes and edges from Neo4j for visualization.
    Returns entities as nodes and relationships as edges.
    """
    try:
        graph_store = get_graph_store()
        driver = await graph_store._get_driver()

        nodes = []
        edges = []

        async with driver.session() as session:
            # Fetch all entities (nodes)
            node_result = await session.run(
                """
                MATCH (e:Entity)
                RETURN e.name AS name, e.type AS type, e.description AS description
                LIMIT 100
                """
            )
            async for record in node_result:
                nodes.append({
                    "id": record["name"],
                    "label": record["name"],
                    "type": (record["type"] or "concept").lower(),
                    "description": record["description"] or "",
                })

            # Fetch all relationships (edges)
            edge_result = await session.run(
                """
                MATCH (a:Entity)-[r]->(b:Entity)
                RETURN a.name AS source, b.name AS target,
                       type(r) AS relationship, r.description AS description
                LIMIT 200
                """
            )
            async for record in edge_result:
                edges.append({
                    "source": record["source"],
                    "target": record["target"],
                    "label": (record["relationship"] or "relates_to").lower().replace("_", " "),
                    "description": record["description"] or "",
                })

        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
            },
        }

    except Exception as e:
        logger.error(f"Failed to fetch graph data: {e}")
        return {
            "nodes": [],
            "edges": [],
            "stats": {"total_nodes": 0, "total_edges": 0},
            "error": str(e),
        }


@router.get("/graph/stats")
@limiter.limit("30/minute")
async def get_graph_stats(request: Request):
    """Get graph statistics from Neo4j."""
    try:
        graph_store = get_graph_store()
        stats = await graph_store.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get graph stats: {e}")
        return {"entity_count": 0, "relationship_count": 0, "document_count": 0}
