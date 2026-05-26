import json

from app.rag.module_loader import load_module_documents


def test_load_module_documents_reads_markdown(tmp_path) -> None:
    module_dir = tmp_path / "demo_module"
    documents_dir = module_dir / "documents"
    documents_dir.mkdir(parents=True)
    (module_dir / "module.json").write_text(
        json.dumps(
            {
                "id": "demo_module",
                "title": "演示模组",
                "system": "coc7",
                "language": "zh",
                "spoiler_level": "keeper_only",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (documents_dir / "01_scene.md").write_text("# 场景\n\n这里是开场。", encoding="utf-8")

    documents = load_module_documents(module_dir)

    assert len(documents) == 1
    assert documents[0].metadata["module_id"] == "demo_module"
    assert documents[0].metadata["content_type"] == "scene"
    assert documents[0].metadata["source"] == "01_scene.md"
