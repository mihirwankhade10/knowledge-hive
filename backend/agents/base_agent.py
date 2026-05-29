"""
KnowledgeHive - Base Agent

Abstract base class for all agents in the swarm.
Provides timing, error handling, and status tracking.
Designed for easy migration to AutoGen in Phase 2.
"""

import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

from backend.models.query import AgentStatus

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    """Result of an agent execution."""

    status: AgentStatus = AgentStatus.COMPLETED
    output: dict = field(default_factory=dict)
    duration_ms: float = 0.0
    error: Optional[str] = None
    output_summary: str = ""


class BaseAgent(ABC):
    """
    Abstract base class for KnowledgeHive agents.

    All agents follow the same lifecycle:
    1. execute() is called with a context dict
    2. The agent performs its work via _run()
    3. Timing, status, and errors are handled automatically
    4. An AgentResult is returned

    Subclasses only need to implement _run().
    """

    def __init__(self, name: str):
        self.name = name

    async def execute(self, context: dict) -> AgentResult:
        """
        Execute the agent with automatic timing and error handling.

        Args:
            context: Dictionary of inputs for the agent.

        Returns:
            AgentResult with status, output, and timing.
        """
        logger.info(f"[{self.name}] Starting execution")
        start_time = time.time()

        try:
            output = await self._run(context)
            duration = (time.time() - start_time) * 1000

            result = AgentResult(
                status=AgentStatus.COMPLETED,
                output=output,
                duration_ms=round(duration, 2),
                output_summary=self._summarize(output),
            )
            logger.info(
                f"[{self.name}] Completed in {result.duration_ms}ms"
            )
            return result

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error(f"[{self.name}] Failed: {e}")
            return AgentResult(
                status=AgentStatus.FAILED,
                output={},
                duration_ms=round(duration, 2),
                error=str(e),
                output_summary=f"Failed: {str(e)[:100]}",
            )

    @abstractmethod
    async def _run(self, context: dict) -> dict:
        """
        Core agent logic. Implement in subclasses.

        Args:
            context: Dictionary of inputs.

        Returns:
            Dictionary of outputs.
        """
        ...

    def _summarize(self, output: dict) -> str:
        """Generate a human-readable summary of the output. Override in subclasses."""
        return f"{self.name} completed"
