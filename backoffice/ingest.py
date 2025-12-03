from io import BytesIO
from pathlib import Path
from typing import Tuple

from pypdf import PdfReader
from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image, ImageOps


def read_text(file_bytes: bytes, filename: str, allow_ocr: bool = True) -> Tuple[str, list]:
    """
    Return extracted text for supported file types and a list of non-fatal warnings.
    """
    suffix = Path(filename).suffix.lower()
    warnings = []

    if suffix in {".txt", ".csv"}:
        return file_bytes.decode("utf-8", errors="replace"), warnings

    if suffix == ".pdf":
        try:
            reader = PdfReader(BytesIO(file_bytes))
            pages = [page.extract_text() or "" for page in reader.pages]
            text = "\n".join(pages).strip()
            if text:
                return text, warnings

            if allow_ocr:
                # Fallback: OCR scanned/bitmap PDFs
                images = convert_from_bytes(file_bytes)
                ocr_text = "\n".join(_ocr_image(img) for img in images).strip()
                if ocr_text:
                    warnings.append("Used OCR fallback for PDF pages.")
                    return ocr_text, warnings
        except Exception as exc:  # pragma: no cover - defensive
            warnings.append(f"Could not read PDF: {exc}")
            return "", warnings

    if suffix in {".png", ".jpg", ".jpeg"}:
        try:
            image = Image.open(BytesIO(file_bytes))
            if allow_ocr:
                text = _ocr_image(image)
            else:
                text = ""
            return text, warnings
        except Exception as exc:  # pragma: no cover - depends on local OCR
            warnings.append(
                "Image OCR failed. Install Tesseract for better results "
                f"(error: {exc})"
            )
            return "", warnings

    warnings.append(f"Unsupported file type: {suffix}")
    return "", warnings


def _ocr_image(image: Image.Image) -> str:
    """
    Lightly preprocess and OCR an image for better PNG/JPG accuracy.
    """
    if image.mode != "L":
        image = image.convert("L")  # grayscale for OCR stability
    # Boost contrast and resize modestly to improve OCR accuracy.
    image = ImageOps.autocontrast(image)
    new_size = (int(image.width * 1.5), int(image.height * 1.5))
    image = image.resize(new_size)
    # Gentle threshold to reduce noise.
    image = image.point(lambda x: 0 if x < 170 else 255, mode="1")
    return pytesseract.image_to_string(image, config="--psm 6").strip()
