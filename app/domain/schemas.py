INVOICE_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Invoice",
    "type": "object",
    "additionalProperties": False,
    "required": ["invoice_number", "vendor", "invoice_date", "total", "currency"],
    "properties": {
        "invoice_number": {"type": "string", "minLength": 1},
        "vendor": {"type": "string", "minLength": 1},
        "invoice_date": {"type": "string", "format": "date"},
        "due_date": {"type": ["string", "null"], "format": "date"},
        "currency": {"type": "string", "pattern": "^[A-Z]{3}$"},
        "subtotal": {"type": ["number", "null"], "minimum": 0},
        "tax": {"type": ["number", "null"], "minimum": 0},
        "total": {"type": "number", "minimum": 0},
        "line_items": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["description", "quantity", "unit_price", "amount"],
                "properties": {
                    "description": {"type": "string"},
                    "quantity": {"type": "number", "minimum": 0},
                    "unit_price": {"type": "number", "minimum": 0},
                    "amount": {"type": "number", "minimum": 0},
                },
            },
        },
    },
}

SCHEMAS = {"invoice": INVOICE_SCHEMA}
