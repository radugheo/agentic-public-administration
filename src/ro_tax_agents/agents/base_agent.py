"""Base agent class for domain agents."""

from abc import ABC, abstractmethod
from typing import Any

from ro_tax_agents.state.base import BaseAgentState


class BaseDomainAgent(ABC):
    """Abstract base class for domain agents.

    All domain agents inherit from this class and implement
    the process method for their specific domain logic.
    """

    @abstractmethod
    def process(self, state: BaseAgentState) -> dict[str, Any]:
        """Process the agent's domain-specific logic.

        Args:
            state: Current agent state

        Returns:
            State updates
        """
        pass

    def __call__(self, state: BaseAgentState) -> dict[str, Any]:
        """Make the agent callable as a LangGraph node."""
        return self.process(state)
