import json
import re
from pathlib import Path

from app.config import settings
from app.schemas.modules import ModuleCreateRequest, ModuleDetail, ModuleMetadata, ModuleSummary


MODULE_FILE = "module.json"
DOCUMENTS_DIR = "documents"
PROCESSED_DIR = "processed"
INDEX_DIR = "index"
ASSETS_DIR = "assets"
NOTES_DIR = "notes"
REVISIONS_DIR = "revisions"


class ModuleService:
    def __init__(self, modules_dir: Path | None = None) -> None:
        self.modules_dir = modules_dir or settings.modules_private_dir

    def list_modules(self) -> list[ModuleSummary]:
        if not self.modules_dir.exists():
            return []

        modules: list[ModuleSummary] = []
        for module_dir in sorted(path for path in self.modules_dir.iterdir() if path.is_dir()):
            metadata = self._read_metadata(module_dir)
            if metadata is None:
                continue
            modules.append(self._build_summary(module_dir, metadata))
        return modules

    def get_module(self, module_id: str) -> ModuleDetail:
        module_dir = self._module_dir(module_id)
        metadata = self._read_metadata(module_dir)
        if metadata is None:
            raise FileNotFoundError(f"Module not found: {module_id}")
        return self._build_detail(module_dir, metadata)

    def create_module(self, request: ModuleCreateRequest) -> ModuleDetail:
        module_dir = self._module_dir(request.id)
        module_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_module_dirs(module_dir)
        metadata = ModuleMetadata(**request.model_dump())
        self._write_metadata(module_dir, metadata)
        return self._build_detail(module_dir, metadata)

    def module_exists(self, module_id: str) -> bool:
        module_dir = self._module_dir(module_id)
        return self._read_metadata(module_dir) is not None

    def save_document(self, module_id: str, filename: str, content: bytes) -> Path:
        self.get_module(module_id)
        safe_name = sanitize_filename(filename)
        suffix = Path(safe_name).suffix.lower()
        if suffix not in {".md", ".markdown", ".txt", ".pdf"}:
            raise ValueError(f"Unsupported module document type: {suffix}")
        documents_dir = self.module_paths(module_id)["documents_dir"]
        documents_dir.mkdir(parents=True, exist_ok=True)
        output_path = documents_dir / safe_name
        output_path.write_bytes(content)
        return output_path

    def module_paths(self, module_id: str) -> dict[str, Path]:
        module_dir = self._module_dir(module_id)
        return {
            "module_dir": module_dir,
            "documents_dir": module_dir / DOCUMENTS_DIR,
            "processed_dir": module_dir / PROCESSED_DIR,
            "index_dir": module_dir / INDEX_DIR,
            "assets_dir": module_dir / ASSETS_DIR,
            "notes_dir": module_dir / NOTES_DIR,
            "revisions_dir": module_dir / REVISIONS_DIR,
        }

    def _build_summary(self, module_dir: Path, metadata: ModuleMetadata) -> ModuleSummary:
        documents_dir = module_dir / DOCUMENTS_DIR
        document_count = self._count_documents(documents_dir)
        index_ready = self._index_ready(module_dir / INDEX_DIR)
        return ModuleSummary(
            **metadata.model_dump(),
            has_documents=document_count > 0,
            document_count=document_count,
            index_ready=index_ready,
        )

    def _build_detail(self, module_dir: Path, metadata: ModuleMetadata) -> ModuleDetail:
        summary = self._build_summary(module_dir, metadata)
        return ModuleDetail(
            **summary.model_dump(),
            module_dir=str(module_dir),
            documents_dir=str(module_dir / DOCUMENTS_DIR),
            processed_dir=str(module_dir / PROCESSED_DIR),
            index_dir=str(module_dir / INDEX_DIR),
        )

    def _module_dir(self, module_id: str) -> Path:
        return self.modules_dir / module_id

    def _read_metadata(self, module_dir: Path) -> ModuleMetadata | None:
        metadata_path = module_dir / MODULE_FILE
        if not metadata_path.exists():
            return None
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        return ModuleMetadata.model_validate(payload)

    def _write_metadata(self, module_dir: Path, metadata: ModuleMetadata) -> None:
        metadata_path = module_dir / MODULE_FILE
        metadata_path.write_text(
            json.dumps(metadata.model_dump(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _ensure_module_dirs(self, module_dir: Path) -> None:
        for child in (DOCUMENTS_DIR, PROCESSED_DIR, INDEX_DIR, ASSETS_DIR, NOTES_DIR, REVISIONS_DIR):
            (module_dir / child).mkdir(parents=True, exist_ok=True)

    def _count_documents(self, documents_dir: Path) -> int:
        if not documents_dir.exists():
            return 0
        return sum(1 for path in documents_dir.rglob("*") if path.is_file())

    def _index_ready(self, index_dir: Path) -> bool:
        if not index_dir.exists():
            return False
        return any(path.is_file() for path in index_dir.rglob("*"))


def sanitize_filename(filename: str) -> str:
    name = Path(filename).name.strip()
    if not name:
        raise ValueError("Document filename cannot be empty.")
    return re.sub(r"[^\w.\-\u4e00-\u9fff]+", "_", name)
