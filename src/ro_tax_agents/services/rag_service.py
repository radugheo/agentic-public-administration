"""RAG Service - Retrieval-Augmented Generation using UiPath Context Grounding."""

from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from langchain_core.messages import SystemMessage, HumanMessage
from uipath_langchain.retrievers import ContextGroundingRetriever

from ro_tax_agents.config.settings import settings


# Mapping of agent types to UiPath Context Grounding index names
AGENT_INDEXES = {
    "pfa": settings.uipath_index_pfa,
    "rental_income": settings.uipath_index_rental_income,
    "certificate": settings.uipath_index_certificate,
}

# Prompt de sistem pentru răspunsurile RAG
RAG_SYSTEM_PROMPT = """Ești un expert în legislația fiscală din România.
Răspunde întrebărilor utilizatorului DOAR pe baza contextului furnizat mai jos.
Dacă informația nu se găsește în context, spune clar că nu ai informația necesară.
Răspunde în limba română, clar și concis.

Context relevant:
{context}
"""


class RAGService:
    """RAG service using UiPath Context Grounding for knowledge retrieval.

    Uses ContextGroundingRetriever to query UiPath-hosted vector indexes
    for each agent type (pfa, rental_income, certificate).
    """

    def __init__(self):
        self._retrievers: dict[str, ContextGroundingRetriever] = {}
        self._llm = None

    def _get_retriever(self, tip_agent: str) -> ContextGroundingRetriever:
        """Get or create a retriever for the given agent type."""
        if tip_agent not in self._retrievers:
            if tip_agent not in AGENT_INDEXES:
                tipuri_valide = list(AGENT_INDEXES.keys())
                raise ValueError(
                    f"Tip agent invalid: '{tip_agent}'. Tipuri valide: {tipuri_valide}"
                )
            self._retrievers[tip_agent] = ContextGroundingRetriever(
                index_name=AGENT_INDEXES[tip_agent],
                folder_path=settings.uipath_folder_path or None,
            )
        return self._retrievers[tip_agent]

    @property
    def llm(self) -> ChatOpenAI:
        """Lazy initialization for LLM."""
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=settings.openai_model,
                temperature=0,
                api_key=settings.openai_api_key or None,
            )
        return self._llm

    def retrieve(self, query: str, tip_agent: str, k: int = 3) -> list[Document]:
        """Retrieve the most relevant documents for a query.

        Args:
            query: User question
            tip_agent: Agent type (pfa, rental_income, certificate)
            k: Number of documents to return

        Returns:
            List of relevant documents

        Raises:
            ValueError: If agent type is invalid
        """
        retriever = self._get_retriever(tip_agent)
        retriever.number_of_results = k
        return retriever.invoke(query)

    def query(self, intrebare: str, tip_agent: str, k: int = 3) -> str:
        """Full RAG query: retrieval + LLM answer generation.

        Args:
            intrebare: User question
            tip_agent: Agent type (pfa, rental_income, certificate)
            k: Number of documents to use as context

        Returns:
            LLM-generated answer based on retrieved context
        """
        documente = self.retrieve(intrebare, tip_agent, k=k)
        context = "\n\n---\n\n".join(doc.page_content for doc in documente)

        prompt_sistem = RAG_SYSTEM_PROMPT.format(context=context)

        raspuns = self.llm.invoke([
            SystemMessage(content=prompt_sistem),
            HumanMessage(content=intrebare),
        ])

        return raspuns.content


# Singleton instance
rag_service = RAGService()
