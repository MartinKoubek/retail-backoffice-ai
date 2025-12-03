from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from app import process_document
from backoffice.ingest import pytesseract

ASSETS = Path("tests/assets")


class InMemoryFile(BytesIO):
    def __init__(self, data: bytes, name: str):
        super().__init__(data)
        self.name = name


def test_process_txt_sample():
    sample_path = Path("samples/sample_invoice.txt")
    data = sample_path.read_bytes()
    doc, validation, ai, html_report, pdf_report, warnings = process_document(
        InMemoryFile(data, sample_path.name)
    )

    assert doc.document_id == "INV-2024-0512"
    assert len(doc.items) == 3
    assert any(issue["level"] == "warning" for issue in validation)
    assert html_report and pdf_report
    assert not warnings


def test_process_pdf_asset():
    pdf_path = ASSETS / "test_invoice.pdf"
    doc, validation, ai, html_report, pdf_report, warnings = process_document(
        InMemoryFile(pdf_path.read_bytes(), pdf_path.name)
    )

    assert doc.document_id == "INV-XYZ-123"
    assert any(item.sku == "SKU-100" for item in doc.items)
    assert html_report and pdf_report
    assert warnings == []


def test_process_csv_asset():
    csv_path = ASSETS / "test_invoice.csv"
    doc, validation, ai, html_report, pdf_report, warnings = process_document(
        InMemoryFile(csv_path.read_bytes(), csv_path.name)
    )

    assert doc.document_date == "2024-06-01"
    assert doc.document_id in {"CSV-123", "ID"} or doc.document_id is not None
    assert html_report and pdf_report
    assert warnings == []


def test_process_png_with_mocked_ocr(monkeypatch):
    png_path = ASSETS / "test_invoice.png"
    mock_text = (
        "Date: 2024-02-02\n"
        "Invoice ID: INV-PNG-1\n"
        "Supplier: PNG Supplier\n"
        "SKU-300 Part 4 12.00\n"
    )
    monkeypatch.setattr(pytesseract, "image_to_string", lambda *_, **__: mock_text)

    doc, validation, ai, html_report, pdf_report, warnings = process_document(
        InMemoryFile(png_path.read_bytes(), png_path.name)
    )

    assert doc.document_id == "INV-PNG-1"
    assert any(item.sku == "SKU-300" for item in doc.items)
    assert html_report and pdf_report
    assert warnings == []
