from typing import Protocol

from openai import OpenAI

from app.config import settings
from app.rag.module_prompts import build_module_prompt
from app.rag.types import RetrievedChunk


class ModuleGenerator(Protocol):
    def generate(
        self,
        question: str,
        contexts: list[RetrievedChunk],
        retrieval_question: str | None = None,
        query_notes: list[str] | None = None,
    ) -> str:
        ...


class TemplateModuleGenerator:
    def generate(
        self,
        question: str,
        contexts: list[RetrievedChunk],
        retrieval_question: str | None = None,
        query_notes: list[str] | None = None,
    ) -> str:
        if not contexts:
            return "当前模组资料中未检索到明确依据。请换一种更接近模组内容的问法。"

        preview_lines = []
        for index, item in enumerate(contexts, start=1):
            title_path = item.chunk.metadata.get("title_path", [])
            title = " / ".join(title_path) if isinstance(title_path, list) else str(title_path)
            preview = item.chunk.content[:260].replace("\n", " ")
            preview_lines.append(f"{index}. {title or item.chunk.metadata.get('source', 'unknown')}: {preview}")

        _ = build_module_prompt(
            question,
            [item.chunk.content for item in contexts],
            retrieval_question=retrieval_question,
            query_notes=query_notes,
        )
        return "我先返回检索到的模组依据。\n\n" + "\n".join(preview_lines)


class LLMModuleGenerator:
    def __init__(self) -> None:
        if not settings.llm_api_key or settings.llm_api_key == "replace-me":
            raise ValueError("LLM_API_KEY is required when GENERATOR_PROVIDER=llm.")
        self.client = OpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
        )

    def generate(
        self,
        question: str,
        contexts: list[RetrievedChunk],
        retrieval_question: str | None = None,
        query_notes: list[str] | None = None,
    ) -> str:
        if not contexts:
            return "当前模组资料中未检索到明确依据。请换一种更接近模组内容的问法。"

        context_texts = []
        for index, item in enumerate(contexts, start=1):
            source = item.chunk.metadata.get("source", "unknown")
            title_path = item.chunk.metadata.get("title_path", [])
            title = " / ".join(title_path) if isinstance(title_path, list) else str(title_path)
            context_texts.append(
                f"[片段 {index}]\n来源：{source}\n标题：{title}\n内容：\n{item.chunk.content}"
            )

        prompt = build_module_prompt(
            question,
            context_texts,
            retrieval_question=retrieval_question,
            query_notes=query_notes,
        )
        response = self.client.chat.completions.create(
            model=settings.llm_model,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}],
        )
        answer = response.choices[0].message.content
        if not answer:
            raise RuntimeError("LLM returned an empty answer.")
        return answer


def create_module_generator(provider: str) -> ModuleGenerator:
    normalized_provider = provider.lower().strip()
    if normalized_provider == "template":
        return TemplateModuleGenerator()
    if normalized_provider == "llm":
        return LLMModuleGenerator()
    raise ValueError(f"Unsupported generator provider: {provider}")
