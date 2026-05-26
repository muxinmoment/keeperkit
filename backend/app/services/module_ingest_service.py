from app.config import settings
from app.rag.embeddings import create_embedding_model
from app.rag.module_loader import load_module_documents
from app.rag.splitter import split_documents
from app.rag.vector_store_factory import create_vector_store
from app.services.module_service import ModuleService


class ModuleIngestService:
    def __init__(self, module_service: ModuleService | None = None) -> None:
        self.module_service = module_service or ModuleService()

    def ingest(self, module_id: str) -> dict[str, int | str]:
        module_detail = self.module_service.get_module(module_id)
        paths = self.module_service.module_paths(module_id)
        documents = load_module_documents(paths["module_dir"])
        chunks = split_documents(documents)
        embedding_model = create_embedding_model(
            provider=settings.embedding_provider,
            model_name=settings.embedding_model,
        )
        vector_store = create_vector_store(
            provider=settings.vector_store_provider,
            index_dir=paths["index_dir"],
            embedding_model=embedding_model,
            collection_name=f"keeperkit_module_{module_id}",
        )
        vector_store.save(chunks)
        return {
            "module_id": module_detail.id,
            "document_count": len(documents),
            "chunk_count": len(chunks),
            "index_dir": str(paths["index_dir"]),
        }
