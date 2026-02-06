"""Main graph composition - ties all components together."""

from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from ro_tax_agents.state.base import BaseAgentState
from ro_tax_agents.orchestration.entry_agent import entry_agent_node, request_clarification_node
from ro_tax_agents.orchestration.router import route_to_domain_agent, route_after_domain_agent
from ro_tax_agents.agents import (
    pfa_agent_node,
    property_sale_agent_node,
    rental_income_agent_node,
    certificate_agent_node,
    efactura_agent_node,
)
from ro_tax_agents.services import rao_agent_service


def create_graph() -> StateGraph:
    """Create the main orchestration graph.

    This graph implements a hierarchical supervisor pattern where:
    1. Entry Agent analyzes user intent and routes to domain agents
    2. Domain agents handle specific tax-related tasks
    3. Shared services are available to all domain agents

    Returns:
        Configured StateGraph (not compiled)
    """
    # Initialize graph with base state
    builder = StateGraph(BaseAgentState)

    # Add Entry Agent (intent detection & routing)
    builder.add_node("entry_agent", entry_agent_node)

    # Add Domain Agent nodes
    builder.add_node("pfa_agent", pfa_agent_node)
    builder.add_node("property_sale_agent", property_sale_agent_node)
    builder.add_node("rental_income_agent", rental_income_agent_node)
    builder.add_node("certificate_agent", certificate_agent_node)
    builder.add_node("efactura_agent", efactura_agent_node)

    # Add RAO service as a node (for general tax questions)
    builder.add_node("rao_service", rao_agent_service)

    # Add clarification node
    builder.add_node("request_clarification", request_clarification_node)

    # Define edges
    # Start -> Entry Agent
    builder.add_edge(START, "entry_agent")

    # Entry Agent -> Domain Agents (conditional routing)
    builder.add_conditional_edges(
        "entry_agent",
        route_to_domain_agent,
        {
            "pfa_agent": "pfa_agent",
            "property_sale_agent": "property_sale_agent",
            "rental_income_agent": "rental_income_agent",
            "certificate_agent": "certificate_agent",
            "efactura_agent": "efactura_agent",
            "rao_service": "rao_service",
            "request_clarification": "request_clarification",
        },
    )

    # Domain agents -> End (they complete their workflow)
    builder.add_edge("pfa_agent", END)
    builder.add_edge("property_sale_agent", END)
    builder.add_edge("rental_income_agent", END)
    builder.add_edge("certificate_agent", END)
    builder.add_edge("efactura_agent", END)
    builder.add_edge("rao_service", END)

    # Clarification -> End (wait for user to provide more info)
    builder.add_edge("request_clarification", END)

    return builder


def compile_graph(checkpointer=None):
    """Compile the graph with optional checkpointing.

    Args:
        checkpointer: Optional checkpointer for state persistence.
                     If None, uses in-memory checkpointer.

    Returns:
        Compiled graph ready for invocation
    """
    builder = create_graph()

    if checkpointer is None:
        checkpointer = MemorySaver()

    return builder.compile(checkpointer=checkpointer)


def get_initial_state(session_id: str, user_id: str = None) -> BaseAgentState:
    """Create an initial state for a new conversation.

    Args:
        session_id: Unique session identifier
        user_id: Optional user identifier

    Returns:
        Initial state dictionary
    """
    return {
        "messages": [],
        "current_agent": None,
        "next_agent": None,
        "user_id": user_id,
        "session_id": session_id,
        "detected_intent": None,
        "intent_confidence": 0.0,
        "workflow_status": "pending",
        "error_message": None,
        "shared_context": {},
    }
