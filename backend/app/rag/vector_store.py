import json
import math
from pathlib import Path

from app.rag.embeddings import HashEmbeddingModel
from app.rag.types import DocumentChunk, RetrievedChunk


class JsonVectorStore:
    def __init__(self, index_dir: Path, embedding_model: HashEmbeddingModel | None = None) -> None:
        self.index_dir = index_dir
        self.index_file = index_dir / "chunks.json"
        self.embedding_model = embedding_model or HashEmbeddingModel()

    def save(self, chunks: list[DocumentChunk]) -> None:
        self.index_dir.mkdir(parents=True, exist_ok=True)
        records = [
            {
                "id": chunk.id,
                "content": chunk.content,
                "metadata": chunk.metadata,
                "embedding": self.embedding_model.embed(chunk.content),
            }
            for chunk in chunks
        ]
        self.index_file.write_text(
            json.dumps(records, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def search(self, query: str, top_k: int) -> list[RetrievedChunk]:
        if not self.index_file.exists():
            raise FileNotFoundError(
                f"Index file does not exist: {self.index_file}. Run scripts/ingest_rules.py first."
            )

        query_embedding = self.embedding_model.embed(query)
        records = json.loads(self.index_file.read_text(encoding="utf-8"))
        scored: list[RetrievedChunk] = []
        for record in records:
            chunk = DocumentChunk(
                id=record["id"],
                content=record["content"],
                metadata=record.get("metadata", {}),
            )
            score = cosine_similarity(query_embedding, record["embedding"])
            scored.append(RetrievedChunk(chunk=chunk, score=score))

        return sorted(scored, key=lambda item: item.score, reverse=True)[:top_k]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("Embedding dimensions do not match.")
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)
