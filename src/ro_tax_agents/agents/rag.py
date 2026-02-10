"""RAG Agent - Tax Code Knowledge expert, powered by retrieval-augmented generation."""

from typing import Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage

from ro_tax_agents.state.base import BaseAgentState
from ro_tax_agents.config.prompts import RAG_AGENT_SYSTEM_PROMPT
from ro_tax_agents.config.settings import settings
from ro_tax_agents.services.rag import rag_service, AGENT_INDEXES


class RAGAgent:
    """Tax Code Knowledge expert, powered by RAG.

    Provides expertise on Romanian tax legislation by retrieving
    relevant knowledge from the RAG vector store across all
    available agent knowledge bases.
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

    def _retrieve_across_all_bases(self, query: str, k: int = 2) -> str:
        """Retrieve relevant knowledge from ALL RAG knowledge bases.

        For general tax questions, we search across pfa, rental_income,
        and certificate knowledge bases to find the most relevant context.
        """
        all_docs = []
        for agent_type in AGENT_INDEXES:
            try:
                docs = rag_service.retrieve(query, agent_type, k=k)
                all_docs.extend(docs)
            except Exception:
                continue

        if not all_docs:
            return ""
        return "\n\n---\n\n".join(doc.page_content for doc in all_docs)

    def process(self, state: BaseAgentState) -> dict[str, Any]:
        """Provide RAG-grounded tax code expertise.

        Args:
            state: Current agent state

        Returns:
            State updates with tax guidance
        """
        shared_context = state.get("shared_context", {})
        tax_question = shared_context.get("tax_question")

        # If no explicit question, extract from last message
        if not tax_question:
            messages = state.get("messages", [])
            if messages:
                last_message = messages[-1]
                if hasattr(last_message, "content"):
                    tax_question = last_message.content

        if not tax_question:
            return {
                "messages": [AIMessage(content="Nu am primit o intrebare specifica despre legislatia fiscala.")],
                "shared_context": {
                    **shared_context,
                    "tax_guidance_provided": False,
                },
            }

        # Retrieve relevant knowledge from RAG
        rag_context = self._retrieve_across_all_bases(str(tax_question))

        # Build messages with RAG context
        llm_messages: list[SystemMessage | HumanMessage] = [SystemMessage(content=RAG_AGENT_SYSTEM_PROMPT)]
        if rag_context:
            llm_messages.append(SystemMessage(
                content=f"Relevant tax code knowledge retrieved from the knowledge base:\n{rag_context}"
            ))
        llm_messages.append(HumanMessage(content=str(tax_question)))

        response = self.llm.invoke(llm_messages)

        return {
            "messages": [response],
            "shared_context": {
                **shared_context,
                "tax_guidance_provided": True,
                "last_tax_question": tax_question,
            },
        }


_rag_agent = RAGAgent()


def rag_node(state: BaseAgentState) -> dict[str, Any]:
    """LangGraph node function for RAG agent."""
    return _rag_agent.process(state)
