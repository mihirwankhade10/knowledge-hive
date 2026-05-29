"""
KnowledgeHive - Graph Agent

Extracts entities and relationships from document chunks using LLM,
then stores them in the Neo4j knowledge graph.
"""

import json
import logging
from typing import Optional

from backend.agents.base_agent import BaseAgent
from backend.services.llm_service import LLMProvider
from backend.services.neo4j_service import GraphStore
from backend.utils.prompts import ENTITY_EXTRACTION_PROMPT, RELATIONSHIP_EXTRACTION_PROMPT

logger = logging.getLogger(__name__)


class GraphAgent(BaseAgent):
    """
    Agent responsible for knowledge graph construction:
    Chunks → LLM Extract Entities → LLM Extract Relationships → Store in Neo4j
    """

    def __init__(self, llm_service: LLMProvider, graph_store: GraphStore):
        super().__init__(name="Graph Agent")
        self.llm_service = llm_service
        self.graph_store = graph_store

    async def _run(self, context: dict) -> dict:
        """
        Run the graph extraction pipeline.

        Context requires:
            - document_id: str
            - chunks: list[dict] with 'content' field
        """
        document_id = context["document_id"]
        chunks = context.get("chunks", [])

        if not chunks:
            return {"entity_count": 0, "relationship_count": 0}

        # Initialize graph store
        await self.graph_store.initialize()

        # Combine chunk content for entity extraction
        # Process in batches to stay within LLM context limits
        combined_text = "\n\n".join(
            c.get("content", "") for c in chunks[:10]  # Limit to first 10 chunks
        )

        # Step 1: Extract entities
        logger.info(f"[Graph] Extracting entities from {len(chunks)} chunks")
        entities = await self._extract_entities(combined_text)

        # Step 2: Store entities
        entity_count = await self.graph_store.store_entities(document_id, entities)

        # Step 3: Extract relationships
        relationship_count = 0
        if entities:
            logger.info(f"[Graph] Extracting relationships from {len(entities)} entities")
            relationships = await self._extract_relationships(entities, combined_text)
            relationship_count = await self.graph_store.store_relationships(relationships)

        return {
            "document_id": document_id,
            "entity_count": entity_count,
            "relationship_count": relationship_count,
            "entities": [e.get("name", "") for e in entities[:10]],
        }

    async def _extract_entities(self, text: str) -> list[dict]:
        """Use LLM to extract entities from text."""
        prompt = ENTITY_EXTRACTION_PROMPT.format(text=text[:4000])

        try:
            response = await self.llm_service.generate(
                prompt=prompt,
                system_prompt="You are a precise entity extraction system. Respond only with valid JSON.",
                temperature=0.1,
            )
            return self._parse_json_response(response)
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return []

    async def _extract_relationships(
        self, entities: list[dict], text: str
    ) -> list[dict]:
        """Use LLM to extract relationships between entities."""
        entity_names = json.dumps([e.get("name", "") for e in entities])
        prompt = RELATIONSHIP_EXTRACTION_PROMPT.format(
            entities=entity_names, text=text[:4000]
        )

        try:
            response = await self.llm_service.generate(
                prompt=prompt,
                system_prompt="You are a precise relationship extraction system. Respond only with valid JSON.",
                temperature=0.1,
            )
            return self._parse_json_response(response)
        except Exception as e:
            logger.error(f"Relationship extraction failed: {e}")
            return []

    def _parse_json_response(self, response: str) -> list[dict]:
        """Parse JSON from LLM response, handling markdown code blocks."""
        text = response.strip()

        # Strip markdown code blocks if present
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if len(lines) > 2 else text

        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return parsed
            return []
        except json.JSONDecodeError:
            # Try to find JSON array in the response
            start = text.find("[")
            end = text.rfind("]")
            if start != -1 and end != -1:
                try:
                    return json.loads(text[start : end + 1])
                except json.JSONDecodeError:
                    pass
            logger.warning(f"Could not parse JSON from LLM response: {text[:200]}")
            return []

    def _summarize(self, output: dict) -> str:
        return (
            f"Extracted {output.get('entity_count', 0)} entities, "
            f"{output.get('relationship_count', 0)} relationships"
        )
