FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr libgl1 && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml requirements.txt ./
COPY app ./app
RUN pip install --no-cache-dir .[postgres,ocr]
COPY migrations ./migrations
COPY alembic.ini ./
RUN mkdir -p /app/data/uploads
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]

