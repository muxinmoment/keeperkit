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

    assert timeline.module_id == "demo_module"
    assert timeline.events
    assert timeline.events[0].location == "书房"
    assert timeline.events[0].npcs
    assert summary.module_id == "demo_module"
    assert summary.highlights
    assert summary.clues
    assert summary.npcs
