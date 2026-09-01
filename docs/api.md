# API guide

Interactive OpenAPI is available at `/docs`; the raw specification is at `/openapi.json`.

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/v1/documents` | Upload and process one PDF |
| `POST` | `/api/v1/documents/batch` | Process up to 20 PDFs with per-file results |
| `GET` | `/api/v1/documents` | List documents and extraction summaries |
| `GET` | `/api/v1/documents/{id}` | Get one document |
| `GET` | `/api/v1/reviews` | List pending human reviews |
| `POST` | `/api/v1/reviews/{id}` | Approve valid output or submit corrected data |
| `GET` | `/api/v1/documents/{id}/export.json` | Export completed effective data |
| `GET` | `/api/v1/documents/{id}/export.csv` | Export completed effective data |

Failures use a stable detail object such as:

```json
{"detail":{"code":"UNSUPPORTED_MEDIA_TYPE","message":"Only PDF uploads are accepted"}}
```

Batch upload returns HTTP `207` with separate `accepted` and `rejected` arrays so one malformed file does not hide successful work.

