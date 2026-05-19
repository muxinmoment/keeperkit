from app.rag.prompts import build_rule_prompt
from app.rag.types import RetrievedChunk


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
