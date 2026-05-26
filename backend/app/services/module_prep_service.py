from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.agents.module_prep_graph import create_module_prep_graph
from app.config import settings
from app.rag.document_reader import SUPPORTED_DOCUMENT_SUFFIXES, build_file_fingerprint, read_document_text
from app.rag.module_generator import create_module_generator
from app.schemas.modules import (
    ModulePrepFullSection,
    ModulePrepStructuredData,
    ModulePrepDraftResponse,
    ModulePrepDraftUpdateRequest,
    ModulePrepMapEdge,
    ModulePrepMapNode,
    ModulePrepMapResponse,
    ModulePrepFullResponse,
    ModulePrepSummaryItem,
    ModulePrepSummaryResponse,
    ModuleSource,
    ModuleTimelineEvent,
    ModuleTimelineResponse,
)
from app.services.module_service import ModuleService
from app.services.module_structure_service import guess_structure_type


NPC_PATTERN = re.compile(r"^(?:NPC|人物|角色)[:：\s]+(.+)$")
CLUE_PATTERN = re.compile(r"^(?:线索|clue)[:：\s]+(.+)$")
LOCATION_PATTERN = re.compile(r"^(?:地点|场景|location)[:：\s]+(.+)$")
TRIGGER_PATTERN = re.compile(r"^(?:触发条件|触发)[:：\s]+(.+)$")
MAP_KIND_LABELS = {
    "scene": "场景",
    "timeline": "时间线",
    "npc": "NPC",
    "clue": "线索",
    "location": "地点",
    "trigger": "触发",
    "document": "资料",
}
FULL_PREP_CACHE_FILE = "prep_full_cache.json"
FULL_PREP_DRAFT_FILE = "prep_draft.json"
FULL_PREP_PROMPT_VERSION = "v2-json"


