"""
KnowledgeHive - Neo4j Graph Store Service

Abstracted graph store with Neo4j implementation.
Handles entity/relationship storage and subgraph queries.
"""

import logging
from typing import Protocol, Optional

from neo4j import AsyncGraphDatabase, AsyncDriver

logger = logging.getLogger(__name__)


class GraphStore(Protocol):
    """Protocol for graph store providers."""

    async def initialize(self) -> None:
        """Initialize the graph store (create constraints, indexes)."""
        ...

    async def store_entities(
        self, document_id: str, entities: list[dict]
    ) -> int:
        """Store extracted entities. Returns count stored."""
        ...

    async def store_relationships(
        self, relationships: list[dict]
    ) -> int:
        """Store relationships between entities. Returns count stored."""
        ...

    async def query_related(
        self, entity_names: list[str], max_depth: int = 2
    ) -> list[dict]:
        """Query for entities related to the given names."""
        ...

    async def get_stats(self) -> dict:
        """Get graph statistics."""
        ...


class Neo4jGraphStore:
    """Graph store implementation using Neo4j."""

    def __init__(self, uri: str, user: str, password: str):
        self.uri = uri
        self.user = user
        self.password = password
        self._driver: Optional[AsyncDriver] = None

    async def _get_driver(self) -> AsyncDriver:
        if self._driver is None:
            self._driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
            )
        return self._driver

    async def initialize(self) -> None:
        """Create constraints and indexes for the knowledge graph."""
        driver = await self._get_driver()
        async with driver.session() as session:
            # Create constraint on Entity name for uniqueness
            await session.run(
                "CREATE CONSTRAINT entity_name IF NOT EXISTS "
                "FOR (e:Entity) REQUIRE e.name IS UNIQUE"
            )
            # Create index on Document
            await session.run(
                "CREATE INDEX document_id IF NOT EXISTS "
                "FOR (d:Document) ON (d.document_id)"
            )
            logger.info("Neo4j constraints and indexes created")

    async def store_entities(
        self, document_id: str, entities: list[dict]
    ) -> int:
        """
        Store entities as graph nodes.

        Each entity dict should have: name, type, description
        """
        if not entities:
            return 0

        driver = await self._get_driver()
        count = 0

        async with driver.session() as session:
            # Ensure document node exists
            await session.run(
                "MERGE (d:Document {document_id: $doc_id})",
                doc_id=document_id,
            )

            for entity in entities:
                try:
                    result = await session.run(
                        """
                        MERGE (e:Entity {name: $name})
                        ON CREATE SET e.type = $type,
                                      e.description = $description,
                                      e.created_at = datetime()
                        ON MATCH SET e.description = CASE
                            WHEN e.description IS NULL THEN $description
                            ELSE e.description
                        END
                        WITH e
                        MATCH (d:Document {document_id: $doc_id})
                        MERGE (d)-[:MENTIONS]->(e)
                        RETURN e.name AS name
                        """,
                        name=entity.get("name", ""),
                        type=entity.get("type", "CONCEPT"),
                        description=entity.get("description", ""),
                        doc_id=document_id,
                    )
                    records = [r async for r in result]
                    if records:
                        count += 1
                except Exception as e:
                    logger.warning(f"Failed to store entity {entity}: {e}")

        logger.info(f"Stored {count} entities in Neo4j for document {document_id}")
        return count

    async def store_relationships(self, relationships: list[dict]) -> int:
        """
        Store relationships between entities.

        Each relationship dict should have: source, target, relationship, description
        """
        if not relationships:
            return 0

        driver = await self._get_driver()
        count = 0

        async with driver.session() as session:
            for rel in relationships:
                try:
                    rel_type = rel.get("relationship", "RELATES_TO").upper()
                    # Sanitize relationship type for Cypher
                    rel_type = "".join(
                        c if c.isalnum() or c == "_" else "_" for c in rel_type
                    )

                    await session.run(
                        f"""
                        MATCH (source:Entity {{name: $source}})
                        MATCH (target:Entity {{name: $target}})
                        MERGE (source)-[r:{rel_type}]->(target)
                        ON CREATE SET r.description = $description,
                                      r.created_at = datetime()
                        """,
                        source=rel.get("source", ""),
                        target=rel.get("target", ""),
                        description=rel.get("description", ""),
                    )
                    count += 1
                except Exception as e:
                    logger.warning(f"Failed to store relationship {rel}: {e}")

        logger.info(f"Stored {count} relationships in Neo4j")
        return count

    async def query_related(
        self, entity_names: list[str], max_depth: int = 2
    ) -> list[dict]:
        """Query for entities and relationships related to the given names."""
        if not entity_names:
            return []

        driver = await self._get_driver()
        results = []

        async with driver.session() as session:
            result = await session.run(
                """
                UNWIND $names AS name
                MATCH (e:Entity)
                WHERE toLower(e.name) CONTAINS toLower(name)
                OPTIONAL MATCH path = (e)-[r*1..2]-(related:Entity)
                WITH e, related, r
                RETURN DISTINCT
                    e.name AS entity,
                    e.type AS entity_type,
                    e.description AS entity_description,
                    related.name AS related_entity,
                    related.type AS related_type,
                    related.description AS related_description
                LIMIT 20
                """,
                names=entity_names,
            )

            async for record in result:
                entry = {
                    "entity": record["entity"],
                    "entity_type": record["entity_type"],
                    "entity_description": record["entity_description"],
                }
                if record["related_entity"]:
                    entry["related_entity"] = record["related_entity"]
                    entry["related_type"] = record["related_type"]
                    entry["related_description"] = record["related_description"]
                results.append(entry)

        return results

    async def get_stats(self) -> dict:
        """Get graph statistics (node and relationship counts)."""
        try:
            driver = await self._get_driver()
            async with driver.session() as session:
                node_result = await session.run(
                    "MATCH (e:Entity) RETURN count(e) AS count"
                )
                node_record = await node_result.single()
                entity_count = node_record["count"] if node_record else 0

                rel_result = await session.run(
                    "MATCH ()-[r]->() RETURN count(r) AS count"
                )
                rel_record = await rel_result.single()
                rel_count = rel_record["count"] if rel_record else 0

                doc_result = await session.run(
                    "MATCH (d:Document) RETURN count(d) AS count"
                )
                doc_record = await doc_result.single()
                doc_count = doc_record["count"] if doc_record else 0

                return {
                    "entity_count": entity_count,
                    "relationship_count": rel_count,
                    "document_count": doc_count,
                }
        except Exception as e:
            logger.error(f"Failed to get Neo4j stats: {e}")
            return {"entity_count": 0, "relationship_count": 0, "document_count": 0}

    async def close(self):
        """Close the driver."""
        if self._driver:
            await self._driver.close()
            self._driver = None
