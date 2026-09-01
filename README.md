# DocuStruct AI

**A PDF-to-validated-data workflow that makes uncertain extraction visible before downstream systems trust it.**

DocuStruct AI is a recruiter-facing full-stack portfolio project built around a practical document-operations problem: PDFs are easy for people to read but unreliable as application inputs. The platform accepts individual or batch invoice PDFs, extracts embedded text with OCR fallback, maps content into structured fields, validates the result against JSON Schema, calculates confidence, and sends unsafe results to a human-review queue. Approved data exports as JSON or CSV.

> Portfolio status: production-minded architecture and local demo—not represented as production-ready. See [verification evidence](#verification-evidence) and [known limitations](#known-limitations).

## What this demonstrates

- **Python / FastAPI:** typed REST endpoints, OpenAPI, multipart upload, stable failures, and batch partial-success semantics.
- **PostgreSQL / SQLAlchemy / Alembic:** persisted document lifecycle, raw machine output, confidence, validation errors, and auditable corrections.
- **Document AI pipeline:** PyMuPDF text extraction, Tesseract OCR fallback, provider-based structured extraction, Draft 2020-12 JSON Schema validation, and field-level confidence.
- **Human-in-the-loop design:** invalid or low-confidence data cannot export until reviewed; corrections are independently validated.
- **Full-stack delivery:** responsive upload dashboard, Docker Compose, health checks, CI, tests, synthetic fixtures, and reproducible demo steps.

## Workflow

```text
PDF upload → object storage → text extraction → OCR fallback
           → structured provider → schema validation → confidence
           → completed → JSON / CSV
           └ review required → corrected or approved → export
```

The default `heuristic-v1` provider is deterministic and offline so the repository is testable without paid credentials. `StructuredExtractionProvider` is the seam for a hosted or local LLM adapter; no hosted LLM integration is claimed in this version.

Read the [architecture and lifecycle](docs/architecture.md) for the component diagram and design tradeoffs.

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,postgres,ocr]"
.\.venv\Scripts\python.exe scripts\generate_samples.py
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Then open `http://localhost:8000`. The two PDFs in `samples/` contain explicitly synthetic business data: one clean extraction and one intentionally incomplete document that enters review. For PostgreSQL, run `docker compose up --build`.

## API example

```bash
curl -F "file=@samples/synthetic-invoice-clean.pdf;type=application/pdf" \
  -F "schema_name=invoice" http://localhost:8000/api/v1/documents
```

See the [API guide](docs/api.md), interactive `/docs`, and [demo runbook](docs/demo.md).

## Repository map

```text
app/api.py                 HTTP contract and failure responses
app/services/documents.py lifecycle, review, and export orchestration
app/services/extraction.py PDF/OCR and provider-based extraction pipeline
app/services/storage.py   replaceable object-storage interface
app/domain/schemas.py      versionable JSON Schema definitions
app/web/                   accessible responsive dashboard
migrations/                PostgreSQL-compatible schema history
tests/                     unit, integration, quality, and failure-path tests
samples/                   safe synthetic demo PDFs
```

## Quality and security choices

- Upload size and PDF media type are bounded; filenames are isolated below generated storage keys.
- SHA-256 supports source integrity checks and future deduplication, but deduplication is not implemented.
- `.env.example` contains placeholders and non-secret development defaults.
- Machine output and reviewer correction remain separate for auditability.
- Exports are blocked for failed and pending-review documents.
- CI runs lint, tests with a coverage floor, a migration, and a container build.

## Verification evidence

| Claim | Status | Evidence |
|---|---|---|
| Unit and API integration tests | **Verified** | 7/7 passed; 92% application coverage on Python 3.11 |
| Extraction quality fixture | **Verified** | Synthetic clean invoice extracted `INV-2026-0042` and total `366.12`; regression test prevents `Subtotal`/`Total` collision |
| Review and export rules | **Verified** | Invalid document routed to review; schema-valid correction completed; pending review export blocked by tests |
| Static analysis and compilation | **Verified** | Ruff passed; `python -m compileall app` passed |
| SQLite migration | **Verified** | Alembic revision `0001` upgraded locally |
| Synthetic PDF generation | **Verified** | Two no-real-personal-data sample PDFs generated successfully |
| Docker configuration and image | **Verified** | Compose config parsed; application image built successfully with Tesseract |
| PostgreSQL container workflow | **Verified** | PostgreSQL and app became healthy; live upload, review routing, JSON export, and UI ran on host port 8001 |
| Browser UI | **Verified** | Home page rendered meaningful content, document statuses and export actions; no error overlay or browser console errors detected |
| OCR fallback on scanned PDF | **Not run** | Tesseract is installed in the image; no scanned-image quality fixture is included yet |
| GitHub Actions | **Rerun pending** | Run `33540921143` exposed a clean-checkout test-directory defect; the fix passes Ruff and 7/7 tests locally at 92.38% coverage and awaits publication/rerun |

Verification was performed locally on 2026-09-01. See the [full evidence report](outputs/verification-report.md).

## Known limitations

- Processing runs in the request path; a production deployment needs a durable queue, retries, idempotency, and worker backpressure.
- The included provider handles a controlled invoice layout. Real documents require an evaluated LLM/document-model adapter and a labelled quality corpus.
- OCR depends on the host Tesseract binary and is not yet covered by a scanned-PDF integration fixture.
- Authentication, tenant isolation, malware scanning, retention policies, encryption-key management, rate limiting, and observability are not implemented.
- CSV uses a portable field/value representation; domain-specific flattened line-item exports would need an explicit contract.
- Local storage is a development adapter, not a multi-instance object store.

## License

MIT — see [LICENSE](LICENSE).
