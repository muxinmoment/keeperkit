import json

from app.schemas.modules import ModuleCreateRequest
from app.services.module_structure_service import ModuleStructureService
from app.services.module_service import ModuleService


def test_module_structure_service_groups_documents(tmp_path) -> None:
    service = ModuleService(modules_dir=tmp_path)
    service.create_module(ModuleCreateRequest(id="demo_module", title="演示模组"))

    documents_dir = tmp_path / "demo_module" / "documents"
    (documents_dir / "scene.md").write_text("# 场景\n\n这里是场景。", encoding="utf-8")
    (documents_dir / "npc_note.md").write_text("# NPC\n\n这里是 NPC。", encoding="utf-8")

    response = ModuleStructureService(service).inspect("demo_module")

    assert response.module_id == "demo_module"
    assert response.groups
    assert any(group.content_type == "scene" for group in response.groups)
    assert any(group.content_type == "npc" for group in response.groups)