class ModulePrepService:
    def __init__(self, module_service: ModuleService | None = None) -> None:
        self.module_service = module_service or ModuleService()
        self.generator = create_module_generator(settings.generator_provider)
        self.prep_graph = create_module_prep_graph(self.generator)

    def build_timeline(self, module_id: str) -> ModuleTimelineResponse:
        self.module_service.get_module(module_id)
        paths = self.module_service.module_paths(module_id)
        events: list[ModuleTimelineEvent] = []
        order = 0

        for path in sorted(paths["documents_dir"].rglob("*")):
            if not path.is_file() or path.suffix.lower() not in SUPPORTED_DOCUMENT_SUFFIXES:
                continue
            content = read_cached_document_text(paths, path)
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
            if not path.is_file() or path.suffix.lower() not in SUPPORTED_DOCUMENT_SUFFIXES:
                continue
            content = read_cached_document_text(paths, path)
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

    def build_prep_map(self, module_id: str) -> ModulePrepMapResponse:
        module = self.module_service.get_module(module_id)
        paths = self.module_service.module_paths(module_id)
        nodes: dict[str, ModulePrepMapNode] = {
            "module": ModulePrepMapNode(
                id="module",
                label=module.title,
                kind="module",
                summary="当前模组的备团总览",
            )
        }
        edges: list[ModulePrepMapEdge] = []
        warnings: list[str] = []
        scene_count = 0

        for path in sorted(paths["documents_dir"].rglob("*")):
            if not path.is_file() or path.suffix.lower() not in SUPPORTED_DOCUMENT_SUFFIXES:
                continue
            content = read_cached_document_text(paths, path)
            lines = iterate_lines(content)
            if not lines:
                continue

            source = str(path.relative_to(paths["documents_dir"]))
            content_type = guess_structure_type(path)
            scene_count += 1
            scene_kind = "timeline" if content_type == "timeline" else "scene"
            scene_id = f"{scene_kind}-{scene_count}"
            scene_title = make_event_title(path, lines)
            nodes[scene_id] = ModulePrepMapNode(
                id=scene_id,
                label=scene_title,
                kind=scene_kind,
                source=source,
                summary=make_preview(content, limit=96),
            )
            edges.append(ModulePrepMapEdge(source_id="module", target_id=scene_id, label=MAP_KIND_LABELS[scene_kind]))

            location = extract_first(LOCATION_PATTERN, lines)
            if location:
                location_id = make_node_id("location", location)
                nodes.setdefault(
                    location_id,
                    ModulePrepMapNode(id=location_id, label=location, kind="location", source=source),
                )
                edges.append(ModulePrepMapEdge(source_id=scene_id, target_id=location_id, label="发生于"))

            trigger = extract_first(TRIGGER_PATTERN, lines)
            if trigger:
                trigger_id = make_node_id("trigger", trigger)
                nodes.setdefault(
                    trigger_id,
                    ModulePrepMapNode(id=trigger_id, label=trigger, kind="trigger", source=source),
                )
                edges.append(ModulePrepMapEdge(source_id=trigger_id, target_id=scene_id, label="触发"))

            for npc in extract_many(NPC_PATTERN, lines, limit=8):
                npc_id = make_node_id("npc", npc)
                nodes.setdefault(npc_id, ModulePrepMapNode(id=npc_id, label=npc, kind="npc", source=source))
                edges.append(ModulePrepMapEdge(source_id=scene_id, target_id=npc_id, label="出现"))

            for clue in extract_many(CLUE_PATTERN, lines, limit=8):
                clue_id = make_node_id("clue", clue)
                nodes.setdefault(clue_id, ModulePrepMapNode(id=clue_id, label=clue, kind="clue", source=source))
                edges.append(ModulePrepMapEdge(source_id=scene_id, target_id=clue_id, label="可获得"))

        if len(nodes) <= 1:
            warnings.append("还没有识别到可绘制的备团结构，先上传模组资料。")
        elif not any(node.kind == "clue" for node in nodes.values()):
            warnings.append("地图里还没有线索节点，建议在模组材料中标注“线索：”。")
        if not any(node.kind == "npc" for node in nodes.values()):
            warnings.append("地图里还没有 NPC 节点，建议在模组材料中标注“NPC：”或“人物：”。")

        return ModulePrepMapResponse(
            module_id=module_id,
            nodes=list(nodes.values()),
            edges=dedupe_edges(edges),
            warnings=warnings,
        )

    def build_full_prep(self, module_id: str) -> ModulePrepFullResponse:
        module = self.module_service.get_module(module_id)
        paths = self.module_service.module_paths(module_id)
        documents: list[str] = []
        sources: list[ModuleSource] = []
        character_count = 0
        fingerprints: list[dict[str, object]] = []

        for path in sorted(paths["documents_dir"].rglob("*")):
            if not path.is_file() or path.suffix.lower() not in SUPPORTED_DOCUMENT_SUFFIXES:
                continue
            content = read_cached_document_text(paths, path).strip()
            if not content:
                continue
            source = str(path.relative_to(paths["documents_dir"]))
            content_type = guess_structure_type(path)
            documents.append(f"[来源：{source}]\n类型：{content_type}\n\n{content}")
            character_count += len(content)
            fingerprints.append(
                {
                    "source": source,
                    "content_type": content_type,
                    "fingerprint": build_file_fingerprint(path),
                }
            )
            sources.append(
                ModuleSource(
                    knowledge_base="module_fulltext",
                    module_id=module_id,
                    source=source,
                    title_path=guess_title_path_from_path(path),
                    content_type=content_type,
                    spoiler_level=module.spoiler_level,
                    content_preview=make_preview(content, limit=180),
                )
            )

        cache_key = build_full_prep_cache_key(fingerprints)
        cached_response = read_full_prep_cache(paths["processed_dir"] / FULL_PREP_CACHE_FILE, module_id, cache_key)
        if cached_response is not None:
            return cached_response

        graph_state = self.prep_graph.invoke(
            {
                "action": "generate",
                "module_title": module.title,
                "documents": documents,
            },
            config=graph_config(module_id),
        )
        answer = str(graph_state.get("answer", ""))
        structured = parse_structured_prep(answer)
        response = ModulePrepFullResponse(
            module_id=module_id,
            answer=answer,
            sources=sources,
            document_count=len(documents),
            character_count=character_count,
            cache_hit=False,
            sections=structured_to_sections(structured),
            structured=structured,
        )
        write_full_prep_cache(paths["processed_dir"] / FULL_PREP_CACHE_FILE, response, cache_key)
        return response

    def get_or_create_prep_draft(self, module_id: str) -> ModulePrepDraftResponse:
        self.module_service.get_module(module_id)
        paths = self.module_service.module_paths(module_id)
        draft_path = paths["processed_dir"] / FULL_PREP_DRAFT_FILE
        cached_draft = read_prep_draft(draft_path)
        if cached_draft is not None and not is_structured_empty(cached_draft.structured):
            return cached_draft

        full_prep = self.build_full_prep(module_id)
        draft = ModulePrepDraftResponse(
            **full_prep.model_dump(),
            updated_at=current_timestamp(),
            thread_id=thread_id_for_module(module_id),
            revision_history=[],
        )
        write_prep_draft(draft_path, draft)
        return draft

    def update_prep_draft(self, module_id: str, request: ModulePrepDraftUpdateRequest) -> ModulePrepDraftResponse:
        self.module_service.get_module(module_id)
        paths = self.module_service.module_paths(module_id)
        draft_path = paths["processed_dir"] / FULL_PREP_DRAFT_FILE
        existing = read_prep_draft(draft_path)
        if existing is None:
            existing = self.get_or_create_prep_draft(module_id)
        answer = sections_to_markdown(request.sections)
        structured = sections_to_structured(request.sections, existing.structured)
        draft = existing.model_copy(
            update={
                "answer": answer,
                "sections": request.sections,
                "structured": structured,
                "cache_hit": True,
                "updated_at": current_timestamp(),
            }
        )
        write_prep_draft(draft_path, draft)
        return draft

    def revise_prep_draft_section(
        self,
        module_id: str,
        section_id: str,
        instruction: str,
    ) -> ModulePrepDraftResponse:
        module = self.module_service.get_module(module_id)
        paths = self.module_service.module_paths(module_id)
        draft_path = paths["processed_dir"] / FULL_PREP_DRAFT_FILE
        draft = read_prep_draft(draft_path) or self.get_or_create_prep_draft(module_id)
        sections = list(draft.sections)
        target_index = next((index for index, section in enumerate(sections) if section.id == section_id), None)
        if target_index is None:
            raise ValueError(f"Prep section not found: {section_id}")

        target = sections[target_index]
        graph_state = self.prep_graph.invoke(
            {
                "action": "revise",
                "module_title": module.title,
                "sections": [section.model_dump() for section in sections],
                "section_id": section_id,
                "instruction": instruction,
                "revision_history": draft.revision_history,
            },
            config=graph_config(module_id),
        )
        revised_sections = [
            ModulePrepFullSection.model_validate(section)
            for section in graph_state.get("sections", [])
        ]
        revision_history = [
            dict(item)
            for item in graph_state.get("revision_history", draft.revision_history)
        ]
        updated = draft.model_copy(
            update={
                "answer": sections_to_markdown(revised_sections),
                "sections": revised_sections,
                "structured": sections_to_structured(revised_sections, draft.structured),
                "cache_hit": True,
                "revision_history": revision_history,
                "updated_at": current_timestamp(),
            }
        )
        write_prep_draft(draft_path, updated)
        return updated


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


