"""Pytest configuration and fixtures."""

import pytest
from unittest.mock import patch, MagicMock

from ro_tax_agents.graph import compile_graph, get_initial_state


@pytest.fixture
def mock_openai():
    """Mock OpenAI API calls for testing without API key."""
    with patch("langchain_openai.ChatOpenAI") as mock:
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = MagicMock(
            content="Mock response",
            type="ai"
        )
        mock_instance.with_structured_output.return_value = mock_instance
        mock.return_value = mock_instance
        yield mock


@pytest.fixture
def graph():
    """Compile the main graph for testing."""
    return compile_graph()


@pytest.fixture
def initial_state():
    """Create a fresh initial state."""
    return get_initial_state("test-session-123", "test-user")


@pytest.fixture
def pfa_state(initial_state):
    """State pre-configured for PFA testing."""
    initial_state["shared_context"] = {
        "annual_income": 150000,
        "calculation_type": "pfa_contributions",
    }
    return initial_state


@pytest.fixture
def property_sale_state(initial_state):
    """State pre-configured for property sale testing."""
    initial_state["shared_context"] = {
        "property_value": 100000,
        "ownership_duration_years": 5,
        "calculation_type": "property_sale_tax",
    }
    return initial_state
