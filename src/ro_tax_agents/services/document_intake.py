"""Document Intake Service - OCR and document validation."""

from typing import Any
from langchain_core.messages import AIMessage

from ro_tax_agents.state.base import BaseAgentState
from ro_tax_agents.mocks.tools import mock_ocr_document


class DocumentIntakeService:
    """OCR and document validation service.

    This service processes uploaded documents, extracts data using OCR,
    and validates the extracted information.
    """

    def process(self, state: BaseAgentState) -> dict[str, Any]:
        """Extract and validate document content.

        Args:
            state: Current agent state

        Returns:
            State updates with extracted document data
        """
        shared_context = state.get("shared_context", {})
        document_path = shared_context.get("pending_document_path")

        if not document_path:
            return {
                "messages": [AIMessage(content="Nu a fost furnizat niciun document pentru procesare.")],
                "workflow_status": "error",
                "error_message": "Missing document path",
            }

        # Call mock OCR
        ocr_result = mock_ocr_document(document_path)

        # Validate extracted data based on document type
        validated_data = self._validate_document(ocr_result.document_type, ocr_result.extracted_data)

        # Build response message
        if ocr_result.confidence >= 0.8:
            message = f"Document procesat cu succes: {ocr_result.document_type}\n"
            message += f"Incredere OCR: {ocr_result.confidence * 100:.0f}%\n"
            message += "Date extrase:\n"
            for key, value in ocr_result.extracted_data.items():
                message += f"  - {key}: {value}\n"
        else:
            message = f"Document procesat cu incredere scazuta ({ocr_result.confidence * 100:.0f}%). "
            message += "Va rugam verificati datele extrase."

        return {
            "shared_context": {
                **shared_context,
                "extracted_document_data": ocr_result.extracted_data,
                "document_type": ocr_result.document_type,
                "ocr_confidence": ocr_result.confidence,
                "document_validated": validated_data.get("is_valid", False),
                "validation_errors": validated_data.get("errors", []),
            },
            "messages": [AIMessage(content=message)],
        }

    def _validate_document(self, document_type: str, extracted_data: dict) -> dict:
        """Validate extracted document data.

        Args:
            document_type: Type of document
            extracted_data: Extracted data fields

        Returns:
            Validation result with is_valid flag and any errors
        """
        errors = []

        if document_type == "D212_FORM":
            # Validate D212 specific fields
            if "fiscal_year" not in extracted_data:
                errors.append("Anul fiscal lipseste")
            if "total_income" not in extracted_data:
                errors.append("Venitul total lipseste")

        elif document_type == "RENTAL_CONTRACT":
            # Validate rental contract fields
            required_fields = ["landlord_name", "tenant_name", "monthly_rent", "property_address"]
            for field in required_fields:
                if field not in extracted_data:
                    errors.append(f"Campul {field} lipseste")

        elif document_type == "INVOICE":
            # Validate invoice fields
            required_fields = ["invoice_number", "seller_cui", "total_amount"]
            for field in required_fields:
                if field not in extracted_data:
                    errors.append(f"Campul {field} lipseste")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
        }

    def __call__(self, state: BaseAgentState) -> dict[str, Any]:
        """Make the service callable as a LangGraph node."""
        return self.process(state)


# Singleton instance
document_intake_service = DocumentIntakeService()
