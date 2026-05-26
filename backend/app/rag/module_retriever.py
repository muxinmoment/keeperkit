from pathlib import Path

from app.config import settings
from app.rag.embeddings import create_embedding_model
from app.rag.types import RetrievedChunk
from app.rag.vector_store_factory import create_vector_store


class ModuleRetriever:
    def __init__(self, index_dir: Path, module_id: str) -> None:
        embedding_model = create_embedding_model(
            provider=settings.embedding_provider,
            model_name=settings.embedding_model,
        )
        self.vector_store = create_vector_store(
            provider=settings.vector_store_provider,
            index_dir=index_dir,
            embedding_model=embedding_model,
            collection_name=f"keeperkit_module_{module_id}",
        )

    def retrieve(self, question: str, top_k: int) -> list[RetrievedChunk]:
        return self.vector_store.search(question, top_k=top_k)
