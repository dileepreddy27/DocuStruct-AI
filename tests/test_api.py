def upload(client, content: bytes, name="invoice.pdf"):
    return client.post(
        "/api/v1/documents",
        files={"file": (name, content, "application/pdf")},
        data={"schema_name": "invoice"},
    )


def test_valid_invoice_completes_and_exports(client, valid_invoice_pdf):
    response = upload(client, valid_invoice_pdf)
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "completed"
    assert body["extraction"]["data"]["total"] == 366.12
    assert body["extraction"]["confidence"] >= 0.8
    document_id = body["id"]
    exported = client.get(f"/api/v1/documents/{document_id}/export.json")
    assert exported.status_code == 200
    assert exported.json()["invoice_number"] == "INV-2026-0042"
    csv_export = client.get(f"/api/v1/documents/{document_id}/export.csv")
    assert csv_export.status_code == 200
    assert "invoice_number,INV-2026-0042" in csv_export.text


def test_incomplete_invoice_enters_review_and_accepts_correction(client):
    from tests.conftest import make_pdf

    response = upload(client, make_pdf("Vendor: Incomplete Vendor\nTotal: 15.00"))
    body = response.json()
    assert body["status"] == "review_required"
    assert body["extraction"]["validation_errors"]
    pending = client.get("/api/v1/reviews").json()
    assert len(pending) == 1
    corrected = {
        "invoice_number": "FIX-1",
        "vendor": "Incomplete Vendor",
        "invoice_date": "2026-08-01",
        "due_date": None,
        "currency": "USD",
        "subtotal": 15.0,
        "tax": 0.0,
        "total": 15.0,
        "line_items": [],
    }
    review = client.post(
        f"/api/v1/reviews/{body['id']}",
        json={"reviewer": "demo-reviewer", "corrected_data": corrected},
    )
    assert review.status_code == 200
    assert review.json()["status"] == "completed"
    assert (
        client.get(f"/api/v1/documents/{body['id']}/export.json").json()["invoice_number"]
        == "FIX-1"
    )


def test_non_pdf_is_rejected_without_persisting(client):
    response = client.post(
        "/api/v1/documents",
        files={"file": ("notes.txt", b"hello", "text/plain")},
        data={"schema_name": "invoice"},
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "UNSUPPORTED_MEDIA_TYPE"
    assert client.get("/api/v1/documents").json() == []


def test_invalid_pdf_is_persisted_as_failed(client):
    response = upload(client, b"not actually a PDF")
    assert response.status_code == 201
    assert response.json()["status"] == "failed"
    assert response.json()["error_code"] == "INVALID_PDF"


def test_batch_reports_partial_acceptance(client, valid_invoice_pdf):
    response = client.post(
        "/api/v1/documents/batch",
        files=[
            ("files", ("good.pdf", valid_invoice_pdf, "application/pdf")),
            ("files", ("bad.txt", b"text", "text/plain")),
        ],
        data={"schema_name": "invoice"},
    )
    assert response.status_code == 207
    assert len(response.json()["accepted"]) == 1
    assert response.json()["rejected"][0]["code"] == "UNSUPPORTED_MEDIA_TYPE"
