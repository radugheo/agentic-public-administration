"""Mock implementations of external systems (ANAF SPV, Ghiseul.ro, E-Factura)."""

from typing import Optional
from dataclasses import dataclass
from datetime import datetime
import uuid


@dataclass
class ANAFSPVResponse:
    """Mock ANAF SPV system response."""

    success: bool
    response_code: str
    message: str
    data: Optional[dict] = None


@dataclass
class GhiseulResponse:
    """Mock Ghiseul.ro system response."""

    success: bool
    payment_code: str
    redirect_url: Optional[str] = None
    message: Optional[str] = None


@dataclass
class EFacturaResponse:
    """Mock RO E-Factura system response."""

    success: bool
    state_message: str
    download_id: Optional[str] = None
    errors: list[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class MockANAFSPV:
    """Mock ANAF SPV external system.

    Simulates the ANAF SPV (Spatiul Privat Virtual) portal for
    tax declarations and certificate requests.
    """

    def authenticate(self, certificate_path: str, password: str) -> ANAFSPVResponse:
        """Authenticate with ANAF SPV using digital certificate.

        Args:
            certificate_path: Path to digital certificate
            password: Certificate password

        Returns:
            Authentication response
        """
        return ANAFSPVResponse(
            success=True,
            response_code="AUTH_OK",
            message="Autentificare reusita",
            data={
                "session_id": f"anaf_session_{uuid.uuid4().hex[:16]}",
                "user_cui": "RO12345678",
                "valid_until": datetime.now().isoformat(),
            },
        )

    def submit_declaration(
        self, declaration_type: str, xml_content: str
    ) -> ANAFSPVResponse:
        """Submit a tax declaration.

        Args:
            declaration_type: Type of declaration (D212, etc.)
            xml_content: XML content of the declaration

        Returns:
            Submission response
        """
        return ANAFSPVResponse(
            success=True,
            response_code="DECL_SUBMITTED",
            message=f"Declaratia {declaration_type} a fost depusa",
            data={
                "submission_id": f"{declaration_type}-{datetime.now().year}-{uuid.uuid4().hex[:6].upper()}",
                "timestamp": datetime.now().isoformat(),
            },
        )

    def get_fiscal_certificate(
        self, cnp_cui: str, certificate_type: str
    ) -> ANAFSPVResponse:
        """Request a fiscal certificate.

        Args:
            cnp_cui: CNP or CUI of the taxpayer
            certificate_type: Type of certificate requested

        Returns:
            Certificate response
        """
        return ANAFSPVResponse(
            success=True,
            response_code="CERT_GENERATED",
            message="Certificat fiscal generat",
            data={
                "certificate_id": f"CERT-{datetime.now().year}-{uuid.uuid4().hex[:6].upper()}",
                "valid_until": "2024-12-31",
                "download_url": f"mock://anaf.ro/certificates/CERT-{uuid.uuid4().hex[:8]}.pdf",
            },
        )

    def check_declaration_status(self, submission_id: str) -> ANAFSPVResponse:
        """Check status of a submitted declaration.

        Args:
            submission_id: Submission ID to check

        Returns:
            Status response
        """
        return ANAFSPVResponse(
            success=True,
            response_code="STATUS_OK",
            message="Declaratia a fost procesata cu succes",
            data={
                "submission_id": submission_id,
                "status": "processed",
                "processing_date": datetime.now().isoformat(),
            },
        )


class MockGhiseulRo:
    """Mock Ghiseul.ro external system.

    Simulates the Ghiseul.ro payment platform for tax payments.
    """

    def initiate_payment(
        self, amount: float, payment_type: str, reference: str
    ) -> GhiseulResponse:
        """Initiate a payment.

        Args:
            amount: Payment amount in RON
            payment_type: Type of payment
            reference: Payment reference

        Returns:
            Payment initiation response
        """
        payment_code = f"GH-PAY-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        return GhiseulResponse(
            success=True,
            payment_code=payment_code,
            redirect_url=f"mock://ghiseul.ro/pay/{reference}",
            message=f"Plata de {amount} RON initiata cu succes",
        )

    def check_payment_status(self, payment_code: str) -> GhiseulResponse:
        """Check payment status.

        Args:
            payment_code: Payment code to check

        Returns:
            Payment status response
        """
        return GhiseulResponse(
            success=True,
            payment_code=payment_code,
            message="Plata a fost confirmata",
        )

    def get_payment_receipt(self, payment_code: str) -> GhiseulResponse:
        """Get payment receipt.

        Args:
            payment_code: Payment code

        Returns:
            Receipt response
        """
        return GhiseulResponse(
            success=True,
            payment_code=payment_code,
            redirect_url=f"mock://ghiseul.ro/receipt/{payment_code}.pdf",
            message="Chitanta disponibila pentru descarcare",
        )


class MockEFacturaSystem:
    """Mock RO E-Factura external system.

    Simulates the Romanian E-Factura electronic invoicing system.
    """

    def upload_invoice(self, xml_content: str, cif: str) -> EFacturaResponse:
        """Upload an invoice to E-Factura.

        Args:
            xml_content: Invoice XML content
            cif: Seller CIF/CUI

        Returns:
            Upload response
        """
        return EFacturaResponse(
            success=True,
            state_message="nok",  # Initially not processed
            download_id=f"EF-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}",
        )

    def check_status(self, download_id: str) -> EFacturaResponse:
        """Check invoice processing status.

        Args:
            download_id: Download ID to check

        Returns:
            Status response
        """
        return EFacturaResponse(
            success=True,
            state_message="ok",
            download_id=download_id,
        )

    def download_invoice(self, download_id: str) -> bytes:
        """Download processed invoice.

        Args:
            download_id: Download ID

        Returns:
            Invoice XML content
        """
        return b"<?xml version='1.0'?><Invoice>Mock invoice content</Invoice>"

    def get_messages(self, cif: str, days: int = 60) -> list[dict]:
        """Get E-Factura messages for a company.

        Args:
            cif: Company CIF
            days: Number of days to look back

        Returns:
            List of messages
        """
        return [
            {
                "message_id": f"MSG-{uuid.uuid4().hex[:8]}",
                "type": "FACTURA PRIMITA",
                "upload_index": f"EF-{uuid.uuid4().hex[:10]}",
                "date": datetime.now().isoformat(),
            }
        ]


# Singleton instances
mock_anaf_spv = MockANAFSPV()
mock_ghiseul = MockGhiseulRo()
mock_efactura_system = MockEFacturaSystem()
