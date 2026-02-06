"""Property Sale Agent - Tax calculation for property sales."""

from typing import Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage

from ro_tax_agents.state.base import BaseAgentState
from ro_tax_agents.config.prompts import PROPERTY_SALE_AGENT_SYSTEM_PROMPT
from ro_tax_agents.config.settings import settings
from ro_tax_agents.services import calculation_agent_service


class PropertySaleAgent:
    """Property Sale agent for calculating property sale taxes.

    Tax rates:
    - 3% if property owned less than 3 years
    - 1% if property owned 3 years or more
    """

    def __init__(self):
        self._llm = None

    @property
    def llm(self):
        """Lazy initialization of the LLM."""
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=settings.openai_model,
                temperature=0,
                api_key=settings.openai_api_key or None,
            )
        return self._llm

    def process(self, state: BaseAgentState) -> dict[str, Any]:
        """Process property sale tax calculation requests.

        Args:
            state: Current agent state

        Returns:
            State updates with tax calculation or guidance
        """
        shared_context = state.get("shared_context", {})
        extracted_entities = shared_context.get("extracted_entities", {})

        # Check if we have the necessary information
        property_value = extracted_entities.get("property_value") or shared_context.get("property_value")
        ownership_years = extracted_entities.get("ownership_years") or shared_context.get("ownership_duration_years")

        if property_value is not None and ownership_years is not None:
            # We have all data - calculate tax
            return self._calculate_tax(state, float(property_value), int(ownership_years))
        else:
            # Need more information
            return self._request_information(state, property_value, ownership_years)

    def _calculate_tax(self, state: BaseAgentState, property_value: float, ownership_years: int) -> dict[str, Any]:
        """Calculate property sale tax.

        Args:
            state: Current agent state
            property_value: Property sale value in RON
            ownership_years: Years of property ownership

        Returns:
            State updates with calculation results
        """
        shared_context = state.get("shared_context", {})

        # Update shared context
        updated_context = {
            **shared_context,
            "property_value": property_value,
            "ownership_duration_years": ownership_years,
            "calculation_type": "property_sale_tax",
        }

        # Create updated state for calculation service
        calc_state = {**state, "shared_context": updated_context}

        # Call calculation service
        calc_result = calculation_agent_service.process(calc_state)

        # Get calculation results
        calculated_tax = calc_result["shared_context"].get("calculated_tax", 0)
        tax_rate = calc_result["shared_context"].get("tax_rate", 0)

        # Use LLM to present the results
        context_message = (
            f"Tax calculation completed. Present these results to the user:\n"
            f"- Property value: {property_value:,.2f} RON\n"
            f"- Ownership duration: {ownership_years} years\n"
            f"- Applied tax rate: {tax_rate}%\n"
            f"- Calculated tax: {calculated_tax:,.2f} RON\n"
            f"Explain the payment options (Ghiseul.ro online or Treasury) and offer to help with payment."
        )

        response = self.llm.invoke([
            SystemMessage(content=PROPERTY_SALE_AGENT_SYSTEM_PROMPT),
            *state["messages"],
            SystemMessage(content=context_message),
        ])

        return {
            "messages": [response],
            "shared_context": calc_result["shared_context"],
            "current_agent": "property_sale_agent",
            "workflow_status": "in_progress",
        }

    def _request_information(
        self, state: BaseAgentState, property_value: Any, ownership_years: Any
    ) -> dict[str, Any]:
        """Request missing information for tax calculation using LLM.

        Args:
            state: Current agent state
            property_value: Property value if known
            ownership_years: Ownership years if known

        Returns:
            State updates with information request
        """
        shared_context = state.get("shared_context", {})

        # Build context about what we know and what we need
        context_parts = ["Current information and tax rules:"]
        context_parts.append("- Tax rate is 1% if property owned >= 3 years")
        context_parts.append("- Tax rate is 3% if property owned < 3 years")

        if property_value is not None:
            context_parts.append(f"- Property value provided: {property_value:,.2f} RON")
        else:
            context_parts.append("- MISSING: Property sale value (in RON)")

        if ownership_years is not None:
            context_parts.append(f"- Ownership duration provided: {ownership_years} years")
        else:
            context_parts.append("- MISSING: Ownership duration (in years)")

        context_parts.append("Ask the user for the missing information to calculate the tax.")

        response = self.llm.invoke([
            SystemMessage(content=PROPERTY_SALE_AGENT_SYSTEM_PROMPT),
            SystemMessage(content="\n".join(context_parts)),
            *state["messages"],
        ])

        return {
            "messages": [response],
            "current_agent": "property_sale_agent",
            "shared_context": {
                **shared_context,
                "awaiting_property_data": True,
                "property_value": property_value,
                "ownership_duration_years": ownership_years,
            },
            "workflow_status": "in_progress",
        }


# Create singleton instance
_property_sale_agent = PropertySaleAgent()


def property_sale_agent_node(state: BaseAgentState) -> dict[str, Any]:
    """LangGraph node function for Property Sale agent."""
    return _property_sale_agent.process(state)
