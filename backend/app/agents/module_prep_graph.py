from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Literal, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph

from app.config import settings
from app.rag.module_generator import ModuleGenerator


class PrepDraftGraphState(TypedDict, total=False):
    action: Literal["generate", "revise"]
    module_title: str
    documents: list[str]
    answer: str
    sections: list[dict[str, str]]
    section_id: str
    instruction: str
    revision_history: list[dict[str, str]]


_POSTGRES_CHECKPOINTER: PostgresSaver | None = None
_POSTGRES_CHECKPOINTER_CONTEXT: AbstractContextManager[PostgresSaver] | None = None


def create_module_prep_graph(generator: ModuleGenerator):
    graph = StateGraph(PrepDraftGraphState)

    def route(state: PrepDraftGraphState) -> str:
        return state.get("action", "generate")

    def generate_draft(state: PrepDraftGraphState) -> PrepDraftGraphState:
        answer = generator.generate_from_documents(
            state.get("module_title", ""),
            state.get("documents", []),
        )
        return {"answer": answer}

    def revise_section(state: PrepDraftGraphState) -> PrepDraftGraphState:
        section_id = state.get("section_id", "")
        sections = [dict(section) for section in state.get("sections", [])]
        target_index = next(
            (index for index, section in enumerate(sections) if section.get("id") == section_id),
            None,
        )
        if target_index is None:
            raise ValueError(f"Prep section not found: {section_id}")

        target = sections[target_index]
        revised_content = generator.revise_prep_section(
            module_title=state.get("module_title", ""),
            section_title=target.get("title", ""),
            section_content=target.get("content", ""),
            instruction=state.get("instruction", ""),
        )
        sections[target_index] = {**target, "content": revised_content}
        history = list(state.get("revision_history", []))
        history.append(
            {
                "section_id": section_id,
                "instruction": state.get("instruction", ""),
                "result_preview": revised_content[:240],
            }
        )
        return {
            "sections": sections,
            "revision_history": history,
        }

    graph.add_node("generate_draft", generate_draft)
    graph.add_node("revise_section", revise_section)
    graph.add_conditional_edges(
        START,
        route,
        {
            "generate": "generate_draft",
            "revise": "revise_section",
        },
    )
    graph.add_edge("generate_draft", END)
    graph.add_edge("revise_section", END)
    return graph.compile(checkpointer=create_checkpointer())


def create_checkpointer():
    if settings.langgraph_checkpointer.lower() == "postgres":
        return get_postgres_checkpointer()
    return MemorySaver()


def get_postgres_checkpointer() -> PostgresSaver:
    global _POSTGRES_CHECKPOINTER, _POSTGRES_CHECKPOINTER_CONTEXT
    if _POSTGRES_CHECKPOINTER is not None:
        return _POSTGRES_CHECKPOINTER
    if not settings.langgraph_postgres_uri:
        raise ValueError("LANGGRAPH_POSTGRES_URI is required when LANGGRAPH_CHECKPOINTER=postgres.")
    _POSTGRES_CHECKPOINTER_CONTEXT = PostgresSaver.from_conn_string(settings.langgraph_postgres_uri)
    saver = _POSTGRES_CHECKPOINTER_CONTEXT.__enter__()
    saver.setup()
    _POSTGRES_CHECKPOINTER = saver
    return saver
