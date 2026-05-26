from __future__ import annotations

import re
from pathlib import Path

from app.schemas.modules import (
    ModulePrepSummaryItem,
    ModulePrepSummaryResponse,
    ModuleTimelineEvent,
    ModuleTimelineResponse,
)
from app.services.module_service import ModuleService
from app.services.module_structure_service import guess_structure_type


NPC_PATTERN = re.compile(r"^(?:NPC|人物|角色)[:：\s]+(.+)$")
CLUE_PATTERN = re.compile(r"^(?:线索|clue)[:：\s]+(.+)$")
LOCATION_PATTERN = re.compile(r"^(?:地点|场景|location)[:：\s]+(.+)$")
TRIGGER_PATTERN = re.compile(r"^(?:触发条件|触发)[:：\s]+(.+)$")


class ModulePrepService:
    def __init__(self, module_service: ModuleService | None = None) -> None:
        self.module_service = module_service or ModuleService()

    def build_timeline(self, module_id: str) -> ModuleTimelineResponse:
        self.module_service.get_module(module_id)
        paths = self.module_service.module_paths(module_id)
        events: list[ModuleTimelineEvent] = []
        order = 0

        for path in sorted(paths["documents_dir"].rglob("*")):
            if not path.is_file():
                continue
            content = read_text(path)
            content_type = guess_structure_type(path)
            if content_type not in {"scene", "timeline", "document", "note"}:
                continue
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            if not lines:
                continue
            order += 1
            first_line = lines[0]
            events.append(
                ModuleTimelineEvent(
                    order=order,
                    title=first_line.lstrip("# ").strip()[:60] or path.stem,
                    source=str(path.relative_to(paths["documents_dir"])),
                    content_type=content_type,
                    location=extract_first(LOCATION_PATTERN, lines),
                    npcs=extract_many(NPC_PATTERN, lines),
                    clues=extract_many(CLUE_PATTERN, lines),
                    trigger=extract_first(TRIGGER_PATTERN, lines),
                    preview=make_preview(content),
                )
            )

        return ModuleTimelineResponse(module_id=module_id, events=events)

    def build_prep_summary(self, module_id: str) -> ModulePrepSummaryResponse:
        self.module_service.get_module(module_id)
        paths = self.module_service.module_paths(module_id)
        highlights: list[ModulePrepSummaryItem] = []
        clues: list[ModulePrepSummaryItem] = []
        npcs: list[ModulePrepSummaryItem] = []
        warnings: list[str] = []

        for path in sorted(paths["documents_dir"].rglob("*")):
            if not path.is_file():
                continue
            content = read_text(path)
            content_type = guess_structure_type(path)
            preview = make_preview(content)
            title = path.stem

            if content_type in {"scene", "timeline"} and len(highlights) < 6:
                highlights.append(ModulePrepSummaryItem(title=title, content_type=content_type, source=str(path.relative_to(paths["documents_dir"])), preview=preview))

            for clue in extract_many(CLUE_PATTERN, content.splitlines()):
                if len(clues) >= 8:
                    break
                clues.append(ModulePrepSummaryItem(title=clue, content_type="clue", source=str(path.relative_to(paths["documents_dir"])), preview=preview))

            for npc in extract_many(NPC_PATTERN, content.splitlines()):
                if len(npcs) >= 8:
                    break
                npcs.append(ModulePrepSummaryItem(title=npc, content_type="npc", source=str(path.relative_to(paths["documents_dir"])), preview=preview))

        if not highlights:
            warnings.append("未识别到明显的场景或时间线内容，可能需要更明确的标题或更细的拆分。")
        if not clues:
            warnings.append("未识别到明显的线索条目，建议检查模组正文中是否有线索标题或关键词。")
        if not npcs:
            warnings.append("未识别到明显的 NPC 信息，建议检查文件名和标题路径。")

        return ModulePrepSummaryResponse(
            module_id=module_id,
            highlights=highlights,
            clues=clues,
            npcs=npcs,
            warnings=warnings,
        )


def read_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        return f"PDF: {path.stem}"
    return path.read_text(encoding="utf-8")


def extract_first(pattern: re.Pattern[str], lines: list[str] | str) -> str | None:
    for line in iterate_lines(lines):
        match = pattern.match(line)
        if not match:
            continue
        value = match.group(1).strip()
        return value or None
    return None


def extract_many(pattern: re.Pattern[str], lines: list[str] | str, limit: int = 5) -> list[str]:
    results: list[str] = []
    for line in iterate_lines(lines):
        match = pattern.match(line)
        if not match:
            continue
        value = match.group(1).strip()
        if value and value not in results:
            results.append(value)
        if len(results) >= limit:
            break
    return results


def make_preview(text: str, limit: int = 140) -> str:
    return text.replace("\n", " ").strip()[:limit]


def iterate_lines(lines: list[str] | str) -> list[str]:
    if isinstance(lines, str):
        return [line.strip() for line in lines.splitlines() if line.strip()]
    return [line.strip() for line in lines if line.strip()]
