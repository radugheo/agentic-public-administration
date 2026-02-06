"""Tax form data models."""

from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional


class D212Form(BaseModel):
    """D212 (Declaratia Unica) form data model."""

    fiscal_year: int = Field(..., description="Fiscal year for the declaration")
    total_income: Decimal = Field(..., description="Total income in RON")
    total_expenses: Decimal = Field(default=Decimal("0"), description="Total expenses in RON")
    net_income: Optional[Decimal] = Field(default=None, description="Net income (calculated)")
    cas_due: Optional[Decimal] = Field(default=None, description="CAS contribution due")
    cass_due: Optional[Decimal] = Field(default=None, description="CASS contribution due")
    cnp: str = Field(..., description="Personal identification number (CNP)")
    activity_code: Optional[str] = Field(default=None, description="CAEN activity code")

    def calculate_net_income(self) -> Decimal:
        """Calculate net income."""
        self.net_income = self.total_income - self.total_expenses
        return self.net_income


class RentalContract(BaseModel):
    """Rental contract data model for ANAF registration."""

    landlord_name: str = Field(..., description="Landlord full name")
    landlord_cnp: str = Field(..., description="Landlord CNP")
    tenant_name: str = Field(..., description="Tenant full name")
    tenant_cnp: str = Field(..., description="Tenant CNP")
    property_address: str = Field(..., description="Property address")
    monthly_rent: Decimal = Field(..., description="Monthly rent in RON")
    contract_start_date: str = Field(..., description="Contract start date (YYYY-MM-DD)")
    contract_end_date: str = Field(..., description="Contract end date (YYYY-MM-DD)")
    registration_number: Optional[str] = Field(
        default=None, description="ANAF registration number"
    )
