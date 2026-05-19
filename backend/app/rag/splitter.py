import hashlib
import re

from app.rag.types import DocumentChunk, RawDocument


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def split_documents(
    documents: list[RawDocument],
    max_chars: int = 1200,
    overlap_chars: int = 120,
) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []
    for document in documents:
        chunks.extend(split_markdown_document(document, max_chars, overlap_chars))
    return chunks


def split_markdown_document(
    document: RawDocument,
    max_chars: int = 1200,
    overlap_chars: int = 120,
) -> list[DocumentChunk]:
    title_stack: list[str] = []
    buffer: list[str] = []
    chunks: list[DocumentChunk] = []

    def flush() -> None:
        text = "\n".join(line for line in buffer).strip()
        has_body = any(line.strip() and not HEADING_RE.match(line) for line in buffer)
        if not has_body:
            buffer.clear()
            return
        if not text:
            return
        for part in split_long_text(text, max_chars=max_chars, overlap_chars=overlap_chars):
            source = str(document.metadata.get("source", "unknown"))
            chunk_id = stable_chunk_id(source, title_stack, part)
            chunks.append(
                DocumentChunk(
                    id=chunk_id,
                    content=part,
                    metadata={
                        **document.metadata,
                        "title_path": title_stack.copy(),
                    },
                )
            )
        buffer.clear()

    for line in document.content.splitlines():
        heading = HEADING_RE.match(line)
        if heading:
            flush()
            level = len(heading.group(1))
            title = heading.group(2).strip()
            title_stack = title_stack[: level - 1]
            title_stack.append(title)
            buffer.append(line)
            continue
        buffer.append(line)

    flush()
    return chunks


def split_long_text(text: str, max_chars: int, overlap_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]

    parts: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        window = text[start:end]
        split_at = max(window.rfind("\n\n"), window.rfind("。"), window.rfind(". "))
        if split_at > max_chars * 0.45:
            end = start + split_at + 1
        parts.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(0, end - overlap_chars)
    return [part for part in parts if part]


def stable_chunk_id(source: str, title_path: list[str], content: str) -> str:
    payload = "\n".join([source, *title_path, content])
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()
