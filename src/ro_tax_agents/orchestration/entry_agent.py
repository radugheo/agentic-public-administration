"""Entry Agent - Intent detection and routing."""

from typing import Literal
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from ro_tax_agents.state.base import BaseAgentState
from ro_tax_agents.config.prompts import ENTRY_AGENT_SYSTEM_PROMPT
from ro_tax_agents.config.settings import settings


class ExtractedEntities(BaseModel):
    """Entities extracted from user message."""

    annual_income: float | None = Field(default=None, description="Annual income in RON if mentioned")
    property_value: float | None = Field(default=None, description="Property value if mentioned")
    ownership_years: int | None = Field(default=None, description="Years of ownership if mentioned")
    monthly_rent: float | None = Field(default=None, description="Monthly rent if mentioned")
    invoice_type: str | None = Field(default=None, description="Invoice type (B2B/B2C) if mentioned")

    model_config = {"extra": "forbid"}


class IntentClassification(BaseModel):
    """Structured output for intent classification."""

    intent: Literal[
        "pfa_d212_filing",
        "pfa_cas_cass",
        "property_sale_tax",
        "rental_contract_registration",
        "fiscal_certificate",
        "efactura_b2b",
        "efactura_b2c",
        "general_question",
        "unclear",
    ] = Field(description="The classified intent of the user request")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score for the classification")
    reasoning: str = Field(description="Brief reasoning for the classification")
    extracted_entities: ExtractedEntities = Field(
        default_factory=ExtractedEntities,
        description="Any relevant entities extracted from the user message"
    )

    model_config = {"extra": "forbid"}


def entry_agent_node(state: BaseAgentState) -> dict:
    """Entry agent that detects intent and routes to appropriate domain agent.

    This is the main entry point for user requests. It analyzes the user's
    message, classifies the intent, and determines which domain agent should
    handle the request.

    Args:
        state: Current agent state with user messages

    Returns:
        State updates with intent classification and routing decision
    """
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0,
        api_key=settings.openai_api_key or None,
    )

    query = state["query"]
    user_message = HumanMessage(content=query)

    try:
        structured_llm = llm.with_structured_output(IntentClassification)

        result: IntentClassification = structured_llm.invoke([
            SystemMessage(content=ENTRY_AGENT_SYSTEM_PROMPT),
            user_message,
        ])

        # Map intents to domain agents
        intent_to_agent = {
            "pfa_d212_filing": "pfa",
            "pfa_cas_cass": "pfa",
            "property_sale_tax": "property_sale",
            "rental_contract_registration": "rental_income",
            "fiscal_certificate": "certificate",
            "efactura_b2b": "efactura",
            "efactura_b2c": "efactura",
            "general_question": "rag",  # Route general questions to RAG agent
            "unclear": "clarify",
        }

        next_agent = intent_to_agent.get(result.intent, "clarify")

        return {
            "messages": [user_message],
            "detected_intent": result.intent,
            "intent_confidence": result.confidence,
            "next_agent": next_agent,
            "current_agent": "entry_agent",
            "shared_context": {
                **state.get("shared_context", {}),
                "intent_reasoning": result.reasoning,
                "extracted_entities": result.extracted_entities.model_dump(),
            },
            "workflow_status": "in_progress",
        }

    except Exception as e:
        # Fallback if LLM fails - ask for clarification
        return {
            "messages": [
                user_message,
                AIMessage(
                    content="Nu am putut procesa cererea. Va rugam sa reformulati intrebarea sau sa specificati mai clar ce serviciu doriti."
                ),
            ],
            "detected_intent": "unclear",
            "intent_confidence": 0.0,
            "next_agent": "clarify",
            "current_agent": "entry_agent",
            "shared_context": {
                **state.get("shared_context", {}),
                "entry_agent_error": str(e),
            },
            "workflow_status": "in_progress",
        }


def request_clarification_node(state: BaseAgentState) -> dict:
    """Node that requests clarification from the user.

    Args:
        state: Current agent state

    Returns:
        State updates with clarification request
    """
    intent_reasoning = state.get("shared_context", {}).get("intent_reasoning", "")

    message = (
        "Nu am inteles exact ce doriti sa faceti. "
        "Va rog sa specificati unul dintre urmatoarele servicii:\n\n"
        "1. **D212 / Contributii PFA** - depunere declaratie unica, calcul CAS/CASS\n"
        "2. **Impozit vanzare proprietate** - calcul impozit 1% sau 3%\n"
        "3. **Inregistrare contract inchiriere** - inregistrare la ANAF\n"
        "4. **Certificat fiscal** - obtinere certificat de atestare fiscala\n"
        "5. **E-Factura** - emitere facturi electronice B2B/B2C\n\n"
        "Cu ce va pot ajuta?"
    )

    return {
        "messages": [AIMessage(content=message)],
        "next_agent": None,  # Wait for user input
        "workflow_status": "pending",
    }
