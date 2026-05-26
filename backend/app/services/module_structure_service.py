from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from app.rag.document_reader import SUPPORTED_DOCUMENT_SUFFIXES, read_document_text
from app.schemas.modules import ModuleStructureGroup, ModuleStructureItem, ModuleStructureResponse
from app.services.module_service import ModuleService


STRUCTURE_ORDER = ["scene", "npc", "clue", "location", "timeline", "handout", "monster", "note", "rule", "document"]
GROUP_LABELS = {
    "scene": "场景",
    "npc": "NPC",
    "clue": "线索",
    "location": "地点",
    "timeline": "时间线",
    "handout": "手牌",
    "monster": "怪物",
    "note": "备注",
    "rule": "规则",
    "document": "其他",
}
KEYWORDS: list[tuple[str, str]] = [
    ("scene", "scene"),
    ("场景", "scene"),
    ("npc", "npc"),
    ("人物", "npc"),
    ("角色", "npc"),
    ("线索", "clue"),
    ("clue", "clue"),
    ("地点", "location"),
    ("location", "location"),
    ("时间线", "timeline"),
    ("timeline", "timeline"),
    ("手牌", "handout"),
    ("handout", "handout"),
    ("怪物", "monster"),
    ("monster", "monster"),
    ("笔记", "note"),
    ("note", "note"),
    ("规则", "rule"),
    ("rule", "rule"),
]


class ModuleStructureService:
    def __init__(self, module_service: ModuleService | None = None) -> None:
        self.module_service = module_service or ModuleService()

    def inspect(self, module_id: str) -> ModuleStructureResponse:
        self.module_service.get_module(module_id)
        paths = self.module_service.module_paths(module_id)
        groups: dict[str, list[ModuleStructureItem]] = defaultdict(list)

        for path in sorted(paths["documents_dir"].rglob("*")):
            if not path.is_file() or path.suffix.lower() not in SUPPORTED_DOCUMENT_SUFFIXES:
                continue
            content_type = guess_structure_type(path)
            relative_source = str(path.relative_to(paths["documents_dir"]))
            preview = read_preview(path)
            groups[content_type].append(
                ModuleStructureItem(
                    label=make_label(path, content_type),
                    source=relative_source,
                    title_path=guess_title_path(path),
                    content_type=content_type,
                    preview=preview,
                )
            )

        ordered_groups: list[ModuleStructureGroup] = []
        for content_type in STRUCTURE_ORDER:
            items = groups.get(content_type)
            if not items:
                continue
            ordered_groups.append(
                ModuleStructureGroup(
                    content_type=content_type,
                    label=GROUP_LABELS.get(content_type, content_type),
                    items=items,
                )
            )

        return ModuleStructureResponse(module_id=module_id, groups=ordered_groups)


def guess_structure_type(path: Path) -> str:
    probe = normalize_text(f"{path.stem} {' '.join(path.parts)}")
    for needle, content_type in KEYWORDS:
        if needle in probe:
            return content_type
    return "document"


def guess_title_path(path: Path) -> list[str]:
    parts = [part for part in path.with_suffix("").parts if part not in {"documents", "processed", "assets", "notes", "revisions"}]
    if len(parts) > 1:
        return parts[-2:]
    if parts:
        return [parts[-1]]
    return []


def make_label(path: Path, content_type: str) -> str:
    stem = path.stem
    if content_type == "document":
        return stem
    return stem


def read_preview(path: Path, limit: int = 160) -> str:
    try:
        text = read_document_text(path)
    except UnicodeDecodeError:
        return path.name
    except ValueError:
        return path.name
    preview = text.strip().replace("\n", " ")
    return preview[:limit]


def normalize_text(text: str) -> str:
    return "".join(text.lower().split())
