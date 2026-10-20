"""Pass 1 PDF extraction: Docling to page-marked Markdown. No LLM involved."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PAGE_MARKER = "<!-- page: {n} -->"
PAGE_MARKER_RE = re.compile(r"^<!-- page: (\d+) -->$", re.MULTILINE)
MIN_PAGE_CHARS = 20  # pages with less text are flagged, never "corrected"


@dataclass
class Extraction:
    markdown: str
    page_count: int
    low_confidence_pages: list[int] = field(default_factory=list)
    title: str = ""
    author: str = ""


def _default_converter() -> Any:
    from docling.document_converter import DocumentConverter  # lazy: slow import

    return DocumentConverter()


def _pdf_metadata(path: Path) -> tuple[str, str]:
    try:
        import pypdfium2 as pdfium

        pdf = pdfium.PdfDocument(str(path))
        try:
            meta = pdf.get_metadata_dict()
        finally:
            pdf.close()
    except Exception:  # noqa: BLE001 - metadata is optional; bad PDFs fail in the converter
        return "", ""
    return (meta.get("Title") or "").strip(), (meta.get("Author") or "").strip()


def extract_pdf(path: Path, converter: Any | None = None) -> Extraction:
    document = (converter or _default_converter()).convert(str(path)).document
    parts: list[str] = []
    low: list[int] = []
    pages = sorted(document.pages)
    for n in pages:
        text = document.export_to_markdown(page_no=n).strip()
        if len(text) < MIN_PAGE_CHARS:
            low.append(n)
        parts.append(f"{PAGE_MARKER.format(n=n)}\n\n{text}")
    title, author = _pdf_metadata(path)
    return Extraction("\n\n".join(parts), len(pages), low, title, author)
