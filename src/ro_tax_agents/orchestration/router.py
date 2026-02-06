"""Router logic for conditional edges."""

from ro_tax_agents.state.base import BaseAgentState
from ro_tax_agents.config.settings import settings

# Mapping of intents to domain agents
INTENT_TO_AGENT = {
    "pfa_d212_filing": "pfa",
    "pfa_cas_cass": "pfa",
    "property_sale_tax": "property_sale",
    "rental_contract_registration": "rental_income",
    "fiscal_certificate": "certificate",
    "efactura_b2b": "efactura",
    "efactura_b2c": "efactura",
    "general_question": "rao",
    "unclear": "clarify",
}


def route_to_domain_agent(state: BaseAgentState) -> str:
    """Routing function for conditional edges from entry agent.

    Determines which domain agent should handle the request based on
    the detected intent and confidence level.

    Args:
        state: Current agent state

    Returns:
        Name of the next node to route to
    """
    confidence = state.get("intent_confidence", 0.0)
    next_agent = state.get("next_agent", "clarify")

    # If confidence is too low, ask for clarification
    if confidence < settings.intent_confidence_threshold:
        return "request_clarification"

    # Map agent names to node names
    agent_to_node = {
        "pfa": "pfa_agent",
        "property_sale": "property_sale_agent",
        "rental_income": "rental_income_agent",
        "certificate": "certificate_agent",
        "efactura": "efactura_agent",
        "rao": "rao_service",
        "clarify": "request_clarification",
    }

    return agent_to_node.get(next_agent, "request_clarification")


def route_after_domain_agent(state: BaseAgentState) -> str:
    """Route after a domain agent completes.

    Determines whether to return to entry agent, end, or continue.

    Args:
        state: Current agent state

    Returns:
        Name of the next node
    """
    workflow_status = state.get("workflow_status", "in_progress")
    next_agent = state.get("next_agent")

    if workflow_status == "completed":
        return "end"
    elif workflow_status == "error":
        return "end"
    elif next_agent == "entry":
        return "entry_agent"
    else:
        return "end"
