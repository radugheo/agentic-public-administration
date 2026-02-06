"""Payment-related data models."""

from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional
from datetime import datetime


class PaymentRequest(BaseModel):
    """Payment request for Ghiseul.ro."""

    amount: Decimal = Field(..., description="Payment amount in RON")
    payment_type: str = Field(..., description="Type of tax payment")
    reference_number: Optional[str] = Field(
        default=None, description="Reference number for the payment"
    )
    user_cnp: Optional[str] = Field(default=None, description="User CNP")
    user_cui: Optional[str] = Field(default=None, description="Company CUI if applicable")
    description: Optional[str] = Field(default=None, description="Payment description")


class PaymentResult(BaseModel):
    """Result from Ghiseul.ro payment processing."""

    status: str = Field(..., description="Payment status (success/failed/pending)")
    transaction_id: Optional[str] = Field(default=None, description="Transaction ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="Transaction timestamp")
    message: str = Field(..., description="Status message")
    redirect_url: Optional[str] = Field(default=None, description="Payment redirect URL")
