from app.domain.schemas import INVOICE_SCHEMA
from app.services.extraction import HeuristicInvoiceProvider


def test_heuristic_provider_extracts_invoice_fields():
    result = HeuristicInvoiceProvider().extract(
        "Invoice Number: A-10\nVendor: Acme Labs\nInvoice Date: 2026-08-01\n"
        "Currency: USD\nSubtotal: 10.00\nTax: 1.00\nTotal: 11.00\n"
        "ITEM | Service | 1 | 10.00 | 10.00",
        INVOICE_SCHEMA,
    )
    assert result.data["invoice_number"] == "A-10"
    assert result.data["total"] == 11.0
    assert result.data["line_items"][0]["description"] == "Service"


def test_provider_does_not_invent_missing_fields():
    result = HeuristicInvoiceProvider().extract("Vendor: Acme Labs", INVOICE_SCHEMA)
    assert "invoice_number" not in result.data
    assert result.field_confidence["line_items"] == 0.45
