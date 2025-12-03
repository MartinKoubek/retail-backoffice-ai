import os
from difflib import get_close_matches
from typing import Dict, List

from .extraction import DocumentData


def suggest_corrections(data: DocumentData, validation_results: List[Dict], catalog: Dict[str, Dict]) -> Dict:
    suggestions: List[str] = []
    for issue in validation_results:
        msg = issue["message"]
        if "SKU" in msg and "not in catalog" in msg and data.items:
            unknown_sku = msg.split("SKU")[-1].split()[0]
            nearest = _closest_sku(unknown_sku, catalog)
            if nearest:
                suggestions.append(f"Did you mean SKU {nearest}?")
        elif "quantity" in msg and "exceeds" in msg:
            suggestions.append("Reduce quantity to expected range or confirm with supplier.")
        elif "Missing required field" in msg:
            suggestions.append("Provide the missing header fields before approval.")

    if not validation_results:
        suggestions.append("Looks good. Consider auto-approving similar documents.")
    if not data.supplier and catalog:
        suggestions.append("Supplier missing; infer from SKU ownership or ask requester.")

    recommended_action = _recommended_action(validation_results)
    return {
        "recommendations": suggestions,
        "recommended_action": recommended_action,
        "short_summary": _summarize_document(data, validation_results),
    }


def _recommended_action(validation_results: List[Dict]) -> str:
    has_errors = any(item["level"] == "error" for item in validation_results)
    has_warnings = any(item["level"] == "warning" for item in validation_results)
    if has_errors:
        return "reject"
    if has_warnings:
        return "request_correction"
    return "approve"


def _summarize_document(data: DocumentData, validation_results: List[Dict]) -> str:
    item_count = len(data.items or [])
    error_count = sum(1 for r in validation_results if r["level"] == "error")
    warning_count = sum(1 for r in validation_results if r["level"] == "warning")
    return (
        f"Doc {data.document_id or 'unknown'} dated {data.document_date or 'unknown'} "
        f"from {data.supplier or 'unknown'} with {item_count} item(s); "
        f"{error_count} error(s), {warning_count} warning(s)."
    )


def _closest_sku(target: str, catalog: Dict[str, Dict]) -> str:
    if not target or not catalog:
        return ""
    matches = get_close_matches(target, catalog.keys(), n=1, cutoff=0.5)
    return matches[0] if matches else ""


def llm_enabled() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))

