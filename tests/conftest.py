import os

os.environ["DATABASE_URL"] = "sqlite:///./work/test.db"
os.environ["STORAGE_ROOT"] = "./work/test-uploads"

import fitz
import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


def make_pdf(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_textbox(fitz.Rect(50, 50, 550, 790), text, fontsize=11)
    return doc.tobytes()


@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def valid_invoice_pdf():
    return make_pdf("""INVOICE
Invoice Number: INV-2026-0042
Vendor: Northstar Office Supply
Invoice Date: 2026-08-15
Due Date: 2026-09-14
Currency: USD
ITEM | Ergonomic Keyboard | 2 | 75.00 | 150.00
ITEM | USB-C Dock | 1 | 189.00 | 189.00
Subtotal: 339.00
Tax: 27.12
Total: 366.12
""")
