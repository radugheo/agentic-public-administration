"""Base state definitions for the agent system."""

from typing import TypedDict, Annotated, Literal, Optional, Any
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class BaseAgentState(TypedDict):
    """Base state shared across all agents in the system.

    This state is used by the main orchestration graph and contains
    fields needed for routing and cross-agent communication.
    """

    # Conversation history - uses add_messages reducer for proper aggregation
    messages: Annotated[list[BaseMessage], add_messages]

    # Routing control
    current_agent: Optional[str]  # Currently active agent
    next_agent: Optional[str]  # Next agent to route to

    # User context
    user_id: Optional[str]
    session_id: str

    # Intent classification results from Entry Agent
    detected_intent: Optional[str]
    intent_confidence: float

    # Workflow tracking
    workflow_status: Literal["pending", "in_progress", "completed", "error"]
    error_message: Optional[str]

    # Shared data store for cross-agent communication
    shared_context: dict[str, Any]
