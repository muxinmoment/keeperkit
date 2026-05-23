import math
from typing import Protocol

from app.rag.types import RetrievedChunk


class Reranker(Protocol):
    def rerank(
        self,
        question: str,
        candidates: list[RetrievedChunk],
        top_k: int,
    ) -> list[RetrievedChunk]:
        ...


class SimpleReranker:
    def rerank(
        self,
        question: str,
        candidates: list[RetrievedChunk],
        top_k: int,
    ) -> list[RetrievedChunk]:
        _ = question
        return sorted(candidates, key=lambda item: item.score, reverse=True)[:top_k]


class BGEReranker:
    def __init__(self, model_name: str) -> None:
        try:
            from sentence_transformers import CrossEncoder
        except ImportError as exc:
            raise RuntimeError(
                "Missing dependency: sentence-transformers. Install it with: "
                "pip install sentence-transformers"
            ) from exc

        self.model_name = model_name
        self.model = CrossEncoder(model_name)

    def rerank(
        self,
        question: str,
        candidates: list[RetrievedChunk],
        top_k: int,
    ) -> list[RetrievedChunk]:
        if not candidates:
            return []

        pairs = [(question, candidate.chunk.content) for candidate in candidates]
        scores = self.model.predict(pairs, show_progress_bar=False)
        reranked = [
            RetrievedChunk(chunk=candidate.chunk, score=sigmoid(float(score)))
            for candidate, score in zip(candidates, scores, strict=True)
        ]
        return sorted(reranked, key=lambda item: item.score, reverse=True)[:top_k]


def create_reranker(provider: str, model_name: str) -> Reranker:
    normalized_provider = provider.lower().strip()
    if normalized_provider == "simple":
        return SimpleReranker()
    if normalized_provider in {"bge", "sentence_transformers", "sentence-transformers"}:
        return BGEReranker(model_name=model_name)
    raise ValueError(f"Unsupported reranker provider: {provider} ({model_name})")


def sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)
