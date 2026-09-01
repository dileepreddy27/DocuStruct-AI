# DocuStruct AI — local verification report

Date: 2026-09-01  
Scope: local source and runtime only; a local `main` Git repository was initialized, but no commit, remote repository, or publication action was performed.

## Outcome

DocuStruct AI is ready for local demonstration and a publication review. The tested path covers PDF upload through persisted PostgreSQL state, deterministic structured extraction, JSON Schema validation, confidence-based review routing, corrected-data validation, and JSON/CSV export. It is intentionally described as production-minded, not production-ready.

## Evidence

| Area | Result | Observed evidence |
|---|---|---|
| Tests | Verified | 7 passed in 1.57 seconds; 92% application coverage |
| Lint | Verified | Ruff: `All checks passed!` |
| Compilation | Verified | `python -m compileall app` completed without errors |
| Migration | Verified | Alembic applied `0001` to SQLite; the container entrypoint applied migrations against PostgreSQL |
| Samples | Verified | Two explicitly synthetic invoice PDFs generated |
| Container build | Verified | `docustruct-ai-app:latest` built successfully, including Tesseract OCR packages |
| Compose services | Verified | PostgreSQL and application containers both reported healthy |
| Clean extraction | Verified | `synthetic-invoice-clean.pdf` completed at 0.97 confidence and exported total `366.12` |
| Human review | Verified | `synthetic-invoice-review.pdf` entered `review_required` with two validation errors and appeared in the pending queue |
| UI runtime | Verified | HTTP 200; 705 characters of visible content; upload/process/refresh/export controls rendered; no error overlay or console errors |
| Failure paths | Verified | Tests cover unsupported media, unreadable PDFs, partial batch success, review correction, and export behavior |
| Secret hygiene | Verified with noted defaults | Scan found only empty `LLM_API_KEY`, typed config field, and the documented local-only Compose database password |
| OCR quality | Not run | Runtime dependency exists, but a scanned-PDF fixture and accuracy assertion remain future work |
| Hosted LLM | Not implemented | Provider interface exists; deterministic offline provider is the only included adapter |
| Remote CI | Unverified | GitHub Actions workflow exists, but no remote repository or run exists |

## Reproduce

Follow [docs/demo.md](../docs/demo.md). If host port 8000 is occupied, set `APP_PORT=8001` before `docker compose up --build`.

## Publication gate

Before publication: review and commit the current candidate set, repeat secret and local-path scans, then create the remote only after explicit authorization. After pushing, verify the public tree and the first GitHub Actions run before adding CI badges or claiming remote CI success.
