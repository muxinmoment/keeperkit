from pydantic import BaseModel, Field


class Source(BaseModel):
    source: str
    title_path: list[str] = Field(default_factory=list)
    score: float | None = None
    content_preview: str


class RuleAskRequest(BaseModel):
    question: str = Field(min_length=1)
    top_k: int | None = Field(default=None, ge=1, le=20)
    rerank_top_k: int | None = Field(default=None, ge=1, le=10)


class RuleAskResponse(BaseModel):
    answer: str
    sources: list[Source]
