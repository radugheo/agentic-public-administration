"""State definitions for the agent system."""

from ro_tax_agents.state.base import BaseAgentState
from ro_tax_agents.state.domain_states import (
    PFAAgentState,
    PropertySaleAgentState,
    RentalIncomeAgentState,
    CertificateAgentState,
    EFacturaAgentState,
)

__all__ = [
    "BaseAgentState",
    "PFAAgentState",
    "PropertySaleAgentState",
    "RentalIncomeAgentState",
    "CertificateAgentState",
    "EFacturaAgentState",
]
