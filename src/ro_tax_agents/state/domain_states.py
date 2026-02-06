"""Domain-specific state extensions for each agent."""

from typing import Optional, Literal
from decimal import Decimal

from ro_tax_agents.state.base import BaseAgentState


class PFAAgentState(BaseAgentState):
    """State for PFA/Freelancer agent workflows.

    Extends base state with D212 and contribution-specific fields.
    """

    # D212 form data
    d212_income: Optional[Decimal]
    d212_expenses: Optional[Decimal]
    cas_amount: Optional[Decimal]
    cass_amount: Optional[Decimal]
    fiscal_year: Optional[int]


class PropertySaleAgentState(BaseAgentState):
    """State for property sale tax calculation workflows."""

    property_value: Optional[Decimal]
    ownership_duration_years: Optional[int]
    tax_rate: Optional[Decimal]  # 1% or 3%
    calculated_tax: Optional[Decimal]


class RentalIncomeAgentState(BaseAgentState):
    """State for rental contract registration workflows."""

    contract_start_date: Optional[str]
    contract_end_date: Optional[str]
    monthly_rent: Optional[Decimal]
    property_address: Optional[str]
    tenant_cnp: Optional[str]
    landlord_cnp: Optional[str]


class CertificateAgentState(BaseAgentState):
    """State for fiscal attestation requests."""

    certificate_type: Optional[str]
    request_purpose: Optional[str]
    delivery_method: Optional[Literal["electronic", "physical"]]
    cnp_cui: Optional[str]


class EFacturaAgentState(BaseAgentState):
    """State for E-Factura operations."""

    invoice_type: Optional[Literal["B2B", "B2C"]]
    seller_cui: Optional[str]
    buyer_cui: Optional[str]
    invoice_items: list[dict]
    invoice_total: Optional[Decimal]
    invoice_vat: Optional[Decimal]
    invoice_xml: Optional[str]
    upload_index: Optional[str]
