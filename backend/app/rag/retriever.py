from pathlib import Path

from app.rag.types import RetrievedChunk
from app.rag.vector_store import JsonVectorStore


class RuleRetriever:
    def __init__(self, index_dir: Path) -> None:
        self.vector_store = JsonVectorStore(index_dir=index_dir)

    def retrieve(self, question: str, top_k: int) -> list[RetrievedChunk]:
        return self.vector_store.search(question, top_k=top_k)
