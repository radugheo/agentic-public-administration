"""Base mixin for domain agents with RAG and LLM support."""

from langchain_openai import ChatOpenAI

from ro_tax_agents.state.base import BaseAgentState
from ro_tax_agents.config.settings import settings
from ro_tax_agents.services import rag_service


class RAGEnabledAgentMixin:
    """Mixin providing shared RAG context retrieval and lazy LLM initialization.

    Domain agents should:
    1. Set the class attribute RAG_AGENT_TYPE to their agent type string
    2. Inherit from this mixin
    """

    RAG_AGENT_TYPE: str = ""
    LLM_TEMPERATURE: float = 0

    def __init__(self):
        self._llm = None

    @property
    def llm(self) -> ChatOpenAI:
        """Lazy initialization of the LLM."""
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=settings.openai_model,
                temperature=self.LLM_TEMPERATURE,
                api_key=settings.openai_api_key or None,
            )
        return self._llm

    def _get_rag_context(self, state: BaseAgentState) -> str:
        """Retrieve relevant tax knowledge from RAG vector store.

        Args:
            state: Current agent state containing messages

        Returns:
            Formatted string of relevant document contents, or empty string
        """
        if not self.RAG_AGENT_TYPE:
            return ""
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
