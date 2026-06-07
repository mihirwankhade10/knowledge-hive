"""
KnowledgeHive - Response Agent

Generates the final answer with citations using validated context.
The last agent in the query pipeline.
"""

import logging

from backend.agents.base_agent import BaseAgent
from backend.services.llm_service import LLMProvider
from backend.utils.prompts import ANSWER_GENERATION_PROMPT

logger = logging.getLogger(__name__)


class ResponseAgent(BaseAgent):
    """
    Agent responsible for answer generation:
    Validated Context + Question → LLM Answer → Citations + Sources
    """

    def __init__(self, llm_service: LLMProvider):
        super().__init__(name="Response Agent")
        self.llm_service = llm_service

    async def _run(self, context: dict) -> dict:
        """
        Run the response generation pipeline.

        Context requires:
            - question: str
            - validated_chunks: list[dict]
            - confidence: float
            - graph_context: str
        """
        question = context["question"]
        validated_chunks = context.get("validated_chunks", [])
        confidence = context.get("confidence", 0.0)
        graph_context = context.get("graph_context", "No graph context available.")

        if not validated_chunks:
            return {
                "answer": "I don't have enough information to answer this question. "
                "Please upload relevant documents first.",
                "sources": [],
                "confidence": 0.0,
            }

        try:
            # Format context for the LLM
            context_text = "\n\n".join(
                f"[Source {i+1} - {c.get('filename', 'unknown')}]:\n{c.get('content', '')}"
                for i, c in enumerate(validated_chunks)
            )

            # Generate answer
            logger.info(f"[Response] Generating answer for: {question[:80]}...")
            prompt = ANSWER_GENERATION_PROMPT.format(
                context=context_text,
                graph_context=graph_context,
                question=question,
            )

            answer = await self.llm_service.generate(
                prompt=prompt,
                system_prompt=(
                    "You are KnowledgeHive, an enterprise knowledge assistant. "
                    "Provide accurate, well-cited answers based on the provided context."
                ),
                temperature=0.3,
                max_tokens=2000,
            )

            # Build source references
            sources = [
                {
                    "document_name": c.get("filename", "unknown"),
                    "chunk_text": c.get("content", "")[:300],
                    "relevance_score": c.get("relevance_score", 0.0),
                }
                for c in validated_chunks
            ]

            return {
                "answer": answer.strip() if answer else "Unable to generate an answer.",
                "sources": sources,
                "confidence": confidence,
            }
        except Exception as e:
            logger.error(f"[Response] Answer generation failed: {e}")
            # Return a response with available sources even if answer generation fails
            sources = [
                {
                    "document_name": c.get("filename", "unknown"),
                    "chunk_text": c.get("content", "")[:300],
                    "relevance_score": c.get("relevance_score", 0.0),
                }
                for c in validated_chunks
            ]
            return {
                "answer": f"I found relevant information but encountered an error while generating the response. Please try again. (Error: {str(e)[:100]})",
                "sources": sources,
                "confidence": 0.0,
            }

    def _summarize(self, output: dict) -> str:
        answer_preview = output.get("answer", "")[:80]
        return (
            f"Generated answer ({len(output.get('sources', []))} sources, "
            f"confidence: {output.get('confidence', 0.0):.1%}): {answer_preview}..."
        )
