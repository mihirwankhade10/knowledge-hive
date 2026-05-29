"""
KnowledgeHive - Validation Agent

Validates retrieved evidence, scores confidence, and ranks sources.
Uses LLM to assess relevance of retrieved chunks to the question.
"""

import json
import logging

from backend.agents.base_agent import BaseAgent
from backend.services.llm_service import LLMProvider
from backend.utils.prompts import VALIDATION_PROMPT

logger = logging.getLogger(__name__)


class ValidationAgent(BaseAgent):
    """
    Agent responsible for evidence validation:
    Retrieved Chunks + Question → LLM Score → Ranked Sources + Confidence
    """

    def __init__(self, llm_service: LLMProvider):
        super().__init__(name="Validation Agent")
        self.llm_service = llm_service

    async def _run(self, context: dict) -> dict:
        """
        Run the validation pipeline.

        Context requires:
            - question: str
            - chunks: list[dict] with 'content', 'filename', 'score' fields
            - graph_context: str
        """
        question = context["question"]
        chunks = context.get("chunks", [])
        graph_context = context.get("graph_context", "")

        if not chunks:
            return {
                "validated_chunks": [],
                "confidence": 0.0,
                "reasoning": "No chunks to validate",
            }

        # Format context for validation
        context_text = "\n\n".join(
            f"[Source {i+1} - {c.get('filename', 'unknown')}]: {c.get('content', '')}"
            for i, c in enumerate(chunks)
        )

        # Use LLM to validate
        logger.info(f"[Validation] Validating {len(chunks)} chunks")
        validation = await self._validate_with_llm(question, context_text)

        # Apply relevance scores to chunks
        relevance_scores = validation.get("relevance_scores", [])
        overall_confidence = validation.get("overall_confidence", 0.5)
        reasoning = validation.get("reasoning", "")

        validated_chunks = []
        for i, chunk in enumerate(chunks):
            llm_relevance = (
                relevance_scores[i] if i < len(relevance_scores) else 0.5
            )
            # Combine vector similarity score with LLM relevance
            vector_score = chunk.get("score", 0.5)
            combined_score = (vector_score + llm_relevance) / 2

            validated_chunks.append(
                {
                    **chunk,
                    "relevance_score": round(combined_score, 3),
                    "llm_relevance": llm_relevance,
                }
            )

        # Sort by relevance
        validated_chunks.sort(key=lambda x: x["relevance_score"], reverse=True)

        return {
            "validated_chunks": validated_chunks,
            "confidence": round(overall_confidence, 3),
            "reasoning": reasoning,
            "graph_context": graph_context,
        }

    async def _validate_with_llm(
        self, question: str, context: str
    ) -> dict:
        """Use LLM to validate retrieved context."""
        prompt = VALIDATION_PROMPT.format(question=question, context=context)

        try:
            response = await self.llm_service.generate(
                prompt=prompt,
                system_prompt="You are a precise fact-checking system. Respond only with valid JSON.",
                temperature=0.1,
            )
            return self._parse_validation_response(response)
        except Exception as e:
            logger.error(f"Validation LLM call failed: {e}")
            return {
                "relevance_scores": [],
                "overall_confidence": 0.5,
                "reasoning": f"Validation skipped due to error: {str(e)[:100]}",
            }

    def _parse_validation_response(self, response: str) -> dict:
        """Parse the validation JSON response from LLM."""
        text = response.strip()

        # Strip markdown code blocks
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if len(lines) > 2 else text

        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            # Try to extract JSON object
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                try:
                    return json.loads(text[start : end + 1])
                except json.JSONDecodeError:
                    pass

        logger.warning(f"Could not parse validation response: {text[:200]}")
        return {
            "relevance_scores": [],
            "overall_confidence": 0.5,
            "reasoning": "Could not parse validation response",
        }

    def _summarize(self, output: dict) -> str:
        return (
            f"Validated {len(output.get('validated_chunks', []))} chunks, "
            f"confidence: {output.get('confidence', 0.0):.1%}"
        )
