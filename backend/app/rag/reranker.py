from app.rag.types import RetrievedChunk


class SimpleReranker:
    def rerank(
        self,
        question: str,
        candidates: list[RetrievedChunk],
        top_k: int,
    ) -> list[RetrievedChunk]:
        _ = question
        return sorted(candidates, key=lambda item: item.score, reverse=True)[:top_k]
