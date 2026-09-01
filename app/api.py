from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_document_service
from app.models import Document
from app.schemas import BatchResponse, DocumentView, ReviewDecision
from app.services.documents import DocumentService
from app.services.extraction import ExtractionFailure

router = APIRouter(prefix="/api/v1")


def find_document(document_id: str, db: Session) -> Document:
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(
            status_code=404, detail={"code": "DOCUMENT_NOT_FOUND", "message": "Document not found"}
        )
    return document


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/documents", response_model=DocumentView, status_code=status.HTTP_201_CREATED)
def upload_document(
    file: Annotated[UploadFile, File(description="PDF document")],
    schema_name: Annotated[str, Form()] = "invoice",
    service: DocumentService = Depends(get_document_service),
) -> Document:
    try:
        return service.create_and_process(
            file.filename or "upload.pdf", file.content_type or "", file.file.read(), schema_name
        )
    except ExtractionFailure as exc:
        raise HTTPException(
            status_code=422, detail={"code": exc.code, "message": str(exc)}
        ) from exc


@router.post(
    "/documents/batch", response_model=BatchResponse, status_code=status.HTTP_207_MULTI_STATUS
)
def upload_batch(
    files: Annotated[list[UploadFile], File(description="Up to 20 PDF documents")],
    schema_name: Annotated[str, Form()] = "invoice",
    service: DocumentService = Depends(get_document_service),
) -> dict:
    if len(files) > 20:
        raise HTTPException(
            status_code=422,
            detail={"code": "BATCH_TOO_LARGE", "message": "Maximum batch size is 20"},
        )
    accepted, rejected = [], []
    for file in files:
        try:
            accepted.append(
                service.create_and_process(
                    file.filename or "upload.pdf",
                    file.content_type or "",
                    file.file.read(),
                    schema_name,
                )
            )
        except ExtractionFailure as exc:
            rejected.append(
                {"filename": file.filename or "upload", "code": exc.code, "message": str(exc)}
            )
    return {"accepted": accepted, "rejected": rejected}


@router.get("/documents", response_model=list[DocumentView])
def documents(service: DocumentService = Depends(get_document_service)) -> list[Document]:
    return service.list_documents()


@router.get("/documents/{document_id}", response_model=DocumentView)
def document(document_id: str, db: Session = Depends(get_db)) -> Document:
    return find_document(document_id, db)


@router.get("/reviews", response_model=list[DocumentView])
def reviews(service: DocumentService = Depends(get_document_service)) -> list[Document]:
    return service.list_pending_reviews()


@router.post("/reviews/{document_id}", response_model=DocumentView)
def review_document(
    document_id: str,
    decision: ReviewDecision,
    db: Session = Depends(get_db),
    service: DocumentService = Depends(get_document_service),
) -> Document:
    document = find_document(document_id, db)
    try:
        return service.decide_review(document, decision.reviewer, decision.corrected_data)
    except ValueError as exc:
        raise HTTPException(
            status_code=409, detail={"code": "REVIEW_CONFLICT", "message": str(exc)}
        ) from exc


@router.get("/documents/{document_id}/export.{format}")
def export_document(
    document_id: str,
    format: str,
    db: Session = Depends(get_db),
    service: DocumentService = Depends(get_document_service),
) -> Response:
    document = find_document(document_id, db)
    if document.status.value != "completed":
        raise HTTPException(
            status_code=409,
            detail={"code": "NOT_EXPORTABLE", "message": "Complete review before export"},
        )
    if format == "json":
        body, media = service.export_json(document), "application/json"
    elif format == "csv":
        body, media = service.export_csv(document), "text/csv"
    else:
        raise HTTPException(status_code=404, detail="Export format not supported")
    return Response(
        body,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{document_id}.{format}"'},
    )
