import re
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional


@dataclass
class DocumentItem:
    sku: Optional[str] = None
    name: Optional[str] = None
    quantity: Optional[int] = None
    price: Optional[float] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class DocumentData:
    document_date: Optional[str] = None
    document_id: Optional[str] = None
    supplier: Optional[str] = None
    items: List[DocumentItem] = None
    raw_text: str = ""

    def to_dict(self):
        return {
            "document_date": self.document_date,
            "document_id": self.document_id,
            "supplier": self.supplier,
            "items": [item.to_dict() for item in self.items or []],
        }


DATE_PATTERNS = [
    r"\b(\d{4}-\d{2}-\d{2})\b",
    r"\b(\d{2}/\d{2}/\d{4})\b",
    r"\b(\d{2}-\d{2}-\d{4})\b",
]


def parse_date(text: str) -> Optional[str]:
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, text)
        if match:
            candidate = match.group(1)
            for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y"):
                try:
                    dt = datetime.strptime(candidate, fmt)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue
    return None


def parse_document_id(text: str) -> Optional[str]:
    id_match = re.search(
        r"(?:Invoice\s+ID|Document\s+ID|Invoice|Document|Ref|ID)\s*[:#]?\s*([A-Za-z0-9][A-Za-z0-9\-]{2,})",
        text,
        re.IGNORECASE,
    )
    if id_match:
        candidate = id_match.group(1)
        if len(candidate) >= 3:
            return candidate
    fallback = re.search(r"\b([A-Z]{2,5}-\d{3,})\b", text)
    return fallback.group(1) if fallback else None


def parse_supplier(text: str) -> Optional[str]:
    for label in ("Supplier", "Vendor", "From"):
        match = re.search(fr"{label}[^\w]?[:\-]\s*(.+)", text, re.IGNORECASE)
        if match:
            line = match.group(1).strip()
            return line.splitlines()[0].strip()
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for ln in lines:
        if ln.lower().startswith("date"):
            continue
        return ln[:80]
    return None


def parse_items(text: str) -> List[DocumentItem]:
    items = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or len(line.split()) < 2:
            continue
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in ("date", "invoice", "supplier", "items")) and "sku" not in line_lower:
            continue
        tokens = line.replace(",", " ").split()
        price = None
        qty = None

        if tokens and _is_price(tokens[-1]):
            price = float(tokens.pop())

        if tokens and tokens[-1].isdigit():
            qty = int(tokens.pop())

        if not tokens:
            continue

        sku = tokens[0]
        name = " ".join(tokens[1:]) if len(tokens) > 1 else None

        if qty is None:
            continue

        items.append(DocumentItem(sku=sku, name=name or None, quantity=qty, price=price))

    return items


def _is_price(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


def extract_structured_data(text: str) -> DocumentData:
    document_date = parse_date(text)
    document_id = parse_document_id(text)
    supplier = parse_supplier(text)
    items = parse_items(text)
    return DocumentData(
        document_date=document_date,
        document_id=document_id,
        supplier=supplier,
        items=items,
        raw_text=text,
    )
