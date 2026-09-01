from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.services.documents import DocumentService
from app.services.extraction import ExtractionPipeline, HeuristicInvoiceProvider
from app.services.storage import LocalObjectStorage


def get_document_service(
    db: Session = Depends(get_db), settings: Settings = Depends(get_settings)
) -> DocumentService:
    storage = LocalObjectStorage(settings.storage_root)
    provider = HeuristicInvoiceProvider()
    return DocumentService(db, storage, ExtractionPipeline(provider), settings)
