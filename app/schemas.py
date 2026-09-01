from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models import DocumentStatus, ReviewStatus


class ExtractionView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    provider: str
    text_method: str
    data: dict[str, Any]
    validation_errors: list[Any]
    field_confidence: dict[str, float]
    confidence: float


class ReviewView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    status: ReviewStatus
    reason: str
    corrected_data: dict[str, Any] | None
    reviewer: str | None
    reviewed_at: datetime | None


class DocumentView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    filename: str
    status: DocumentStatus
    schema_name: str
    error_code: str | None
    error_message: str | None
    created_at: datetime
    extraction: ExtractionView | None = None
    review: ReviewView | None = None


class ReviewDecision(BaseModel):
    reviewer: str = Field(min_length=1, max_length=120)
    corrected_data: dict[str, Any] | None = None


class BatchResponse(BaseModel):
    accepted: list[DocumentView]
    rejected: list[dict[str, str]]
