import json

from app.schemas.modules import ModuleAskRequest
from app.services.module_ingest_service import ModuleIngestService
from app.services.module_qa_service import ModuleQAService
from app.services.module_structure_service import ModuleStructureService
from app.services.module_service import ModuleService


def test_module_ingest_and_ask_round_trip(tmp_path, monkeypatch) -> None:
    module_service = ModuleService(modules_dir=tmp_path)
    module_service.create_module(
        __import__("app.schemas.modules", fromlist=["ModuleCreateRequest"]).ModuleCreateRequest(
            id="demo_module",
            title="演示模组",
            system="coc7",
            language="zh",
            keeper_notes="notes",
            spoiler_level="keeper_only",
        )
    )

    documents_dir = tmp_path / "demo_module" / "documents"
    (documents_dir / "scene.md").write_text("# 场景\n\n书房里藏着一把钥匙。", encoding="utf-8")

    ingest_result = ModuleIngestService(module_service).ingest("demo_module")
    assert ingest_result["document_count"] == 1
    assert ingest_result["chunk_count"] >= 1

    response = ModuleQAService(module_service).ask(
        "demo_module",
        ModuleAskRequest(question="书房里有什么？", top_k=5, rerank_top_k=3),
    )

    assert response.answer
    assert response.sources
    assert response.sources[0].module_id == "demo_module"

    structure = ModuleStructureService(module_service).inspect("demo_module")
    assert structure.module_id == "demo_module"
    assert structure.groups
    assert structure.groups[0].items
