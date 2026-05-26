from __future__ import annotations

from pathlib import Path

try:
    import fitz
except ImportError as exc:
    raise RuntimeError("Missing dependency: pymupdf. Install it with: pip install pymupdf") from exc

try:
    import pymupdf4llm
except ImportError:
    pymupdf4llm = None


SUPPORTED_DOCUMENT_SUFFIXES = {".md", ".markdown", ".txt", ".pdf"}


def read_document_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".md", ".markdown", ".txt"}:
        return path.read_text(encoding="utf-8")
    if suffix == ".pdf":
        return read_pdf_text(path)
    raise ValueError(f"Unsupported document type: {path.suffix}")


def read_pdf_text(path: Path) -> str:
    if pymupdf4llm is not None:
        try:
            markdown = pymupdf4llm.to_markdown(str(path))
            if markdown.strip():
                return markdown
        except Exception:
            pass

    parts: list[str] = []
    with fitz.open(path) as document:
        for page_index, page in enumerate(document, start=1):
            text = page.get_text("text").strip()
            if text:
                parts.append(f"\n\n<!-- page: {page_index} -->\n\n{text}")
    return "\n".join(parts)
