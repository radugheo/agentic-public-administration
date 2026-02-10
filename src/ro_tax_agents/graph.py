"""Main graph composition - ties all agents together."""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from ro_tax_agents.state.base import BaseAgentState, GraphInput, GraphOutput
from ro_tax_agents.agents import (
    entry_node,
    route_after_entry,
    clarification_node,
    pfa_node,
    property_sale_node,
    rental_income_node,
    certificate_node,
    efactura_node,
    rag_node,
)


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

    # Entry node (reads state["query"] directly, populates messages)
    builder.add_node("entry", entry_node)

    # Domain agent nodes (wrapped to auto-set response)
    builder.add_node("pfa", _set_response(pfa_node))
    builder.add_node("property_sale", _set_response(property_sale_node))
    builder.add_node("rental_income", _set_response(rental_income_node))
    builder.add_node("certificate", _set_response(certificate_node))
    builder.add_node("efactura", _set_response(efactura_node))

    # RAG agent (for general tax questions)
    builder.add_node("rag", _set_response(rag_node))

    # Clarification node
    builder.add_node("clarification", _set_response(clarification_node))

    # Edges
    builder.add_edge(START, "entry")

    # Entry -> Domain agents (conditional routing)
    builder.add_conditional_edges(
        "entry",
        route_after_entry,
        {
            "pfa": "pfa",
            "property_sale": "property_sale",
            "rental_income": "rental_income",
            "certificate": "certificate",
            "efactura": "efactura",
            "rag": "rag",
            "clarification": "clarification",
        },
    )

    # All terminal nodes -> End
    builder.add_edge("pfa", END)
    builder.add_edge("property_sale", END)
    builder.add_edge("rental_income", END)
    builder.add_edge("certificate", END)
    builder.add_edge("efactura", END)
    builder.add_edge("rag", END)
    builder.add_edge("clarification", END)

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


def get_initial_state(session_id: str, user_id: str = None) -> BaseAgentState: # type: ignore
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
    } # type: ignore
