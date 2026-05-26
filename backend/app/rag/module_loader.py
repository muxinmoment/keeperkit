from __future__ import annotations

import json
import re
from pathlib import Path

from app.rag.document_reader import SUPPORTED_DOCUMENT_SUFFIXES, read_document_text
from app.rag.types import RawDocument


CONTENT_TYPE_RULES: list[tuple[str, str]] = [
    ("timeline", "timeline"),
    ("时间线", "timeline"),
    ("scene", "scene"),
    ("场景", "scene"),
    ("npc", "npc"),
    ("人物", "npc"),
    ("线索", "clue"),
    ("clue", "clue"),
    ("handout", "handout"),
    ("手牌", "handout"),
    ("monster", "monster"),
    ("怪物", "monster"),
    ("note", "note"),
    ("笔记", "note"),
    ("rule", "rule"),
]


def load_module_documents(module_dir: Path) -> list[RawDocument]:
    module_file = module_dir / "module.json"
    documents_dir = module_dir / "documents"
    if not module_file.exists():
        raise FileNotFoundError(f"Module metadata not found: {module_file}")
    if not documents_dir.exists():
        raise FileNotFoundError(f"Module documents directory not found: {documents_dir}")

    module_metadata = json.loads(module_file.read_text(encoding="utf-8"))
    module_id = str(module_metadata.get("id", module_dir.name))
    module_title = str(module_metadata.get("title", module_id))
    base_metadata = {
        "knowledge_base": "module",
        "module_id": module_id,
        "module_title": module_title,
        "system": str(module_metadata.get("system", "coc7")),
        "language": str(module_metadata.get("language", "zh")),
        "spoiler_level": str(module_metadata.get("spoiler_level", "keeper_only")),
    }

    documents: list[RawDocument] = []
    order_index = 0
    for path in sorted(documents_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_DOCUMENT_SUFFIXES:
            continue
        order_index += 1
        documents.append(
            RawDocument(
                content=read_document_text(path),
                metadata={
                    **base_metadata,
                    "source": str(path.relative_to(documents_dir)),
                    "suffix": path.suffix.lower(),
                    "content_type": guess_content_type(path),
                    "order_index": str(order_index),
                },
            )
        )

    if not documents:
        raise FileNotFoundError(
            f"No module documents found in {documents_dir}. Add Markdown, TXT or PDF files first."
        )

    return documents


def guess_content_type(path: Path) -> str:
    probe = normalize_text(f"{path.stem} {' '.join(path.parts)}")
    for needle, content_type in CONTENT_TYPE_RULES:
        if needle in probe:
            return content_type
    return "document"


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", "", text.lower())
