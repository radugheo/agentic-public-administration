"""Certificate Agent - Fiscal attestation certificates."""

from typing import Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from ro_tax_agents.state.base import BaseAgentState
from ro_tax_agents.config.prompts import CERTIFICATE_AGENT_SYSTEM_PROMPT
from ro_tax_agents.config.settings import settings
from ro_tax_agents.services import rag_service
from ro_tax_agents.mocks.tools import mock_fiscal_certificate_request


class CertificateAgent:
    """Certificate agent for fiscal attestation requests.

    Uses LLM for all responses, grounded in RAG tax code knowledge.
    """

    RAG_AGENT_TYPE = "certificate"

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
                temperature=0.3,
                api_key=settings.openai_api_key or None,
            )
        return self._llm

    def process(self, state: BaseAgentState) -> dict[str, Any]:
        """Process fiscal certificate requests using LLM."""
        shared_context = state.get("shared_context", {})
        extracted_entities = shared_context.get("extracted_entities", {})

        # Check if we have data to submit a certificate request
        certificate_type = extracted_entities.get("certificate_type") or shared_context.get("certificate_type")
        cnp_cui = extracted_entities.get("cnp_cui") or shared_context.get("cnp_cui")

        if certificate_type and cnp_cui:
            return self._request_certificate(state, certificate_type, cnp_cui)
        else:
            return self._llm_response(state)

    def _llm_response(self, state: BaseAgentState) -> dict[str, Any]:
        """Generate LLM response for user interaction."""
        shared_context = state.get("shared_context", {})

        # Build context for LLM
        context_parts = []
        if shared_context.get("certificate_type"):
            context_parts.append(f"Certificate type requested: {shared_context['certificate_type']}")
        if shared_context.get("cnp_cui"):
            context_parts.append(f"CNP/CUI provided: {shared_context['cnp_cui']}")

        context = "\n".join(context_parts) if context_parts else "No additional context available."

        rag_context = self._get_rag_context(state)
        messages = [SystemMessage(content=CERTIFICATE_AGENT_SYSTEM_PROMPT)]
        if rag_context:
            messages.append(SystemMessage(content=f"Relevant tax code knowledge:\n{rag_context}"))
        messages.append(SystemMessage(content=f"Current context:\n{context}"))
        messages.extend(state["messages"])

        response = self.llm.invoke(messages)

        return {
            "messages": [response],
            "current_agent": "certificate_agent",
            "shared_context": shared_context,
            "workflow_status": "in_progress",
        }

    def _request_certificate(self, state: BaseAgentState, certificate_type: str, cnp_cui: str) -> dict[str, Any]:
        """Request certificate via mock SPV and use LLM to present result."""
        shared_context = state.get("shared_context", {})

        # Call mock external system
        result = mock_fiscal_certificate_request(cnp_cui, certificate_type)

        # Build result context for LLM
        result_info = (
            f"Certificate request result:\n"
            f"- Status: {result['status']}\n"
            f"- Request ID: {result.get('request_id', 'N/A')}\n"
            f"- Certificate type: {result.get('certificate_type', certificate_type)}\n"
            f"- Estimated time: {result.get('estimated_completion', 'N/A')}\n"
            f"- System message: {result.get('message', 'N/A')}"
        )

        workflow_status = "completed" if result["status"] == "success" else "error"

        rag_context = self._get_rag_context(state)
        messages = [SystemMessage(content=CERTIFICATE_AGENT_SYSTEM_PROMPT)]
        if rag_context:
            messages.append(SystemMessage(content=f"Relevant tax code knowledge:\n{rag_context}"))
        messages.append(SystemMessage(content=result_info))
        messages.append(HumanMessage(content="Present the certificate request result to the user in a friendly, informative way."))

        response = self.llm.invoke(messages)

        return {
            "messages": [response],
            "shared_context": {
                **shared_context,
                "certificate_request_status": result["status"],
                "certificate_request_id": result.get("request_id"),
            },
            "current_agent": "certificate_agent",
            "workflow_status": workflow_status,
        }


_certificate_agent = CertificateAgent()


def certificate_agent_node(state: BaseAgentState) -> dict[str, Any]:
    """LangGraph node function for Certificate agent."""
    return _certificate_agent.process(state)
