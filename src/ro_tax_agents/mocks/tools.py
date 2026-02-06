"""Mock implementations of SPV, Ghiseul.ro, and other tools."""

from typing import Optional
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
import uuid

from ro_tax_agents.models.payments import PaymentRequest, PaymentResult
from ro_tax_agents.models.documents import OCRResult


@dataclass
class SPVSubmissionResult:
    """Result from SPV form submission."""

    status: str
    submission_id: str
    message: str
    timestamp: str


def mock_spv_login(username: str, password: str) -> dict:
    """Mock SPV (ANAF) login.

    Args:
        username: SPV username
        password: SPV password

    Returns:
        Login result with session token
    """
    return {
        "success": True,
        "session_token": f"mock_session_{uuid.uuid4().hex[:16]}",
        "user_cui": "RO12345678",
        "expires_at": "2024-12-31T23:59:59",
    }


def mock_spv_submit_d212(d212_data: dict) -> SPVSubmissionResult:
    """Mock D212 form submission to SPV.

    Args:
        d212_data: D212 form data

    Returns:
        Submission result
    """
    return SPVSubmissionResult(
        status="success",
        submission_id=f"D212-{uuid.uuid4().hex[:10].upper()}",
        message="Declaratia D212 a fost depusa cu succes",
        timestamp=datetime.now().isoformat(),
    )


def mock_spv_register_contract(contract_data: dict) -> dict:
    """Mock rental contract registration with ANAF.

    Args:
        contract_data: Contract registration data

    Returns:
        Registration result
    """
    return {
        "status": "success",
        "registration_number": f"CONTR-{uuid.uuid4().hex[:8].upper()}",
        "registration_date": datetime.now().isoformat(),
        "message": "Contractul de inchiriere a fost inregistrat",
    }


def mock_ghiseul_payment(request: PaymentRequest) -> PaymentResult:
    """Mock Ghiseul.ro payment processing.

    Args:
        request: Payment request data

    Returns:
        Payment result
    """
    return PaymentResult(
        status="success",
        transaction_id=f"GH-{uuid.uuid4().hex[:12].upper()}",
        timestamp=datetime.now(),
        message=f"Plata de {request.amount} RON a fost procesata cu succes",
        redirect_url=f"https://ghiseul.ro/payment/{uuid.uuid4().hex[:8]}",
    )


def mock_ocr_document(document_path: str) -> OCRResult:
    """Mock OCR document processing.

    Args:
        document_path: Path to the document

    Returns:
        OCR result with extracted data
    """
    # Simulate different document types based on path
    document_path_lower = document_path.lower()

    if "d212" in document_path_lower:
        return OCRResult(
            document_type="D212_FORM",
            extracted_data={
                "fiscal_year": 2024,
                "total_income": 150000.00,
                "total_expenses": 45000.00,
                "cnp": "1850101123456",
            },
            confidence=0.94,
        )
    elif "contract" in document_path_lower:
        return OCRResult(
            document_type="RENTAL_CONTRACT",
            extracted_data={
                "landlord_name": "Ion Popescu",
                "tenant_name": "Maria Ionescu",
                "monthly_rent": 500.00,
                "property_address": "Str. Exemplu nr. 1, Bucuresti",
                "contract_start_date": "2024-01-01",
                "contract_end_date": "2024-12-31",
            },
            confidence=0.91,
        )
    elif "factura" in document_path_lower or "invoice" in document_path_lower:
        return OCRResult(
            document_type="INVOICE",
            extracted_data={
                "invoice_number": "FA-2024-001",
                "seller_cui": "RO12345678",
                "buyer_cui": "RO87654321",
                "total_amount": 1190.00,
                "vat_amount": 190.00,
                "invoice_date": "2024-01-15",
            },
            confidence=0.96,
        )
    else:
        return OCRResult(
            document_type="UNKNOWN",
            extracted_data={},
            confidence=0.50,
        )


def mock_efactura_submit(invoice_xml: str, seller_cui: str) -> dict:
    """Mock E-Factura XML submission.

    Args:
        invoice_xml: Invoice XML content
        seller_cui: Seller CUI

    Returns:
        Submission result
    """
    return {
        "status": "success",
        "upload_index": f"EF-{uuid.uuid4().hex[:10].upper()}",
        "message": "Factura a fost incarcata in sistemul E-Factura",
        "validation_status": "valid",
        "timestamp": datetime.now().isoformat(),
    }


def mock_efactura_status(upload_index: str) -> dict:
    """Mock E-Factura status check.

    Args:
        upload_index: Upload index to check

    Returns:
        Status result
    """
    return {
        "upload_index": upload_index,
        "status": "processed",
        "state_message": "ok",
        "processing_date": datetime.now().isoformat(),
        "errors": [],
    }


def mock_fiscal_certificate_request(cnp_cui: str, certificate_type: str) -> dict:
    """Mock fiscal certificate request.

    Args:
        cnp_cui: CNP or CUI
        certificate_type: Type of certificate

    Returns:
        Certificate request result
    """
    return {
        "status": "success",
        "request_id": f"CERT-{uuid.uuid4().hex[:8].upper()}",
        "certificate_type": certificate_type,
        "estimated_completion": "24 hours",
        "message": "Cererea de certificat fiscal a fost inregistrata",
    }
