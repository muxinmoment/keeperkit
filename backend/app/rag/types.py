from dataclasses import dataclass, field


@dataclass(frozen=True)
class RawDocument:
    content: str
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class DocumentChunk:
    id: str
    content: str
    metadata: dict[str, str | list[str]] = field(default_factory=dict)


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: DocumentChunk
    score: float
