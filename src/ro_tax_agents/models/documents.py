"""Document-related data models."""

from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


class DocumentMetadata(BaseModel):
    """Metadata for uploaded documents."""

    document_id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    document_type: Optional[str] = Field(default=None, description="Detected document type")
    upload_timestamp: datetime = Field(
        default_factory=datetime.now, description="Upload timestamp"
    )
    file_size: Optional[int] = Field(default=None, description="File size in bytes")
    mime_type: Optional[str] = Field(default=None, description="MIME type")


class OCRResult(BaseModel):
    """Result from OCR document processing."""

    document_type: str = Field(..., description="Detected document type")
    extracted_data: dict[str, Any] = Field(
        default_factory=dict, description="Extracted data fields"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="OCR confidence score")
    raw_text: Optional[str] = Field(default=None, description="Raw extracted text")
    processing_time_ms: Optional[int] = Field(
        default=None, description="Processing time in milliseconds"
    )
