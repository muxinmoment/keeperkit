from app.config import settings
from app.rag.generator import create_rule_generator
from app.rag.query_rewriter import rewrite_rule_query
from app.rag.reranker import create_reranker
from app.rag.retriever import RuleRetriever
from app.schemas.rules import RuleAskRequest, RuleAskResponse, Source


class RuleQAService:
    def __init__(self) -> None:
        self.retriever = RuleRetriever(index_dir=settings.index_dir)
        self.reranker = create_reranker(
            provider=settings.reranker_provider,
            model_name=settings.reranker_model,
        )
        self.generator = create_rule_generator(settings.generator_provider)

    def ask(self, request: RuleAskRequest) -> RuleAskResponse:
        top_k = request.top_k or settings.retrieval_top_k
        rerank_top_k = request.rerank_top_k or settings.rerank_top_k
        rewrite = rewrite_rule_query(request.question)
        query_notes = build_query_notes(rewrite.matched_terms, rewrite.added_terms)
        candidates = self.retriever.retrieve(rewrite.retrieval_question, top_k=top_k)
        selected = self.reranker.rerank(rewrite.retrieval_question, candidates, top_k=rerank_top_k)
        answer = self.generator.generate(
            request.question,
            selected,
            retrieval_question=rewrite.retrieval_question,
            query_notes=query_notes,
        )
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


def build_query_notes(matched_terms: list[str], added_terms: list[str]) -> list[str]:
    if not matched_terms:
        return []
    return [
        "用户问题包含常见 TRPG 黑话："
        f"{'、'.join(matched_terms)}；检索时已补充规则书常用说法：{'、'.join(added_terms)}。"
    ]
