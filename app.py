import json
from pathlib import Path
from typing import Dict, List, Tuple

import streamlit as st

from backoffice.ai import suggest_corrections
from backoffice.extraction import DocumentData, extract_structured_data
from backoffice.ingest import read_text
from backoffice.reporting import build_html_report, build_pdf_report
from backoffice.validation import load_catalog, summarize_validation, validate_document

CATALOG_PATH = Path("data/products.csv")


def process_document(file) -> Tuple[DocumentData, List[Dict], Dict, str, bytes, List[str]]:
    raw_bytes = file.getvalue()
    text, ingest_warnings = read_text(raw_bytes, file.name)
    data = extract_structured_data(text)
    catalog = load_catalog(CATALOG_PATH)
    validation_results = validate_document(data, catalog)
    ai_output = suggest_corrections(data, validation_results, catalog)
    html_report = build_html_report(data, validation_results, ai_output)
    pdf_report = build_pdf_report(data, validation_results, ai_output)
    return data, validation_results, ai_output, html_report, pdf_report, ingest_warnings


def load_catalog_rows(path: Path) -> List[Dict]:
    if not path.exists():
        return []
    import csv

    with path.open() as f:
        reader = csv.DictReader(f)
        return [
            {
                "sku": row.get("sku", ""),
                "name": row.get("name", ""),
                "max_quantity": row.get("max_quantity", ""),
            }
            for row in reader
        ]


def save_catalog_rows(path: Path, rows: List[Dict]) -> None:
    import csv

    fieldnames = ["sku", "name", "max_quantity"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "sku": (row.get("sku") or "").strip(),
                    "name": (row.get("name") or "").strip(),
                    "max_quantity": (row.get("max_quantity") or "").strip(),
                }
            )


def main():
    st.set_page_config(page_title="Retail Back-Office AI Demo", layout="wide")
    st.title("Retail Back-Office AI Automation")
    st.caption("Document ingestion → Extraction → Validation → AI Suggestions → Report")

    st.sidebar.header("How to use")
    st.sidebar.markdown(
        "- Upload a PDF, image, or text document\n"
        "- Click **Process Document**\n"
        "- Review extracted data, validation, and AI recommendations\n"
    )
    st.sidebar.markdown("Sample files:")
    samples_dir = Path("samples")
    if samples_dir.exists():
        for sample_file in sorted(samples_dir.glob("*")):
            if sample_file.is_file():
                col_name, col_btn = st.sidebar.columns([4, 1])
                col_name.write(sample_file.name)
                col_btn.download_button(
                    label="⬇",
                    data=sample_file.read_bytes(),
                    file_name=sample_file.name,
                    key=f"dl_{sample_file.name}",
                    help=f"Download {sample_file.name}",
                )
    else:
        st.sidebar.caption("No sample files found.")

    st.sidebar.header("Product catalog")
    catalog_rows = load_catalog_rows(CATALOG_PATH)
    st.sidebar.caption("Edit catalog entries (scrollable, first rows shown). Used for SKU validation.")
    edited_catalog = st.sidebar.data_editor(
        catalog_rows,
        num_rows="dynamic",
        hide_index=True,
        height=240,
        key="catalog_editor",
    )
    if st.sidebar.button("Save catalog", type="primary"):
        save_catalog_rows(CATALOG_PATH, edited_catalog)
        st.sidebar.success("Catalog saved.")

    uploaded_file = st.file_uploader(
        "Upload document", type=["pdf", "png", "jpg", "jpeg", "txt", "csv"], accept_multiple_files=False
    )

    if uploaded_file:
        st.subheader("Uploaded file preview")
        st.caption("Lightweight preview (no OCR fallback for speed).")
        file_bytes = uploaded_file.getvalue()
        preview_text, preview_warnings = read_text(file_bytes, uploaded_file.name, allow_ocr=False)
        if preview_text.strip():
            snippet = preview_text[:800]
            suffix = "…" if len(preview_text) > len(snippet) else ""
            st.code(snippet + suffix, language="text")
        else:
            st.info("No text preview available (likely scanned/bitmap). OCR will run during processing.")
        if preview_warnings:
            st.info("\n".join(f"- {w}" for w in preview_warnings))
        if uploaded_file.type.startswith("image/"):
            st.image(file_bytes, caption=uploaded_file.name, use_column_width=True)

    if st.button("Process Document", type="primary"):
        if not uploaded_file:
            st.warning("Please upload a document first.")
            return
        with st.spinner("Processing document..."):
            data, validation_results, ai_output, html_report, pdf_report, ingest_warnings = process_document(
                uploaded_file
            )

        if ingest_warnings:
            st.info("Ingestion warnings:\n" + "\n".join(f"- {w}" for w in ingest_warnings))

        data_tab, validation_tab, ai_tab, report_tab = st.tabs(
            ["Extracted Data", "Validation", "AI Suggestions", "Final Report"]
        )

        with data_tab:
            st.subheader("Structured Output (JSON)")
            st.json(data.to_dict())
            st.code(data.raw_text or "No text detected", language="text")

        with validation_tab:
            summary = summarize_validation(validation_results)
            st.metric("Errors", summary["errors"])
            st.metric("Warnings", summary["warnings"])
            if validation_results:
                for entry in validation_results:
                    if entry["level"] == "error":
                        st.error(entry["message"])
                    else:
                        st.warning(entry["message"])
            else:
                st.success("No validation issues found.")

        with ai_tab:
            st.write(f"Recommended action: **{ai_output.get('recommended_action', '').title()}**")
            for rec in ai_output.get("recommendations", []):
                st.markdown(f"- {rec}")
            st.caption(ai_output.get("short_summary", ""))

        with report_tab:
            st.components.v1.html(html_report, height=500, scrolling=True)
            st.download_button(
                "Download JSON",
                data=json.dumps(data.to_dict(), indent=2),
                file_name="extracted.json",
                mime="application/json",
            )
            st.download_button(
                "Download PDF report",
                data=pdf_report,
                file_name="report.pdf",
                mime="application/pdf",
            )


if __name__ == "__main__":
    main()
