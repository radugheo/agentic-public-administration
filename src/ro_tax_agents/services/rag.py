"""RAG Service - Retrieval-Augmented Generation using UiPath Context Grounding."""

from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from langchain_core.messages import SystemMessage, HumanMessage
from uipath_langchain.retrievers import ContextGroundingRetriever

from ro_tax_agents.config.settings import settings


# Mapping of agent types to UiPath Context Grounding index names
AGENT_INDEXES = settings.rag_index_mapping

# System prompt for RAG responses
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

    def _get_retriever(self, agent_type: str) -> ContextGroundingRetriever:
        """Get or create a retriever for the given agent type."""
        if agent_type not in self._retrievers:
            if agent_type not in AGENT_INDEXES:
                valid_types = list(AGENT_INDEXES.keys())
                raise ValueError(
                    f"Invalid agent type: '{agent_type}'. Valid types: {valid_types}"
                )
            self._retrievers[agent_type] = ContextGroundingRetriever(
                index_name=AGENT_INDEXES[agent_type],
                folder_path=settings.uipath_folder_path or None,
            )
        return self._retrievers[agent_type]

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

    def retrieve(self, query: str, agent_type: str, k: int = 3) -> list[Document]:
        """Retrieve the most relevant documents for a query.

        Args:
            query: User question
            agent_type: Agent type (pfa, rental_income, certificate)
            k: Number of documents to return

        Returns:
            List of relevant documents

        Raises:
            ValueError: If agent type is invalid
        """
        retriever = self._get_retriever(agent_type)
        retriever.number_of_results = k
        return retriever.invoke(query)

    def query(self, question: str, agent_type: str, k: int = 3) -> str:
        """Full RAG query: retrieval + LLM answer generation.

        Args:
            question: User question
            agent_type: Agent type (pfa, rental_income, certificate)
            k: Number of documents to use as context

        Returns:
            LLM-generated answer based on retrieved context
        """
        documents = self.retrieve(question, agent_type, k=k)
        context = "\n\n---\n\n".join(doc.page_content for doc in documents)

        system_prompt = RAG_SYSTEM_PROMPT.format(context=context)

        response = self.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=question),
        ])

        return response.content


# Singleton instance
rag_service = RAGService()
