"""Rental Income Agent - Contract registration and rental tax."""

from typing import Any
from langchain_core.messages import SystemMessage

from ro_tax_agents.state.base import BaseAgentState
from ro_tax_agents.config.prompts import RENTAL_INCOME_AGENT_SYSTEM_PROMPT
from ro_tax_agents.services import calculation_service
from ro_tax_agents.mocks.tools import mock_spv_register_contract
from ro_tax_agents.agents._base import RAGEnabledAgentMixin


class RentalIncomeAgent(RAGEnabledAgentMixin):
    """Rental Income agent for contract registration and tax calculation.

    This agent handles:
    - Rental contract registration with ANAF
    - Rental income tax calculation (10%)
    - Landlord tax obligation guidance

    Uses RAG to ground responses in actual tax code knowledge.
    """

    RAG_AGENT_TYPE = "rental_income"

    def process(self, state: BaseAgentState) -> dict[str, Any]:
        """Process rental income related requests.

        Args:
            state: Current agent state

        Returns:
            State updates with rental guidance or calculations
        """
        shared_context = state.get("shared_context", {})
        extracted_entities = shared_context.get("extracted_entities", {})

        # Check if we have monthly rent to calculate tax
        monthly_rent = extracted_entities.get("monthly_rent") or shared_context.get("monthly_rent")

        if monthly_rent:
            return self._calculate_rental_tax(state, float(monthly_rent))
        else:
            return self._provide_guidance(state)

    def _calculate_rental_tax(self, state: BaseAgentState, monthly_rent: float) -> dict[str, Any]:
        """Calculate rental income tax.

        Args:
            state: Current agent state
            monthly_rent: Monthly rent in RON

        Returns:
            State updates with tax calculation
        """
        shared_context = state.get("shared_context", {})

        # Update context for calculation
        updated_context = {
            **shared_context,
            "monthly_rent": monthly_rent,
            "calculation_type": "rental_income_tax",
        }

        calc_state = {**state, "shared_context": updated_context}
        calc_result = calculation_service.process(calc_state)

        # Get calculation results
        rental_tax = calc_result["shared_context"].get("rental_tax", 0)
        annual_rental_income = calc_result["shared_context"].get("annual_rental_income", 0)

        # Use LLM to present the results, grounded in RAG knowledge
        rag_context = self._get_rag_context(state)
        context_message = (
            f"Rental tax calculation completed. Present these results to the user:\n"
            f"- Monthly rent: {monthly_rent:,.2f} RON\n"
            f"- Annual rental income: {annual_rental_income:,.2f} RON\n"
            f"- Annual rental tax (10%): {rental_tax:,.2f} RON\n"
            f"Explain the next steps: register the contract with ANAF via SPV, declare income in annual declaration, pay the tax. "
            f"Offer to help with contract registration."
        )

        messages = [SystemMessage(content=RENTAL_INCOME_AGENT_SYSTEM_PROMPT)]
        if rag_context:
            messages.append(SystemMessage(content=f"Relevant tax code knowledge:\n{rag_context}"))
        messages.extend(state["messages"])
        messages.append(SystemMessage(content=context_message))

        response = self.llm.invoke(messages)

        return {
            "messages": [response],
            "shared_context": calc_result["shared_context"],
            "current_agent": "rental_income",
            "workflow_status": "in_progress",
        }

    def _provide_guidance(self, state: BaseAgentState) -> dict[str, Any]:
        """Provide guidance on rental income taxation using LLM.

        Args:
            state: Current agent state

        Returns:
            State updates with guidance
        """
        shared_context = state.get("shared_context", {})

        # Build context for LLM, grounded in RAG knowledge
        rag_context = self._get_rag_context(state)
        context_parts = [
            "Key information about rental income in Romania:",
            "- Rental contracts must be registered with ANAF within 30 days",
            "- Registration is done through SPV (Spatiul Privat Virtual)",
            "- Rental income tax rate: 10% of gross income",
            "- Tax is declared and paid annually",
            "Ask the user for monthly rent amount to calculate the tax.",
        ]

        messages = [SystemMessage(content=RENTAL_INCOME_AGENT_SYSTEM_PROMPT)]
        if rag_context:
            messages.append(SystemMessage(content=f"Relevant tax code knowledge:\n{rag_context}"))
        messages.append(SystemMessage(content="\n".join(context_parts)))
        messages.extend(state["messages"])

        response = self.llm.invoke(messages)

        return {
            "messages": [response],
            "current_agent": "rental_income",
            "shared_context": {
                **shared_context,
                "awaiting_rental_data": True,
            },
            "workflow_status": "in_progress",
        }

    def register_contract(self, state: BaseAgentState) -> dict[str, Any]:
        """Register rental contract with ANAF.

        Args:
            state: Current agent state

        Returns:
            State updates with registration result
        """
        shared_context = state.get("shared_context", {})

        contract_data = {
            "landlord_cnp": shared_context.get("landlord_cnp"),
            "tenant_cnp": shared_context.get("tenant_cnp"),
            "property_address": shared_context.get("property_address"),
            "monthly_rent": shared_context.get("monthly_rent"),
            "contract_start_date": shared_context.get("contract_start_date"),
            "contract_end_date": shared_context.get("contract_end_date"),
        }

        result = mock_spv_register_contract(contract_data)

        if result["status"] == "success":
            context_message = (
                f"Contract registration successful. Present these details to the user:\n"
                f"- Registration number: {result['registration_number']}\n"
                f"- Registration date: {result['registration_date']}\n"
                f"- Status message: {result['message']}\n"
                f"Congratulate the user and offer further assistance."
            )
            workflow_status = "completed"
        else:
            context_message = f"Contract registration failed: {result.get('message', 'Unknown error')}. Explain what went wrong and offer to help retry."
            workflow_status = "error"

        rag_context = self._get_rag_context(state)
        messages = [SystemMessage(content=RENTAL_INCOME_AGENT_SYSTEM_PROMPT)]
        if rag_context:
            messages.append(SystemMessage(content=f"Relevant tax code knowledge:\n{rag_context}"))
        messages.extend(state["messages"])
        messages.append(SystemMessage(content=context_message))

        response = self.llm.invoke(messages)

        return {
            "messages": [response],
            "shared_context": {
                **shared_context,
                "contract_registration_status": result["status"],
                "contract_registration_number": result.get("registration_number"),
            },
            "current_agent": "rental_income",
            "workflow_status": workflow_status,
        }


_rental_income_agent = RentalIncomeAgent()


def rental_income_node(state: BaseAgentState) -> dict[str, Any]:
    """LangGraph node function for Rental Income agent."""
    return _rental_income_agent.process(state)
