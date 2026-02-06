"""Invoice data models for E-Factura."""

from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional, Literal
from datetime import date


class InvoiceItem(BaseModel):
    """Individual invoice line item."""

    description: str = Field(..., description="Item description")
    quantity: Decimal = Field(..., description="Quantity")
    unit_price: Decimal = Field(..., description="Unit price in RON")
    vat_rate: Decimal = Field(default=Decimal("0.19"), description="VAT rate (default 19%)")
    total_without_vat: Optional[Decimal] = Field(default=None)
    vat_amount: Optional[Decimal] = Field(default=None)
    total_with_vat: Optional[Decimal] = Field(default=None)

    def calculate_totals(self) -> None:
        """Calculate line item totals."""
        self.total_without_vat = self.quantity * self.unit_price
        self.vat_amount = self.total_without_vat * self.vat_rate
        self.total_with_vat = self.total_without_vat + self.vat_amount


class Invoice(BaseModel):
    """E-Factura invoice model."""

    invoice_number: str = Field(..., description="Invoice number")
    invoice_date: date = Field(..., description="Invoice date")
    invoice_type: Literal["B2B", "B2C"] = Field(..., description="Invoice type")

    # Seller info
    seller_name: str = Field(..., description="Seller company name")
    seller_cui: str = Field(..., description="Seller CUI/CIF")
    seller_address: str = Field(..., description="Seller address")
    seller_reg_number: Optional[str] = Field(default=None, description="Trade registry number")

    # Buyer info
    buyer_name: str = Field(..., description="Buyer name")
    buyer_cui: Optional[str] = Field(default=None, description="Buyer CUI (required for B2B)")
    buyer_address: str = Field(..., description="Buyer address")

    # Invoice items
    items: list[InvoiceItem] = Field(default_factory=list, description="Invoice line items")

    # Totals (calculated)
    total_without_vat: Optional[Decimal] = Field(default=None)
    total_vat: Optional[Decimal] = Field(default=None)
    total_with_vat: Optional[Decimal] = Field(default=None)

    # E-Factura specific
    upload_index: Optional[str] = Field(default=None, description="E-Factura upload index")
    xml_content: Optional[str] = Field(default=None, description="Generated XML content")

    def calculate_totals(self) -> None:
        """Calculate invoice totals from items."""
        for item in self.items:
            item.calculate_totals()

        self.total_without_vat = sum(
            item.total_without_vat or Decimal("0") for item in self.items
        )
        self.total_vat = sum(item.vat_amount or Decimal("0") for item in self.items)
        self.total_with_vat = self.total_without_vat + self.total_vat
