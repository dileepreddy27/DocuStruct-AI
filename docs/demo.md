# Reproducible demo

## Local Python

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,postgres,ocr]"
.\.venv\Scripts\python.exe scripts\generate_samples.py
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Open `http://localhost:8000`, upload `samples/synthetic-invoice-clean.pdf`, and observe a completed extraction. Upload `samples/synthetic-invoice-review.pdf` and inspect its `review_required` state through `GET /api/v1/reviews` or OpenAPI.

## Docker Compose

```powershell
docker compose up --build
```

The app starts after PostgreSQL is healthy and applies migrations before serving traffic. Stop with `docker compose down`; add `-v` only if intentionally removing database and upload volumes.
If port 8000 is already in use, set `APP_PORT=8001` before starting the stack.

## Verification

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest --cov=app --cov-report=term-missing
docker compose config
docker compose build
```
