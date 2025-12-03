import json
from io import BytesIO
from typing import Dict, List

from fpdf import FPDF

from .extraction import DocumentData


def build_html_report(data: DocumentData, validation: List[Dict], ai_output: Dict) -> str:
    items_rows = "".join(
        f"<tr><td>{item.sku or ''}</td><td>{item.name or ''}</td><td>{item.quantity or ''}</td><td>{item.price or ''}</td></tr>"
        for item in data.items or []
    )
    validation_rows = "".join(
        f"<li><strong>{entry['level'].title()}:</strong> {entry['message']}</li>" for entry in validation
    )
    ai_rows = "".join(f"<li>{rec}</li>" for rec in ai_output.get("recommendations", []))
    return f"""
    <html>
        <body style="font-family: Arial, sans-serif; background:#0f172a; color:#e2e8f0; padding:12px;">
            <h2 style="color:#e2e8f0;">Retail Back-Office AI Report</h2>
            <p><strong>Document ID:</strong> {data.document_id or 'N/A'}</p>
            <p><strong>Date:</strong> {data.document_date or 'N/A'}</p>
            <p><strong>Supplier:</strong> {data.supplier or 'N/A'}</p>
            <h3>Items</h3>
            <table border="1" cellspacing="0" cellpadding="6" style="border-color:#334155;color:#e2e8f0;">
                <tr style="background:#1e293b;"><th>SKU</th><th>Name</th><th>Quantity</th><th>Price</th></tr>
                {items_rows if items_rows else '<tr><td colspan="4">No items detected</td></tr>'}
            </table>
            <h3>Validation</h3>
            <ul style="color:#e2e8f0;">{validation_rows or '<li>No issues detected</li>'}</ul>
            <h3>AI Suggestions</h3>
            <ul style="color:#e2e8f0;">{ai_rows or '<li>No suggestions</li>'}</ul>
            <p><strong>Recommended action:</strong> {ai_output.get("recommended_action", "N/A")}</p>
            <h3>JSON Output</h3>
            <pre style="background:#0b1221; color:#e2e8f0; padding:10px; border:1px solid #334155;">{json.dumps(data.to_dict(), indent=2)}</pre>
        </body>
    </html>
    """


def build_pdf_report(data: DocumentData, validation: List[Dict], ai_output: Dict) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    def line(text: str):
        pdf.cell(0, 10, txt=text, ln=1)

    line("Retail Back-Office AI Report")
    line(f"Document ID: {data.document_id or 'N/A'}")
    line(f"Date: {data.document_date or 'N/A'}")
    line(f"Supplier: {data.supplier or 'N/A'}")
    line("")
    line("Items:")
    for item in data.items or []:
        line(f"- {item.sku or 'N/A'} | qty: {item.quantity or 'N/A'} | name: {item.name or 'N/A'} | price: {item.price or 'N/A'}")
    if not data.items:
        line("- No items detected")

    line("")
    line("Validation:")
    for entry in validation:
        line(f"- {entry['level'].title()}: {entry['message']}")
    if not validation:
        line("- No validation issues")

    line("")
    line("AI Suggestions:")
    for rec in ai_output.get("recommendations", []):
        line(f"- {rec}")
    if not ai_output.get("recommendations"):
        line("- No suggestions")
    line(f"Recommended action: {ai_output.get('recommended_action', 'N/A')}")

    buffer = BytesIO()
    pdf_bytes = pdf.output(dest="S")
    if isinstance(pdf_bytes, (bytes, bytearray)):
        buffer.write(bytes(pdf_bytes))
    else:
        buffer.write(str(pdf_bytes).encode("latin1"))
    return buffer.getvalue()
