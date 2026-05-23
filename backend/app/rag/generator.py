from typing import Protocol

from openai import OpenAI

from app.config import settings
from app.rag.prompts import build_rule_prompt
from app.rag.types import RetrievedChunk


class RuleGenerator(Protocol):
    def generate(self, question: str, contexts: list[RetrievedChunk]) -> str:
        ...


class TemplateRuleGenerator:
    """Development generator that keeps answers grounded before wiring an LLM."""

    def generate(self, question: str, contexts: list[RetrievedChunk]) -> str:
        if not contexts:
            return "当前规则资料中未检索到明确依据。"

        preview_lines = []
        for index, item in enumerate(contexts, start=1):
            title_path = item.chunk.metadata.get("title_path", [])
            title = " / ".join(title_path) if isinstance(title_path, list) else str(title_path)
            preview = item.chunk.content[:260].replace("\n", " ")
            preview_lines.append(f"{index}. {title or item.chunk.metadata.get('source', 'unknown')}: {preview}")

        _ = build_rule_prompt(question, [item.chunk.content for item in contexts])
        return (
            "我先返回检索到的规则依据。接入 LLM 后，这里会生成结构化回答。\n\n"
            + "\n".join(preview_lines)
        )


class LLMRuleGenerator:
    def __init__(self) -> None:
        if not settings.llm_api_key or settings.llm_api_key == "replace-me":
            raise ValueError("LLM_API_KEY is required when GENERATOR_PROVIDER=llm.")
        self.client = OpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
        )

    def generate(self, question: str, contexts: list[RetrievedChunk]) -> str:
        if not contexts:
            return "当前规则资料中未检索到明确依据。"

        context_texts = []
        for index, item in enumerate(contexts, start=1):
            source = item.chunk.metadata.get("source", "unknown")
            title_path = item.chunk.metadata.get("title_path", [])
            title = " / ".join(title_path) if isinstance(title_path, list) else str(title_path)
            context_texts.append(
                f"[片段 {index}]\n来源：{source}\n标题：{title}\n内容：\n{item.chunk.content}"
            )

        prompt = build_rule_prompt(question, context_texts)
        response = self.client.chat.completions.create(
            model=settings.llm_model,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}],
        )
        answer = response.choices[0].message.content
        if not answer:
            raise RuntimeError("LLM returned an empty answer.")
        return answer


def create_rule_generator(provider: str) -> RuleGenerator:
    normalized_provider = provider.lower().strip()
    if normalized_provider == "template":
        return TemplateRuleGenerator()
    if normalized_provider == "llm":
        return LLMRuleGenerator()
    raise ValueError(f"Unsupported generator provider: {provider}")
