import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class DocumentStatus(str, enum.Enum):
    queued = "queued"
    processing = "processing"
    completed = "completed"
    review_required = "review_required"
    failed = "failed"


class ReviewStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    corrected = "corrected"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100), default="application/pdf")
    storage_key: Mapped[str] = mapped_column(String(500), unique=True)
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus), default=DocumentStatus.queued
    )
    schema_name: Mapped[str] = mapped_column(String(80), default="invoice")
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    extraction: Mapped["Extraction | None"] = relationship(
        back_populates="document", cascade="all, delete-orphan", uselist=False
    )
    review: Mapped["Review | None"] = relationship(
        back_populates="document", cascade="all, delete-orphan", uselist=False
    )


class Extraction(Base):
    __tablename__ = "extractions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), unique=True, index=True)
    provider: Mapped[str] = mapped_column(String(80))
    text_method: Mapped[str] = mapped_column(String(40))
    raw_text: Mapped[str] = mapped_column(Text)
    data: Mapped[dict] = mapped_column(JSON)
    validation_errors: Mapped[list] = mapped_column(JSON, default=list)
    field_confidence: Mapped[dict] = mapped_column(JSON, default=dict)
    confidence: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    document: Mapped[Document] = relationship(back_populates="extraction")


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), unique=True, index=True)
    status: Mapped[ReviewStatus] = mapped_column(Enum(ReviewStatus), default=ReviewStatus.pending)
    reason: Mapped[str] = mapped_column(Text)
    corrected_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    reviewer: Mapped[str | None] = mapped_column(String(120), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    document: Mapped[Document] = relationship(back_populates="review")
