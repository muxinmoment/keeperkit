from pathlib import Path

from app.rag.embeddings import EmbeddingModel
from app.rag.types import DocumentChunk, RetrievedChunk


class ChromaVectorStore:
    def __init__(
        self,
        index_dir: Path,
        embedding_model: EmbeddingModel,
        collection_name: str,
    ) -> None:
        try:
            import chromadb
        except ImportError as exc:
            raise RuntimeError("Missing dependency: chromadb. Install it with: pip install chromadb") from exc

        self.index_dir = index_dir
        self.embedding_model = embedding_model
        self.client = chromadb.PersistentClient(path=str(index_dir))
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def save(self, chunks: list[DocumentChunk]) -> None:
        self.index_dir.mkdir(parents=True, exist_ok=True)
        if self.collection.count() > 0:
            existing = self.collection.get(include=[])
            ids = existing.get("ids", [])
            if ids:
                self.collection.delete(ids=ids)

        batch_size = 64
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            embeddings = self.embedding_model.embed_batch([chunk.content for chunk in batch])
            self.collection.add(
                ids=[chunk.id for chunk in batch],
                documents=[chunk.content for chunk in batch],
                metadatas=[flatten_metadata(chunk.metadata) for chunk in batch],
                embeddings=embeddings,
            )

    def search(self, query: str, top_k: int) -> list[RetrievedChunk]:
        query_embedding = self.embedding_model.embed(query)
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        retrieved: list[RetrievedChunk] = []
        for chunk_id, document, metadata, distance in zip(ids, documents, metadatas, distances, strict=True):
            chunk = DocumentChunk(
                id=chunk_id,
                content=document,
                metadata=unflatten_metadata(metadata or {}),
            )
            retrieved.append(RetrievedChunk(chunk=chunk, score=1.0 - float(distance)))
        return retrieved


def flatten_metadata(metadata: dict[str, str | list[str]]) -> dict[str, str | int | float | bool]:
    flattened: dict[str, str | int | float | bool] = {}
    for key, value in metadata.items():
        if isinstance(value, list):
            flattened[key] = " / ".join(str(item) for item in value)
        elif value is None:
            continue
        else:
            flattened[key] = str(value)
    return flattened


def unflatten_metadata(metadata: dict[str, str | int | float | bool]) -> dict[str, str | list[str]]:
    restored: dict[str, str | list[str]] = {}
    for key, value in metadata.items():
        if key == "title_path" and isinstance(value, str):
            restored[key] = [part.strip() for part in value.split("/") if part.strip()]
        else:
            restored[key] = str(value)
    return restored
