from app.config import settings
from app.rag.module_generator import create_module_generator
from app.rag.module_retriever import ModuleRetriever
from app.schemas.modules import ModuleAskRequest, ModuleAskResponse, ModuleSource
from app.services.module_service import ModuleService


class ModuleQAService:
    def __init__(self, module_service: ModuleService | None = None) -> None:
        self.module_service = module_service or ModuleService()
        self.generator = create_module_generator(settings.generator_provider)

    def ask(self, module_id: str, request: ModuleAskRequest) -> ModuleAskResponse:
        self.module_service.get_module(module_id)
        paths = self.module_service.module_paths(module_id)
        retriever = ModuleRetriever(index_dir=paths["index_dir"], module_id=module_id)

        top_k = request.top_k or settings.retrieval_top_k
        rerank_top_k = request.rerank_top_k or settings.rerank_top_k
        candidates = retriever.retrieve(request.question, top_k=top_k)
        selected = sorted(candidates, key=lambda item: item.score, reverse=True)[:rerank_top_k]
        answer = self.generator.generate(request.question, selected)
        sources = [
            ModuleSource(
                knowledge_base=str(item.chunk.metadata.get("knowledge_base", "module")),
                module_id=str(item.chunk.metadata.get("module_id", module_id)),
                source=str(item.chunk.metadata.get("source", "unknown")),
                title_path=item.chunk.metadata.get("title_path", []),
                content_type=str(item.chunk.metadata.get("content_type", "document")),
                spoiler_level=str(item.chunk.metadata.get("spoiler_level", "keeper_only")),
                score=round(item.score, 4),
                content_preview=item.chunk.content[:180].replace("\n", " "),
            )
            for item in selected
        ]
        return ModuleAskResponse(answer=answer, sources=sources)
