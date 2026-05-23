from pathlib import Path

from app.config import settings
from app.rag.chroma_store import ChromaVectorStore
from app.rag.embeddings import EmbeddingModel
from app.rag.vector_store import JsonVectorStore


def create_vector_store(
    provider: str,
    index_dir: Path,
    embedding_model: EmbeddingModel,
) -> JsonVectorStore:
    normalized_provider = provider.lower().strip()
    if normalized_provider == "json":
        return JsonVectorStore(index_dir=index_dir, embedding_model=embedding_model)
    if normalized_provider == "chroma":
        return ChromaVectorStore(
            index_dir=index_dir,
            embedding_model=embedding_model,
            collection_name=settings.chroma_collection,
        )
    raise ValueError(f"Unsupported vector store provider: {provider}")
