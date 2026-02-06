"""Mock implementations for external systems and tools."""

from ro_tax_agents.mocks.uipath_sdk import MockUiPathSDK, mock_uipath
from ro_tax_agents.mocks.tools import (
    mock_spv_login,
    mock_spv_submit_d212,
    mock_spv_register_contract,
    mock_ghiseul_payment,
    mock_ocr_document,
    mock_efactura_submit,
    mock_efactura_status,
)
from ro_tax_agents.mocks.external_systems import (
    MockANAFSPV,
    MockGhiseulRo,
    MockEFacturaSystem,
    mock_anaf_spv,
    mock_ghiseul,
    mock_efactura_system,
)

__all__ = [
    "MockUiPathSDK",
    "mock_uipath",
    "mock_spv_login",
    "mock_spv_submit_d212",
    "mock_spv_register_contract",
    "mock_ghiseul_payment",
    "mock_ocr_document",
    "mock_efactura_submit",
    "mock_efactura_status",
    "MockANAFSPV",
    "MockGhiseulRo",
    "MockEFacturaSystem",
    "mock_anaf_spv",
    "mock_ghiseul",
    "mock_efactura_system",
]
