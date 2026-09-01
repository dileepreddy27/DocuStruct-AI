import re
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from typing import Any, Protocol

import fitz
from jsonschema import Draft202012Validator, FormatChecker

from app.domain.schemas import SCHEMAS


class ExtractionFailure(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass
class TextResult:
    text: str
    method: str


@dataclass
class StructuredResult:
    data: dict[str, Any]
    field_confidence: dict[str, float]
    provider: str


@dataclass
class PipelineResult:
    text: TextResult
    structured: StructuredResult
    validation_errors: list[dict[str, str]]
    confidence: float


class StructuredExtractionProvider(Protocol):
    name: str

    def extract(self, text: str, schema: dict[str, Any]) -> StructuredResult: ...


class PdfTextExtractor:
    def extract(self, content: bytes) -> TextResult:
        try:
            document = fitz.open(stream=content, filetype="pdf")
        except Exception as exc:
            raise ExtractionFailure(
                "INVALID_PDF", "The uploaded file is not a readable PDF"
            ) from exc
        text = "\n".join(page.get_text("text") for page in document).strip()
        if text:
            return TextResult(text=text, method="embedded_text")
        try:
            import pytesseract
            from PIL import Image
        except ImportError as exc:
            raise ExtractionFailure(
                "OCR_UNAVAILABLE", "No embedded text and OCR dependencies are unavailable"
            ) from exc
        pages: list[str] = []
        for page in document:
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            image = Image.open(BytesIO(pixmap.tobytes("png")))
            pages.append(pytesseract.image_to_string(image))
        text = "\n".join(pages).strip()
        if not text:
            raise ExtractionFailure(
                "NO_TEXT", "Neither embedded text nor OCR produced readable text"
            )
        return TextResult(text=text, method="ocr")


class HeuristicInvoiceProvider:
    name = "heuristic-v1"

    PATTERNS = {
        "invoice_number": r"Invoice\s*(?:Number|No\.?|#)\s*[:#]?\s*([A-Z0-9-]+)",
        "vendor": r"Vendor\s*:\s*(.+)",
        "invoice_date": r"Invoice\s*Date\s*:\s*(\d{4}-\d{2}-\d{2})",
        "due_date": r"Due\s*Date\s*:\s*(\d{4}-\d{2}-\d{2})",
        "currency": r"Currency\s*:\s*([A-Z]{3})",
        "subtotal": r"Subtotal\s*:\s*\$?([\d,]+\.\d{2})",
        "tax": r"Tax\s*:\s*\$?([\d,]+\.\d{2})",
        "total": r"(?m)^(?:Grand\s+)?Total\s*:\s*\$?([\d,]+\.\d{2})",
    }

    def extract(self, text: str, schema: dict[str, Any]) -> StructuredResult:
        data: dict[str, Any] = {"line_items": []}
        confidence: dict[str, float] = {}
        for field, pattern in self.PATTERNS.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if not match:
                continue
            value: Any = match.group(1).strip()
            if field in {"subtotal", "tax", "total"}:
                value = float(value.replace(",", ""))
            elif field in {"invoice_date", "due_date"}:
                datetime.strptime(value, "%Y-%m-%d")
            elif field == "currency":
                value = value.upper()
            data[field] = value
            confidence[field] = 0.97
        item_pattern = re.compile(
            r"ITEM\s*\|\s*(.+?)\s*\|\s*([\d.]+)\s*\|\s*\$?([\d.]+)\s*\|\s*\$?([\d.]+)",
            re.IGNORECASE,
        )
        for match in item_pattern.finditer(text):
            data["line_items"].append(
                {
                    "description": match.group(1).strip(),
                    "quantity": float(match.group(2)),
                    "unit_price": float(match.group(3)),
                    "amount": float(match.group(4)),
                }
            )
        confidence["line_items"] = 0.94 if data["line_items"] else 0.45
        return StructuredResult(data=data, field_confidence=confidence, provider=self.name)


class ExtractionPipeline:
    def __init__(
        self, provider: StructuredExtractionProvider, text_extractor: PdfTextExtractor | None = None
    ):
        self.provider = provider
        self.text_extractor = text_extractor or PdfTextExtractor()

    def run(self, content: bytes, schema_name: str) -> PipelineResult:
        schema = SCHEMAS.get(schema_name)
        if not schema:
            raise ExtractionFailure("UNKNOWN_SCHEMA", f"Schema '{schema_name}' is not supported")
        text = self.text_extractor.extract(content)
        structured = self.provider.extract(text.text, schema)
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        errors = [
            {"path": ".".join(str(part) for part in error.path) or "$", "message": error.message}
            for error in sorted(
                validator.iter_errors(structured.data), key=lambda item: list(item.path)
            )
        ]
        required = schema.get("required", [])
        required_scores = [structured.field_confidence.get(field, 0.0) for field in required]
        confidence = sum(required_scores) / len(required_scores) if required_scores else 0.0
        if errors:
            confidence = min(confidence, 0.69)
        return PipelineResult(
            text=text,
            structured=structured,
            validation_errors=errors,
            confidence=round(confidence, 3),
        )
