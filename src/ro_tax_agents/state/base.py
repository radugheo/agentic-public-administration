"""Base state definitions for the agent system."""

from typing import Annotated, Literal, Optional, Any
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class GraphInput(TypedDict):
    """Input schema - what the user provides."""
    query: str


class GraphOutput(TypedDict):
    """Output schema - what the user receives."""
    response: str
    detected_intent: Optional[str]
    intent_confidence: float
    workflow_status: Literal["pending", "in_progress", "completed", "error"]


class BaseAgentState(TypedDict):
    """Full internal state shared across all agents in the system.

    Includes all fields from GraphInput and GraphOutput plus
    internal routing and communication fields.
    """

    # --- Input ---
    query: str

    # --- Output ---
    response: str

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
