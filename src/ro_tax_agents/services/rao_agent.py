"""RAO Agent Service - Tax Code Knowledge expert."""

from typing import Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage

from ro_tax_agents.state.base import BaseAgentState
from ro_tax_agents.config.prompts import RAO_AGENT_SYSTEM_PROMPT
from ro_tax_agents.config.settings import settings


class RAOAgentService:
    """Tax Code Knowledge expert service.

    This service provides expertise on Romanian tax legislation,
    procedures, and compliance requirements.
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
        """Provide tax code expertise based on the current context.

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

        # Get tax guidance from LLM
        try:
            response = self.llm.invoke([
                SystemMessage(content=RAO_AGENT_SYSTEM_PROMPT),
                HumanMessage(content=tax_question),
            ])

            return {
                "messages": [response],
                "shared_context": {
                    **shared_context,
                    "tax_guidance_provided": True,
                    "last_tax_question": tax_question,
                },
            }
        except Exception as e:
            # Fallback response if LLM fails
            return {
                "messages": [AIMessage(
                    content="Nu am putut procesa intrebarea fiscala. "
                    "Va rugam sa consultati un consilier fiscal autorizat pentru informatii detaliate."
                )],
                "shared_context": {
                    **shared_context,
                    "tax_guidance_provided": False,
                    "tax_guidance_error": str(e),
                },
            }

    def __call__(self, state: BaseAgentState) -> dict[str, Any]:
        """Make the service callable as a LangGraph node."""
        return self.process(state)


# Singleton instance
rao_agent_service = RAOAgentService()