def read_cached_document_text(paths: dict[str, Path], path: Path) -> str:
    return read_document_text(path, cache_dir=paths["processed_dir"] / "text_cache")


def build_full_prep_cache_key(fingerprints: list[dict[str, object]]) -> str:
    payload = {
        "documents": fingerprints,
        "generator_provider": settings.generator_provider,
        "llm_model": settings.llm_model,
        "prompt_version": FULL_PREP_PROMPT_VERSION,
    }
    raw_value = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw_value.encode("utf-8")).hexdigest()


def read_full_prep_cache(cache_path: Path, module_id: str, cache_key: str) -> ModulePrepFullResponse | None:
    if not cache_path.exists():
        return None
    payload = json.loads(cache_path.read_text(encoding="utf-8"))
    if payload.get("cache_key") != cache_key:
        return None
    response_payload = payload.get("response")
    if not isinstance(response_payload, dict):
        return None
    response = ModulePrepFullResponse.model_validate(response_payload)
    return response.model_copy(update={"module_id": module_id, "cache_hit": True})


def write_full_prep_cache(cache_path: Path, response: ModulePrepFullResponse, cache_key: str) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps(
            {
                "cache_key": cache_key,
                "response": response.model_dump(mode="json"),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def parse_markdown_sections(text: str) -> list[ModulePrepFullSection]:
    sections: list[ModulePrepFullSection] = []
    current_title = "备团提纲"
    current_lines: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("# "):
            append_section(sections, current_title, current_lines)
            current_title = line.lstrip("#").strip() or "未命名章节"
            current_lines = []
            continue
        current_lines.append(raw_line)

    append_section(sections, current_title, current_lines)
    return sections


def append_section(sections: list[ModulePrepFullSection], title: str, lines: list[str]) -> None:
    content = "\n".join(lines).strip()
    if not content:
        return
    sections.append(ModulePrepFullSection(id=make_section_id(title, len(sections) + 1), title=title, content=content))


def parse_structured_prep(text: str) -> ModulePrepStructuredData:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        payload = json.loads(extract_json_object(text))
    return ModulePrepStructuredData.model_validate(payload)


def extract_json_object(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.IGNORECASE)
        stripped = re.sub(r"\s*```$", "", stripped)
        text = stripped
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < 0 or end <= start:
        raise ValueError("AI response did not contain a JSON object.")
    return text[start : end + 1]


def structured_to_sections(structured: ModulePrepStructuredData) -> list[ModulePrepFullSection]:
    sections = [
        ModulePrepFullSection(id="overview", title="备团总览", content=structured.overview),
        ModulePrepFullSection(id="must-know", title="跑团前必须知道", content="\n".join(structured.must_know)),
        ModulePrepFullSection(id="timeline", title="时间线", content=json.dumps([item.model_dump() for item in structured.timeline], ensure_ascii=False, indent=2)),
        ModulePrepFullSection(id="workflow", title="备团工作流", content=json.dumps([item.model_dump() for item in structured.workflow], ensure_ascii=False, indent=2)),
        ModulePrepFullSection(id="npcs", title="NPC 清单", content=json.dumps([item.model_dump() for item in structured.npcs], ensure_ascii=False, indent=2)),
        ModulePrepFullSection(id="clues", title="关键线索", content=json.dumps([item.model_dump() for item in structured.clues], ensure_ascii=False, indent=2)),
        ModulePrepFullSection(id="locations", title="地点与手牌", content="\n".join(structured.locations)),
        ModulePrepFullSection(id="risks", title="可能卡住的地方", content="\n".join(structured.risks)),
        ModulePrepFullSection(id="checklist", title="跑团前检查清单", content="\n".join(structured.checklist)),
    ]
    return [section for section in sections if section.content.strip()]


def sections_to_structured(
    sections: list[ModulePrepFullSection],
    fallback: ModulePrepStructuredData,
) -> ModulePrepStructuredData:
    # Manual text edits are preserved in sections; structured cards keep the last valid JSON shape.
    values = fallback.model_dump()
    for section in sections:
        if section.id == "overview":
            values["overview"] = section.content
        elif section.id == "must-know":
            values["must_know"] = lines_to_list(section.content)
        elif section.id == "locations":
            values["locations"] = lines_to_list(section.content)
        elif section.id == "risks":
            values["risks"] = lines_to_list(section.content)
        elif section.id == "checklist":
            values["checklist"] = lines_to_list(section.content)
        elif section.id == "timeline":
            values["timeline"] = parse_json_section(section.content, values["timeline"])
        elif section.id == "workflow":
            values["workflow"] = parse_json_section(section.content, values["workflow"])
        elif section.id == "npcs":
            values["npcs"] = parse_json_section(section.content, values["npcs"])
        elif section.id == "clues":
            values["clues"] = parse_json_section(section.content, values["clues"])
    return ModulePrepStructuredData.model_validate(values)


def parse_json_section(text: str, fallback: object) -> object:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return fallback


def lines_to_list(text: str) -> list[str]:
    return [line.strip("-* ").strip() for line in text.splitlines() if line.strip()]


def is_structured_empty(structured: ModulePrepStructuredData) -> bool:
    return not any(
        [
            structured.overview.strip(),
            structured.must_know,
            structured.timeline,
            structured.workflow,
            structured.npcs,
            structured.clues,
            structured.locations,
            structured.risks,
            structured.checklist,
        ]
    )


def make_section_id(title: str, index: int) -> str:
    normalized = re.sub(r"\W+", "-", title.lower(), flags=re.UNICODE).strip("-")
    return f"section-{index}-{normalized[:36] or 'untitled'}"


def sections_to_markdown(sections: list[ModulePrepFullSection]) -> str:
    return "\n\n".join(f"# {section.title}\n\n{section.content}".strip() for section in sections)


def read_prep_draft(draft_path: Path) -> ModulePrepDraftResponse | None:
    if not draft_path.exists():
        return None
    payload = json.loads(draft_path.read_text(encoding="utf-8"))
    return ModulePrepDraftResponse.model_validate(payload)


def write_prep_draft(draft_path: Path, draft: ModulePrepDraftResponse) -> None:
    draft_path.parent.mkdir(parents=True, exist_ok=True)
    draft_path.write_text(
        json.dumps(draft.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def thread_id_for_module(module_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"keeperkit:module-prep:{module_id}"))


def graph_config(module_id: str) -> dict[str, dict[str, str]]:
    return {"configurable": {"thread_id": thread_id_for_module(module_id)}}


def make_event_title(path: Path, lines: list[str]) -> str:
    first_line = lines[0].lstrip("# ").strip()
    if not first_line:
        return path.stem
    return first_line[:60]


def guess_title_path_from_path(path: Path) -> list[str]:
    parts = [part for part in path.with_suffix("").parts if part not in {"documents", "processed", "assets", "notes", "revisions"}]
    if len(parts) > 1:
        return parts[-2:]
    if parts:
        return [parts[-1]]
    return []


def make_node_id(kind: str, value: str) -> str:
    normalized = re.sub(r"\W+", "-", value.lower(), flags=re.UNICODE).strip("-")
    if not normalized:
        normalized = "item"
    return f"{kind}-{normalized[:48]}"


def dedupe_edges(edges: list[ModulePrepMapEdge]) -> list[ModulePrepMapEdge]:
    seen: set[tuple[str, str, str]] = set()
    results: list[ModulePrepMapEdge] = []
    for edge in edges:
        key = (edge.source_id, edge.target_id, edge.label)
        if key in seen:
            continue
        seen.add(key)
        results.append(edge)
    return results


def iterate_lines(lines: list[str] | str) -> list[str]:
    if isinstance(lines, str):
        return [line.strip() for line in lines.splitlines() if line.strip()]
    return [line.strip() for line in lines if line.strip()]
