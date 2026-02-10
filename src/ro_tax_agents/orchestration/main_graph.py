"""Main graph composition - ties all components together."""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from ro_tax_agents.state.base import BaseAgentState, GraphInput, GraphOutput
from ro_tax_agents.orchestration.entry_agent import entry_agent_node, request_clarification_node
from ro_tax_agents.orchestration.router import route_to_domain_agent
from ro_tax_agents.agents import (
    pfa_agent_node,
    property_sale_agent_node,
    rental_income_agent_node,
    certificate_agent_node,
    efactura_agent_node,
)
from ro_tax_agents.services import rag_agent_service


def _set_response(node_fn):
    """Wrap a terminal node to auto-populate response from its output messages."""
    def wrapper(state):
        result = node_fn(state)
        if "messages" in result:
            for msg in reversed(result["messages"]):
                if hasattr(msg, "content"):
                    result["response"] = msg.content
                    break
        return result
    return wrapper


def create_graph() -> StateGraph:
    """Create the main orchestration graph.

    This graph implements a hierarchical supervisor pattern where:
    1. Entry Agent analyzes user intent and routes to domain agents
    2. Domain agents handle specific tax-related tasks
    3. Shared services are available to all domain agents

    Returns:
        Configured StateGraph (not compiled)
    """
    builder = StateGraph(BaseAgentState, input_schema=GraphInput, output_schema=GraphOutput)

    # Entry Agent (reads state["query"] directly, populates messages)
    builder.add_node("entry_agent", entry_agent_node)

    # Domain Agent nodes (wrapped to auto-set response)
    builder.add_node("pfa_agent", _set_response(pfa_agent_node))
    builder.add_node("property_sale_agent", _set_response(property_sale_agent_node))
    builder.add_node("rental_income_agent", _set_response(rental_income_agent_node))
    builder.add_node("certificate_agent", _set_response(certificate_agent_node))
    builder.add_node("efactura_agent", _set_response(efactura_agent_node))

    # RAG agent (for general tax questions)
    builder.add_node("rag_agent", _set_response(rag_agent_service))

    # Clarification node
    builder.add_node("request_clarification", _set_response(request_clarification_node))

    # Edges
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
            "rag_agent": "rag_agent",
            "request_clarification": "request_clarification",
        },
    )

    # Domain agents -> End
    builder.add_edge("pfa_agent", END)
    builder.add_edge("property_sale_agent", END)
    builder.add_edge("rental_income_agent", END)
    builder.add_edge("certificate_agent", END)
    builder.add_edge("efactura_agent", END)
    builder.add_edge("rag_agent", END)
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


# Module-level compiled graph for UiPath deployment
graph = compile_graph()


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
