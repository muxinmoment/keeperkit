import sys
from types import SimpleNamespace

from app.rag.reranker import BGEReranker, SimpleReranker
from app.rag.types import DocumentChunk, RetrievedChunk


def make_result(content: str, score: float) -> RetrievedChunk:
    return RetrievedChunk(
        chunk=DocumentChunk(id=content, content=content, metadata={}),
        score=score,
    )


def test_simple_reranker_keeps_highest_scores() -> None:
    candidates = [
        make_result("low", 0.1),
        make_result("high", 0.9),
        make_result("middle", 0.5),
    ]

    results = SimpleReranker().rerank("question", candidates, top_k=2)

    assert [item.chunk.id for item in results] == ["high", "middle"]


def test_bge_reranker_uses_cross_encoder_scores(monkeypatch) -> None:
    class FakeCrossEncoder:
        def __init__(self, model_name: str) -> None:
            self.model_name = model_name

        def predict(self, pairs, show_progress_bar: bool):
            assert show_progress_bar is False
            assert pairs == [
                ("question", "first"),
                ("question", "second"),
            ]
            return [-2.0, 2.0]

    monkeypatch.setitem(
        sys.modules,
        "sentence_transformers",
        SimpleNamespace(CrossEncoder=FakeCrossEncoder),
    )

    reranker = BGEReranker(model_name="fake-bge-reranker")
    results = reranker.rerank(
        "question",
        [
            make_result("first", 0.9),
            make_result("second", 0.1),
        ],
        top_k=1,
    )

    assert [item.chunk.id for item in results] == ["second"]
    assert 0.88 < results[0].score < 0.89
