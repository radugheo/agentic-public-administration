"""Payment Service - Ghiseul.ro integration."""

from typing import Any
from decimal import Decimal
from langchain_core.messages import AIMessage

from ro_tax_agents.state.base import BaseAgentState
from ro_tax_agents.mocks.tools import mock_ghiseul_payment
from ro_tax_agents.models.payments import PaymentRequest


class PaymentService:
    """Ghiseul.ro payment integration service.

    This service handles tax payment processing through the
    Ghiseul.ro platform.
    """

    def process(self, state: BaseAgentState) -> dict[str, Any]:
        """Process payment through Ghiseul.ro.

        Args:
            state: Current agent state

        Returns:
            State updates with payment result
        """
        shared_context = state.get("shared_context", {})

        # Get payment details from context
        payment_amount = shared_context.get("payment_amount")
        payment_type = shared_context.get("payment_type", "tax_payment")
        reference_number = shared_context.get("reference_number")
        user_cnp = shared_context.get("user_cnp")
        user_cui = shared_context.get("user_cui")

        if not payment_amount:
            return {
                "messages": [AIMessage(content="Nu a fost specificata suma pentru plata.")],
                "workflow_status": "error",
                "error_message": "Missing payment amount",
            }

        # Create payment request
        payment_request = PaymentRequest(
            amount=Decimal(str(payment_amount)),
            payment_type=payment_type,
            reference_number=reference_number,
            user_cnp=user_cnp,
            user_cui=user_cui,
            description=f"Plata {payment_type}",
        )

        # Process payment through mock Ghiseul.ro
        result = mock_ghiseul_payment(payment_request)

        if result.status == "success":
            message = (
                f"Plata procesata cu succes!\n\n"
                f"Detalii tranzactie:\n"
                f"  Suma: {payment_amount:,.2f} RON\n"
                f"  Tip: {payment_type}\n"
                f"  ID Tranzactie: {result.transaction_id}\n"
                f"  Data: {result.timestamp}\n\n"
                f"Link pentru plata: {result.redirect_url}"
            )
            workflow_status = "completed"
        else:
            message = f"Plata nu a putut fi procesata: {result.message}"
            workflow_status = "error"

        return {
            "shared_context": {
                **shared_context,
                "payment_status": result.status,
                "payment_transaction_id": result.transaction_id,
                "payment_timestamp": str(result.timestamp),
                "payment_redirect_url": result.redirect_url,
            },
            "messages": [AIMessage(content=message)],
            "workflow_status": workflow_status,
        }

    def __call__(self, state: BaseAgentState) -> dict[str, Any]:
        """Make the service callable as a LangGraph node."""
        return self.process(state)


# Singleton instance
payment_service = PaymentService()
