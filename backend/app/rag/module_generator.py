from typing import Protocol
import json

from openai import OpenAI

from app.config import settings
from app.rag.module_prompts import (
    build_full_module_prep_prompt,
    build_module_prompt,
    build_revise_prep_section_prompt,
)
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

    def generate_from_documents(self, module_title: str, documents: list[str]) -> str:
        ...

    def revise_prep_section(
        self,
        module_title: str,
        section_title: str,
        section_content: str,
        instruction: str,
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

    def generate_from_documents(self, module_title: str, documents: list[str]) -> str:
        if not documents:
            return json.dumps(
                {
                    "overview": "当前模组还没有可整理的全文资料。",
                    "must_know": [],
                    "timeline": [],
                    "workflow": [],
                    "npcs": [],
                    "clues": [],
                    "locations": [],
                    "risks": [],
                    "checklist": [],
                },
                ensure_ascii=False,
            )

        preview_lines = []
        for index, document in enumerate(documents, start=1):
            preview = document[:420].replace("\n", " ")
            preview_lines.append(f"{index}. {preview}")
        return json.dumps(
            {
                "overview": f"{module_title} 已读取全文资料。接入 LLM 后，这里会生成完整结构化备团数据。",
                "must_know": preview_lines[:3],
                "timeline": [],
                "workflow": [{"id": "workflow-1", "title": "读取资料", "goal": "确认模组全文已经进入备团会话", "next_steps": []}],
                "npcs": [],
                "clues": [],
                "locations": [],
                "risks": [],
                "checklist": ["接入 LLM 后重新生成结构化备团数据"],
            },
            ensure_ascii=False,
        )

    def revise_prep_section(
        self,
        module_title: str,
        section_title: str,
        section_content: str,
        instruction: str,
    ) -> str:
        return f"{section_content}\n\nAI 修改提示：{instruction}"


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

    def generate_from_documents(self, module_title: str, documents: list[str]) -> str:
        if not documents:
            return json.dumps(
                {
                    "overview": "当前模组还没有可整理的全文资料。",
                    "must_know": [],
                    "timeline": [],
                    "workflow": [],
                    "npcs": [],
                    "clues": [],
                    "locations": [],
                    "risks": [],
                    "checklist": [],
                },
                ensure_ascii=False,
            )

        prompt = build_full_module_prep_prompt(module_title, documents)
        response = self.client.chat.completions.create(
            model=settings.llm_model,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}],
        )
        answer = response.choices[0].message.content
        if not answer:
            raise RuntimeError("LLM returned an empty answer.")
        return answer

    def revise_prep_section(
        self,
        module_title: str,
        section_title: str,
        section_content: str,
        instruction: str,
    ) -> str:
        prompt = build_revise_prep_section_prompt(
            module_title=module_title,
            section_title=section_title,
            section_content=section_content,
            instruction=instruction,
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
