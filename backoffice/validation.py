import csv
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional

from .extraction import DocumentData, DocumentItem


def load_catalog(csv_path: Path) -> Dict[str, Dict]:
    catalog = {}
    if not csv_path.exists():
        return catalog
    with csv_path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            sku = row.get("sku") or row.get("SKU")
            if not sku:
                continue
            catalog[sku.strip()] = {
                "name": row.get("name", "").strip() or None,
                "max_quantity": _safe_int(row.get("max_quantity")),
            }
    return catalog


def validate_document(data: DocumentData, catalog: Dict[str, Dict]) -> List[Dict]:
    results: List[Dict] = []

    required_fields = {
        "document_date": data.document_date,
        "document_id": data.document_id,
    }

    for field, value in required_fields.items():
        if not value:
            results.append(
                {"level": "error", "message": f"Missing required field: {field.replace('_', ' ')}"}
            )

    if not data.items:
        results.append({"level": "error", "message": "No item lines detected"})

    for idx, item in enumerate(data.items or [], start=1):
        results.extend(_validate_item(item, catalog, idx))

    return results


def _validate_item(item: DocumentItem, catalog: Dict[str, Dict], position: int) -> List[Dict]:
    issues: List[Dict] = []
    label = f"Item {position}"

    if not item.sku:
        issues.append({"level": "error", "message": f"{label}: SKU missing"})
    if item.quantity is None:
        issues.append({"level": "error", "message": f"{label}: quantity missing"})
    elif item.quantity <= 0:
        issues.append({"level": "error", "message": f"{label}: quantity must be > 0"})

    catalog_entry = catalog.get(item.sku or "")
    if catalog_entry is None and item.sku:
        issues.append({"level": "warning", "message": f"{label}: SKU {item.sku} not in catalog"})
    elif catalog_entry:
        max_q = catalog_entry.get("max_quantity")
        if max_q and item.quantity and item.quantity > max_q:
            issues.append(
                {
                    "level": "warning",
                    "message": f"{label}: quantity {item.quantity} exceeds usual max {max_q}",
                }
            )
        if catalog_entry.get("name") and not item.name:
            issues.append(
                {
                    "level": "warning",
                    "message": f"{label}: name missing; catalog suggests {catalog_entry['name']}",
                }
            )

    return issues


def summarize_validation(results: List[Dict]) -> Dict[str, int]:
    summary = {"errors": 0, "warnings": 0}
    for item in results:
        if item["level"] == "error":
            summary["errors"] += 1
        elif item["level"] == "warning":
            summary["warnings"] += 1
    return summary


def _safe_int(value: Optional[str]) -> Optional[int]:
    try:
        return int(value) if value else None
    except (TypeError, ValueError):
        return None

