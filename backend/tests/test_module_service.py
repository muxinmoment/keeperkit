from app.schemas.modules import ModuleCreateRequest
from app.services.module_service import ModuleService


def test_module_service_creates_and_lists_modules(tmp_path) -> None:
    service = ModuleService(modules_dir=tmp_path)

    created = service.create_module(
        ModuleCreateRequest(
            id="demo_module",
            title="演示模组",
            system="coc7",
            language="zh",
            keeper_notes="keep notes",
            spoiler_level="keeper_only",
        )
    )

    assert created.id == "demo_module"
    assert (tmp_path / "demo_module" / "module.json").exists()
    assert (tmp_path / "demo_module" / "documents").exists()

    modules = service.list_modules()
    assert len(modules) == 1
    assert modules[0].title == "演示模组"
    assert modules[0].has_documents is False
    assert modules[0].index_ready is True


def test_module_service_ignores_modules_without_metadata(tmp_path) -> None:
    (tmp_path / "broken").mkdir()

    service = ModuleService(modules_dir=tmp_path)

    assert service.list_modules() == []
