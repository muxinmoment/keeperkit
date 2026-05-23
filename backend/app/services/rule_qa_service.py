from app.config import settings
from app.rag.generator import create_rule_generator
from app.rag.reranker import SimpleReranker
from app.rag.retriever import RuleRetriever
from app.schemas.rules import RuleAskRequest, RuleAskResponse, Source


class RuleQAService:
    def __init__(self) -> None:
        self.retriever = RuleRetriever(index_dir=settings.index_dir)
        self.reranker = SimpleReranker()
        self.generator = create_rule_generator(settings.generator_provider)

    def ask(self, request: RuleAskRequest) -> RuleAskResponse:
        top_k = request.top_k or settings.retrieval_top_k
        rerank_top_k = request.rerank_top_k or settings.rerank_top_k
        candidates = self.retriever.retrieve(request.question, top_k=top_k)
        selected = self.reranker.rerank(request.question, candidates, top_k=rerank_top_k)
        answer = self.generator.generate(request.question, selected)
        sources = [
            Source(
                source=str(item.chunk.metadata.get("source", "unknown")),
                title_path=item.chunk.metadata.get("title_path", []),
                score=round(item.score, 4),
                content_preview=item.chunk.content[:180].replace("\n", " "),
            )
            for item in selected
        ]
        return RuleAskResponse(answer=answer, sources=sources)
