from app.schemas.modules import ModuleCreateRequest
from app.services.module_prep_service import ModulePrepService
from app.services.module_service import ModuleService


def test_module_prep_service_builds_timeline_and_summary(tmp_path) -> None:
    service = ModuleService(modules_dir=tmp_path)
    service.create_module(ModuleCreateRequest(id="demo_module", title="演示模组"))

    documents_dir = tmp_path / "demo_module" / "documents"
    (documents_dir / "scene.md").write_text(
        "# 场景一\n\n地点：书房\nNPC：教授\n线索：日记\n触发条件：玩家进入房间。",
        encoding="utf-8",
    )
    (documents_dir / "timeline.md").write_text(
        "# 时间线\n\n线索：失踪事件\n角色：管家\n",
        encoding="utf-8",
    )

    prep_service = ModulePrepService(service)
    timeline = prep_service.build_timeline("demo_module")
    summary = prep_service.build_prep_summary("demo_module")
    prep_map = prep_service.build_prep_map("demo_module")
    full_prep = prep_service.build_full_prep("demo_module")

    assert timeline.module_id == "demo_module"
    assert timeline.events
    assert timeline.events[0].location == "书房"
    assert timeline.events[0].npcs
    assert summary.module_id == "demo_module"
    assert summary.highlights
    assert summary.clues
    assert summary.npcs
    assert prep_map.module_id == "demo_module"
    assert any(node.kind == "scene" for node in prep_map.nodes)
    assert any(node.kind == "npc" and node.label == "教授" for node in prep_map.nodes)
    assert any(node.kind == "clue" and node.label == "日记" for node in prep_map.nodes)
    assert any(edge.label == "可获得" for edge in prep_map.edges)
    assert full_prep.document_count == 2
    assert full_prep.character_count > 0
    assert full_prep.sources
    assert "全文" in full_prep.answer or "预览" in full_prep.answer


def test_module_prep_service_reads_pdf_text(tmp_path) -> None:
    service = ModuleService(modules_dir=tmp_path)
    service.create_module(ModuleCreateRequest(id="pdf_module", title="PDF 模组"))

    documents_dir = tmp_path / "pdf_module" / "documents"
    create_pdf(
        documents_dir / "scene.pdf",
        "scene: old house\nlocation: hall\nNPC: missing professor\nclue: bloody key",
    )

    summary = ModulePrepService(service).build_prep_summary("pdf_module")

    assert summary.clues
    assert summary.npcs
    assert "bloody key" in summary.clues[0].title
    assert "missing professor" in summary.npcs[0].title


def create_pdf(path, text: str) -> None:
    import fitz

    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    document.save(path)
    document.close()
