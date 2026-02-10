"""PFA/Freelancer Agent - D212 filing and CAS/CASS contributions."""

from typing import Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage

from ro_tax_agents.state.base import BaseAgentState
from ro_tax_agents.config.prompts import PFA_AGENT_SYSTEM_PROMPT
from ro_tax_agents.config.settings import settings
from ro_tax_agents.services import calculation_agent_service
from ro_tax_agents.services import rag_service
from ro_tax_agents.mocks.tools import mock_spv_submit_d212


class PFAAgent:
    """PFA/Freelancer agent for D212 filing and CAS/CASS calculations.

    This agent handles:
    - D212 (Declaratia Unica) form guidance and submission
    - CAS/CASS contribution calculations
    - Tax obligation explanations for self-employed

    Uses RAG to ground responses in actual tax code knowledge.
    """

    RAG_AGENT_TYPE = "pfa"

    def __init__(self):
        self._llm = None

    def _get_rag_context(self, state: BaseAgentState) -> str:
        """Retrieve relevant tax knowledge from RAG vector store."""
        messages = state.get("messages", [])
        if not messages:
            return ""
        last_msg = messages[-1]
        query = last_msg.content if hasattr(last_msg, "content") else ""
        if not query:
            return ""
        try:
            docs = rag_service.retrieve(query, self.RAG_AGENT_TYPE, k=3)
            if docs:
                return "\n\n---\n\n".join(doc.page_content for doc in docs)
        except Exception:
            pass
        return ""

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
        """Process PFA-related requests.

        Args:
            state: Current agent state

        Returns:
            State updates with PFA guidance or calculations
        """
        shared_context = state.get("shared_context", {})
        detected_intent = state.get("detected_intent", "")
        extracted_entities = shared_context.get("extracted_entities", {})

        # Check if we have income information to calculate contributions
        annual_income = extracted_entities.get("annual_income") or shared_context.get("annual_income")

        if annual_income:
            # We have income data - calculate contributions
            return self._calculate_contributions(state, float(annual_income))
        else:
            # No income data - provide guidance and ask for information
            return self._provide_guidance(state)

    def _calculate_contributions(self, state: BaseAgentState, annual_income: float) -> dict[str, Any]:
        """Calculate CAS/CASS contributions for the given income.

        Args:
            state: Current agent state
            annual_income: Annual income in RON

        Returns:
            State updates with calculation results
        """
        shared_context = state.get("shared_context", {})

        # Update shared context with income and calculation type
        updated_context = {
            **shared_context,
            "annual_income": annual_income,
            "calculation_type": "pfa_contributions",
        }

        # Create updated state for calculation service
        calc_state = {**state, "shared_context": updated_context}

        # Call calculation service
        calc_result = calculation_agent_service.process(calc_state)

        # Get calculation results
        cas_amount = calc_result["shared_context"].get("cas_amount", 0)
        cass_amount = calc_result["shared_context"].get("cass_amount", 0)
        total = cas_amount + cass_amount

        # Use LLM to present the calculation results, grounded in RAG knowledge
        rag_context = self._get_rag_context(state)
        context_message = (
            f"Calculation completed. Present these results to the user:\n"
            f"- Annual income: {annual_income:,.2f} RON\n"
            f"- CAS (pension contribution): {cas_amount:,.2f} RON\n"
            f"- CASS (health contribution): {cass_amount:,.2f} RON\n"
            f"- Total contributions: {total:,.2f} RON\n"
            f"Also ask if they want to submit the D212 declaration or have other questions."
        )

        messages = [SystemMessage(content=PFA_AGENT_SYSTEM_PROMPT)]
        if rag_context:
            messages.append(SystemMessage(content=f"Relevant tax code knowledge:\n{rag_context}"))
        messages.extend(state["messages"])
        messages.append(SystemMessage(content=context_message))

        response = self.llm.invoke(messages)

        return {
            "messages": [response],
            "shared_context": calc_result["shared_context"],
            "current_agent": "pfa_agent",
            "workflow_status": "in_progress",
        }

    def _provide_guidance(self, state: BaseAgentState) -> dict[str, Any]:
        """Provide guidance on PFA tax obligations using LLM.

        Args:
            state: Current agent state

        Returns:
            State updates with guidance
        """
        shared_context = state.get("shared_context", {})

        # Build context for LLM, grounded in RAG knowledge
        rag_context = self._get_rag_context(state)
        context_parts = [
            f"Current tax thresholds (based on minimum salary {settings.minimum_gross_salary:,.0f} RON):",
            f"- CAS threshold: {settings.minimum_gross_salary * 12:,.2f} RON (12 minimum salaries)",
            f"- CASS threshold: {settings.minimum_gross_salary * 6:,.2f} RON (6 minimum salaries)",
            "Ask the user for their annual income to calculate contributions.",
        ]

        messages = [SystemMessage(content=PFA_AGENT_SYSTEM_PROMPT)]
        if rag_context:
            messages.append(SystemMessage(content=f"Relevant tax code knowledge:\n{rag_context}"))
        messages.append(SystemMessage(content="\n".join(context_parts)))
        messages.extend(state["messages"])

        response = self.llm.invoke(messages)

        return {
            "messages": [response],
            "current_agent": "pfa_agent",
            "shared_context": {
                **shared_context,
                "awaiting_income_data": True,
            },
            "workflow_status": "in_progress",
        }

    def submit_d212(self, state: BaseAgentState) -> dict[str, Any]:
        """Submit D212 form to ANAF SPV.

        Args:
            state: Current agent state

        Returns:
            State updates with submission result
        """
        shared_context = state.get("shared_context", {})

        d212_data = {
            "fiscal_year": shared_context.get("fiscal_year", 2024),
            "income": shared_context.get("annual_income"),
            "expenses": shared_context.get("expenses", 0),
            "cas_amount": shared_context.get("cas_amount"),
            "cass_amount": shared_context.get("cass_amount"),
        }

        # Mock SPV submission
        result = mock_spv_submit_d212(d212_data)

        if result.status == "success":
            context_message = (
                f"D212 declaration submitted successfully. Present these details to the user:\n"
                f"- Submission ID: {result.submission_id}\n"
                f"- Timestamp: {result.timestamp}\n"
                f"- Status: {result.message}\n"
                f"Congratulate the user and offer further assistance."
            )
            workflow_status = "completed"
        else:
            context_message = f"D212 submission failed with error: {result.message}. Explain what went wrong and offer to help retry."
            workflow_status = "error"

        rag_context = self._get_rag_context(state)
        messages = [SystemMessage(content=PFA_AGENT_SYSTEM_PROMPT)]
        if rag_context:
            messages.append(SystemMessage(content=f"Relevant tax code knowledge:\n{rag_context}"))
        messages.extend(state["messages"])
        messages.append(SystemMessage(content=context_message))

        response = self.llm.invoke(messages)

        return {
            "messages": [response],
            "shared_context": {
                **shared_context,
                "d212_submission_status": result.status,
                "d212_submission_id": result.submission_id,
            },
            "current_agent": "pfa_agent",
            "workflow_status": workflow_status,
        }


# Create singleton instance
_pfa_agent = PFAAgent()


def pfa_agent_node(state: BaseAgentState) -> dict[str, Any]:
    """LangGraph node function for PFA agent."""
    return _pfa_agent.process(state)
