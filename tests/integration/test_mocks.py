"""Integration tests for mock layer."""

import pytest
from decimal import Decimal

from ro_tax_agents.mocks.tools import (
    mock_spv_login,
    mock_spv_submit_d212,
    mock_spv_register_contract,
    mock_ghiseul_payment,
    mock_ocr_document,
    mock_efactura_submit,
    mock_efactura_status,
)
from ro_tax_agents.mocks.uipath_sdk import mock_uipath
from ro_tax_agents.models.payments import PaymentRequest


class TestSPVMocks:
    """Tests for SPV (ANAF) mock implementations."""

    def test_spv_login_returns_session(self):
        """SPV login should return a valid session."""
        result = mock_spv_login("test_user", "test_pass")

        assert result["success"] == True
        assert "session_token" in result
        assert result["session_token"].startswith("mock_session_")

    def test_spv_submit_d212_success(self):
        """D212 submission should return success."""
        d212_data = {
            "fiscal_year": 2024,
            "income": 150000,
            "expenses": 30000,
        }

        result = mock_spv_submit_d212(d212_data)

        assert result.status == "success"
        assert result.submission_id.startswith("D212-")
        assert "D212" in result.message

    def test_spv_register_contract(self):
        """Contract registration should return success."""
        contract_data = {
            "landlord_cnp": "1234567890123",
            "tenant_cnp": "1234567890124",
            "monthly_rent": 500,
        }

        result = mock_spv_register_contract(contract_data)

        assert result["status"] == "success"
        assert "registration_number" in result


class TestGhiseulMock:
    """Tests for Ghiseul.ro mock implementation."""

    def test_payment_processing(self):
        """Payment should be processed successfully."""
        request = PaymentRequest(
            amount=Decimal("1000.00"),
            payment_type="property_tax",
            reference_number="REF-123",
        )

        result = mock_ghiseul_payment(request)

        assert result.status == "success"
        assert result.transaction_id.startswith("GH-")
        assert "1000" in result.message


class TestOCRMock:
    """Tests for OCR mock implementation."""

    def test_ocr_d212_document(self):
        """D212 document should be recognized."""
        result = mock_ocr_document("document_d212.pdf")

        assert result.document_type == "D212_FORM"
        assert result.confidence >= 0.9
        assert "fiscal_year" in result.extracted_data

    def test_ocr_contract_document(self):
        """Contract document should be recognized."""
        result = mock_ocr_document("rental_contract.pdf")

        assert result.document_type == "RENTAL_CONTRACT"
        assert "monthly_rent" in result.extracted_data

    def test_ocr_invoice_document(self):
        """Invoice document should be recognized."""
        result = mock_ocr_document("factura_2024.pdf")

        assert result.document_type == "INVOICE"
        assert "invoice_number" in result.extracted_data


class TestEFacturaMock:
    """Tests for E-Factura mock implementation."""

    def test_efactura_submit(self):
        """E-Factura submission should succeed."""
        result = mock_efactura_submit("<Invoice>test</Invoice>", "RO12345678")

        assert result["status"] == "success"
        assert result["upload_index"].startswith("EF-")

    def test_efactura_status(self):
        """E-Factura status check should work."""
        result = mock_efactura_status("EF-TEST123")

        assert result["upload_index"] == "EF-TEST123"
        assert result["status"] == "processed"


class TestUiPathSDKMock:
    """Tests for UiPath SDK mock implementation."""

    def test_invoke_process(self):
        """Process invocation should return success."""
        result = mock_uipath.invoke_process("TaxCalculation", {"input": "test"})

        assert result["status"] == "completed"
        assert "process_id" in result

    def test_create_task(self):
        """Task creation should work."""
        task = mock_uipath.create_task(
            title="Review Document",
            task_catalog_name="DocumentReview",
            data={"document_id": "123"},
        )

        assert task.task_id is not None
        assert task.title == "Review Document"

    def test_queue_operations(self):
        """Queue operations should work."""
        item = mock_uipath.add_queue_item(
            queue_name="TaxProcessing",
            specific_content={"cnp": "1234567890123"},
        )

        assert item.item_id is not None
        assert item.queue_name == "TaxProcessing"

        items = mock_uipath.get_queue_items("TaxProcessing")
        assert len(items) >= 1

    def test_bucket_operations(self):
        """Bucket operations should work."""
        url = mock_uipath.upload_to_bucket(
            bucket_name="documents",
            file_name="test.pdf",
            content=b"test content",
        )

        assert "bucket://" in url

        content = mock_uipath.download_from_bucket("documents", "test.pdf")
        assert content == b"test content"

    def test_context_grounding(self):
        """Context grounding should return results."""
        results = mock_uipath.context_grounding(
            query="CAS contributions",
            index_name="tax_regulations",
            top_k=2,
        )

        assert len(results) == 2
        assert "content" in results[0]
        assert "score" in results[0]
