"""Tests for RAG service (UiPath Context Grounding)."""

from unittest.mock import patch, MagicMock

import pytest

from ro_tax_agents.services.rag import (
    RAGService,
    AGENT_INDEXES,
)


class TestRAGServiceConfig:
    """Test RAG service configuration."""

    def test_agent_indexes_coverage(self):
        """RAG should cover PFA, rental_income, and certificate agents."""
        assert "pfa" in AGENT_INDEXES
        assert "rental_income" in AGENT_INDEXES
        assert "certificate" in AGENT_INDEXES

    def test_agent_indexes_have_values(self):
        """Each agent index should have a non-empty index name."""
        for agent_type, index_name in AGENT_INDEXES.items():
            assert index_name, f"Index name for {agent_type} is empty"
            assert isinstance(index_name, str)


class TestRAGServiceInstance:
    """Test RAG service instance behavior."""

    def test_lazy_initialization(self):
        """RAG service should not create retrievers until first use."""
        service = RAGService()
        assert service._llm is None
        assert len(service._retrievers) == 0

    def test_invalid_agent_type_raises_error(self):
        """Querying with invalid agent type should raise ValueError."""
        service = RAGService()
        with pytest.raises(ValueError, match="Invalid agent type"):
            service._get_retriever("nonexistent_agent")

    def test_retrieve_returns_documents(self):
        """Retrieve should return a list of documents."""
        service = RAGService()

        mock_doc = MagicMock()
        mock_doc.page_content = "Test content about CAS contributions"

        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = [mock_doc]

        service._retrievers = {"pfa": mock_retriever}

        results = service.retrieve("CAS contributions", "pfa", k=3)
        assert len(results) == 1
        assert results[0].page_content == "Test content about CAS contributions"
        mock_retriever.invoke.assert_called_once_with("CAS contributions")

    def test_retrieve_sets_number_of_results(self):
        """Retrieve should set number_of_results on the retriever."""
        service = RAGService()

        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = []
        service._retrievers = {"pfa": mock_retriever}

        service.retrieve("test", "pfa", k=5)
        assert mock_retriever.number_of_results == 5

    def test_get_retriever_creates_on_first_call(self):
        """_get_retriever should create a new retriever on first call."""
        service = RAGService()
        assert "pfa" not in service._retrievers

        with patch(
            "ro_tax_agents.services.rag.ContextGroundingRetriever"
        ) as MockRetriever:
            retriever = service._get_retriever("pfa")
            MockRetriever.assert_called_once()
            call_kwargs = MockRetriever.call_args.kwargs
            assert call_kwargs["index_name"] == AGENT_INDEXES["pfa"]

    def test_get_retriever_caches(self):
        """_get_retriever should return cached retriever on subsequent calls."""
        service = RAGService()

        with patch(
            "ro_tax_agents.services.rag.ContextGroundingRetriever"
        ) as MockRetriever:
            r1 = service._get_retriever("pfa")
            r2 = service._get_retriever("pfa")
            assert r1 is r2
            # Only called once despite two _get_retriever calls
            MockRetriever.assert_called_once()


class TestRAGAgentIntegration:
    """Test that domain agents correctly import and reference RAG."""

    def test_pfa_agent_has_rag(self):
        """PFA agent should reference RAG service."""
        from ro_tax_agents.agents.pfa import PFAAgent
        agent = PFAAgent()
        assert agent.RAG_AGENT_TYPE == "pfa"
        assert hasattr(agent, "_get_rag_context")

    def test_rental_income_agent_has_rag(self):
        """Rental income agent should reference RAG service."""
        from ro_tax_agents.agents.rental_income import RentalIncomeAgent
        agent = RentalIncomeAgent()
        assert agent.RAG_AGENT_TYPE == "rental_income"
        assert hasattr(agent, "_get_rag_context")

    def test_certificate_agent_has_rag(self):
        """Certificate agent should reference RAG service."""
        from ro_tax_agents.agents.certificate import CertificateAgent
        agent = CertificateAgent()
        assert agent.RAG_AGENT_TYPE == "certificate"
        assert hasattr(agent, "_get_rag_context")

    def test_rag_agent_uses_rag(self):
        """RAG agent should use RAG for knowledge retrieval."""
        from ro_tax_agents.agents.rag import RAGAgent
        agent = RAGAgent()
        assert hasattr(agent, "_retrieve_across_all_bases")
