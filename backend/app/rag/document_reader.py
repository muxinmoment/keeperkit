from __future__ import annotations

import hashlib
import json
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


def read_document_text(path: Path, cache_dir: Path | None = None) -> str:
    suffix = path.suffix.lower()
    if suffix in {".md", ".markdown", ".txt"}:
        return path.read_text(encoding="utf-8")
    if suffix == ".pdf":
        if cache_dir is not None:
            return read_pdf_text_cached(path, cache_dir)
        return read_pdf_text(path)
    raise ValueError(f"Unsupported document type: {path.suffix}")


def read_pdf_text_cached(path: Path, cache_dir: Path) -> str:
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{hash_path(path)}.json"
    fingerprint = build_file_fingerprint(path)

    if cache_path.exists():
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
        if payload.get("fingerprint") == fingerprint and isinstance(payload.get("text"), str):
            return str(payload["text"])

    text = read_pdf_text(path)
    cache_path.write_text(
        json.dumps(
            {
                "source": str(path),
                "fingerprint": fingerprint,
                "text": text,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return text


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


def build_file_fingerprint(path: Path) -> dict[str, int | str]:
    stat = path.stat()
    return {
        "name": path.name,
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }


def hash_path(path: Path) -> str:
    return hashlib.sha256(str(path.resolve()).encode("utf-8")).hexdigest()[:24]
