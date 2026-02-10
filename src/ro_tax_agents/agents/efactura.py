"""E-Factura Agent - Electronic invoicing B2B/B2C."""

from typing import Any
from langchain_core.messages import SystemMessage

from ro_tax_agents.state.base import BaseAgentState
from ro_tax_agents.config.prompts import EFACTURA_AGENT_SYSTEM_PROMPT
from ro_tax_agents.mocks.tools import mock_efactura_submit, mock_efactura_status
from ro_tax_agents.agents._base import RAGEnabledAgentMixin


class EFacturaAgent(RAGEnabledAgentMixin):
    """E-Factura agent for electronic invoicing.

    This agent handles:
    - B2B electronic invoicing (mandatory for VAT-registered companies)
    - B2C electronic invoicing
    - Invoice submission and status tracking
    """

    def process(self, state: BaseAgentState) -> dict[str, Any]:
        """Process E-Factura requests.

        Args:
            state: Current agent state

        Returns:
            State updates with E-Factura guidance or submission
        """
        shared_context = state.get("shared_context", {})
        extracted_entities = shared_context.get("extracted_entities", {})
        detected_intent = state.get("detected_intent", "")

        # Check if we have invoice data to submit
        invoice_xml = shared_context.get("invoice_xml")
        seller_cui = extracted_entities.get("seller_cui") or shared_context.get("seller_cui")

        # Check if checking status of existing invoice
        upload_index = shared_context.get("check_upload_index")
        if upload_index:
            return self._check_invoice_status(state, upload_index)

        if invoice_xml and seller_cui:
            return self._submit_invoice(state, invoice_xml, seller_cui)
        else:
            # Determine if B2B or B2C based on intent
            invoice_type = "B2B" if "b2b" in detected_intent else "B2C" if "b2c" in detected_intent else None
            return self._provide_guidance(state, invoice_type)

    def _submit_invoice(self, state: BaseAgentState, invoice_xml: str, seller_cui: str) -> dict[str, Any]:
        """Submit invoice to E-Factura system.

        Args:
            state: Current agent state
            invoice_xml: Invoice XML content
            seller_cui: Seller CUI

        Returns:
            State updates with submission result
        """
        shared_context = state.get("shared_context", {})

        result = mock_efactura_submit(invoice_xml, seller_cui)

        if result["status"] == "success":
            context_message = (
                f"Invoice submitted successfully to E-Factura system. Present these details:\n"
                f"- Upload index: {result['upload_index']}\n"
                f"- Validation status: {result['validation_status']}\n"
                f"- Timestamp: {result['timestamp']}\n"
                f"- Message: {result['message']}\n"
                f"Explain that they can check the status using the upload index."
            )
            workflow_status = "completed"
        else:
            context_message = f"Invoice submission failed: {result.get('message', 'Unknown error')}. Explain what went wrong and offer to help retry."
            workflow_status = "error"

        response = self.llm.invoke([
            SystemMessage(content=EFACTURA_AGENT_SYSTEM_PROMPT),
            *state["messages"],
            SystemMessage(content=context_message),
        ])

        return {
            "messages": [response],
            "shared_context": {
                **shared_context,
                "efactura_status": result["status"],
                "efactura_upload_index": result.get("upload_index"),
            },
            "current_agent": "efactura",
            "workflow_status": workflow_status,
        }

    def _check_invoice_status(self, state: BaseAgentState, upload_index: str) -> dict[str, Any]:
        """Check status of a submitted invoice.

        Args:
            state: Current agent state
            upload_index: Upload index to check

        Returns:
            State updates with status
        """
        shared_context = state.get("shared_context", {})

        result = mock_efactura_status(upload_index)

        # Use LLM to present the status
        context_parts = [
            f"Invoice status check completed for upload index {upload_index}:",
            f"- Status: {result['status']}",
            f"- Processing date: {result['processing_date']}",
        ]

        if result.get("errors"):
            context_parts.append(f"- Errors found: {', '.join(result['errors'])}")
        else:
            context_parts.append("- No errors")

        context_parts.append("Present this information clearly to the user and offer further assistance.")

        response = self.llm.invoke([
            SystemMessage(content=EFACTURA_AGENT_SYSTEM_PROMPT),
            *state["messages"],
            SystemMessage(content="\n".join(context_parts)),
        ])

        return {
            "messages": [response],
            "shared_context": {
                **shared_context,
                "efactura_check_status": result["status"],
            },
            "current_agent": "efactura",
            "workflow_status": "completed",
        }

    def _provide_guidance(self, state: BaseAgentState, invoice_type: str | None) -> dict[str, Any]:
        """Provide guidance on E-Factura using LLM.

        Args:
            state: Current agent state
            invoice_type: B2B or B2C if determined

        Returns:
            State updates with guidance
        """
        shared_context = state.get("shared_context", {})

        # Build context based on invoice type
        context_parts = ["E-Factura system information:"]

        if invoice_type == "B2B":
            context_parts.extend([
                "User is asking about B2B (Business to Business) invoicing.",
                "B2B e-invoicing is mandatory for VAT-registered companies in Romania.",
                "Required information: seller CUI, buyer CUI, party names and addresses, product/service details (quantity, price, VAT), invoice number and date.",
                "Ask if they want to issue a B2B invoice now.",
            ])
        elif invoice_type == "B2C":
            context_parts.extend([
                "User is asking about B2C (Business to Consumer) invoicing.",
                "B2C is for invoices to individuals (natural persons).",
                "Required information: seller CUI, buyer details (name, address), product/service details, invoice number and date.",
                "Ask if they want to issue a B2C invoice now.",
            ])
        else:
            context_parts.extend([
                "E-Factura is Romania's national electronic invoicing system.",
                "Types: B2B (between companies, mandatory for VAT payers) and B2C (to individuals).",
                "Services available: issue electronic invoice, check existing invoice status, information about E-Factura obligations.",
                "Ask how you can help them.",
            ])

        response = self.llm.invoke([
            SystemMessage(content=EFACTURA_AGENT_SYSTEM_PROMPT),
            SystemMessage(content="\n".join(context_parts)),
            *state["messages"],
        ])

        return {
            "messages": [response],
            "current_agent": "efactura",
            "shared_context": {
                **shared_context,
                "invoice_type": invoice_type,
                "awaiting_invoice_data": True,
            },
            "workflow_status": "in_progress",
        }


_efactura_agent = EFacturaAgent()


def efactura_node(state: BaseAgentState) -> dict[str, Any]:
    """LangGraph node function for E-Factura agent."""
    return _efactura_agent.process(state)
