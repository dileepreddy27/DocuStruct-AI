from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import router
from app.config import get_settings
from app.database import Base, engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    settings.storage_root.mkdir(parents=True, exist_ok=True)
    if settings.database_url.startswith("sqlite"):
        Base.metadata.create_all(engine)
    yield


app = FastAPI(
    title="DocuStruct AI API",
    version="0.1.0",
    description="Convert PDFs into schema-validated data with confidence scoring and human review.",
    lifespan=lifespan,
)
app.include_router(router)

web_dir = Path(__file__).parent / "web"
app.mount("/assets", StaticFiles(directory=web_dir), name="assets")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(web_dir / "index.html")
