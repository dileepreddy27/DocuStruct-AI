from pathlib import Path

import fitz

SAMPLES = {
    "synthetic-invoice-clean.pdf": """SYNTHETIC DEMO DOCUMENT - NO REAL PERSONAL DATA
INVOICE
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
""",
    "synthetic-invoice-review.pdf": """SYNTHETIC DEMO DOCUMENT - NO REAL PERSONAL DATA
INVOICE
Vendor: Example Field Services
Invoice Date: 2026-08-20
ITEM | Inspection service | 1 | 240.00 | 240.00
Total: 240.00
NOTE: Intentionally incomplete to demonstrate human review.
""",
}

root = Path(__file__).resolve().parents[1] / "samples"
root.mkdir(exist_ok=True)
for name, text in SAMPLES.items():
    document = fitz.open()
    page = document.new_page()
    page.insert_textbox(fitz.Rect(55, 55, 540, 780), text, fontsize=11, lineheight=1.4)
    document.save(root / name)
print(f"Generated {len(SAMPLES)} synthetic PDFs in {root}")
