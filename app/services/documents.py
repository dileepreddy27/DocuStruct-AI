import csv
import io
import json
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Document, DocumentStatus, Extraction, Review, ReviewStatus
from app.services.extraction import ExtractionFailure, ExtractionPipeline
from app.services.storage import ObjectStorage


class DocumentService:
    def __init__(
        self, db: Session, storage: ObjectStorage, pipeline: ExtractionPipeline, settings: Settings
    ):
        self.db = db
        self.storage = storage
        self.pipeline = pipeline
        self.settings = settings

    def create_and_process(
        self, filename: str, content_type: str, content: bytes, schema_name: str
    ) -> Document:
        if not filename.lower().endswith(".pdf") or content_type not in {
            "application/pdf",
            "application/octet-stream",
        }:
            raise ExtractionFailure("UNSUPPORTED_MEDIA_TYPE", "Only PDF uploads are accepted")
        if not content or len(content) > self.settings.max_upload_bytes:
            raise ExtractionFailure(
                "INVALID_SIZE", f"PDF must be between 1 and {self.settings.max_upload_bytes} bytes"
            )
        document_id = str(uuid.uuid4())
        safe_filename = filename.replace("/", "_").replace("\\", "_")
        key = f"{document_id}/{safe_filename}"
        stored = self.storage.put(key, content)
        document = Document(
            id=document_id,
            filename=filename,
            content_type="application/pdf",
            storage_key=stored.key,
            sha256=stored.sha256,
            schema_name=schema_name,
            status=DocumentStatus.processing,
        )
        self.db.add(document)
        self.db.commit()
        try:
            result = self.pipeline.run(content, schema_name)
            extraction = Extraction(
                document_id=document.id,
                provider=result.structured.provider,
                text_method=result.text.method,
                raw_text=result.text.text,
                data=result.structured.data,
                validation_errors=result.validation_errors,
                field_confidence=result.structured.field_confidence,
                confidence=result.confidence,
            )
            self.db.add(extraction)
            needs_review = (
                bool(result.validation_errors)
                or result.confidence < self.settings.review_confidence_threshold
            )
            if needs_review:
                reasons = []
                if result.validation_errors:
                    reasons.append(f"{len(result.validation_errors)} schema validation error(s)")
                if result.confidence < self.settings.review_confidence_threshold:
                    reasons.append(f"confidence {result.confidence:.0%} is below threshold")
                self.db.add(Review(document_id=document.id, reason="; ".join(reasons)))
                document.status = DocumentStatus.review_required
            else:
                document.status = DocumentStatus.completed
            self.db.commit()
        except ExtractionFailure as exc:
            document.status = DocumentStatus.failed
            document.error_code = exc.code
            document.error_message = str(exc)
            self.db.commit()
        self.db.refresh(document)
        return document

    def list_documents(self) -> list[Document]:
        return list(self.db.scalars(select(Document).order_by(Document.created_at.desc())).all())

    def list_pending_reviews(self) -> list[Document]:
        statement = (
            select(Document)
            .join(Review)
            .where(Review.status == ReviewStatus.pending)
            .order_by(Document.created_at)
        )
        return list(self.db.scalars(statement).all())

    def decide_review(
        self, document: Document, reviewer: str, corrected_data: dict | None
    ) -> Document:
        if not document.review or document.review.status != ReviewStatus.pending:
            raise ValueError("Document has no pending review")
        if corrected_data is not None:
            from jsonschema import Draft202012Validator, FormatChecker

            from app.domain.schemas import SCHEMAS

            errors = list(
                Draft202012Validator(
                    SCHEMAS[document.schema_name], format_checker=FormatChecker()
                ).iter_errors(corrected_data)
            )
            if errors:
                raise ValueError(
                    "Corrected data does not satisfy the document schema: " + errors[0].message
                )
            document.review.corrected_data = corrected_data
            document.review.status = ReviewStatus.corrected
        else:
            if document.extraction and document.extraction.validation_errors:
                raise ValueError("Invalid extraction must be corrected before approval")
            document.review.status = ReviewStatus.approved
        document.review.reviewer = reviewer
        document.review.reviewed_at = datetime.now(UTC)
        document.status = DocumentStatus.completed
        self.db.commit()
        self.db.refresh(document)
        return document

    @staticmethod
    def effective_data(document: Document) -> dict:
        if document.review and document.review.corrected_data is not None:
            return document.review.corrected_data
        if document.extraction:
            return document.extraction.data
        raise ValueError("Document has no extraction to export")

    def export_json(self, document: Document) -> bytes:
        return json.dumps(self.effective_data(document), indent=2).encode()

    def export_csv(self, document: Document) -> bytes:
        data = self.effective_data(document)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["field", "value"])
        for key, value in data.items():
            writer.writerow([key, json.dumps(value) if isinstance(value, dict | list) else value])
        return output.getvalue().encode()
