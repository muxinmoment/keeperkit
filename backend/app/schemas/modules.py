from pydantic import BaseModel, Field


class ModuleMetadata(BaseModel):
    id: str = Field(min_length=1, pattern=r"^[a-z0-9_-]+$")
    title: str = Field(min_length=1)
    system: str = Field(default="coc7")
    language: str = Field(default="zh")
    keeper_notes: str | None = None
    spoiler_level: str = Field(default="keeper_only")


class ModuleCreateRequest(ModuleMetadata):
    pass


class ModuleSummary(ModuleMetadata):
    has_documents: bool
    document_count: int
    index_ready: bool


class ModuleDetail(ModuleSummary):
    module_dir: str
    documents_dir: str
    processed_dir: str
    index_dir: str


class ModuleAskRequest(BaseModel):
    question: str = Field(min_length=1)
    top_k: int | None = Field(default=None, ge=1, le=20)
    rerank_top_k: int | None = Field(default=None, ge=1, le=10)


class ModuleSource(BaseModel):
    knowledge_base: str = "module"
    module_id: str
    source: str
    title_path: list[str] = Field(default_factory=list)
    content_type: str = "document"
    spoiler_level: str = "keeper_only"
    score: float | None = None
    content_preview: str


class ModuleAskResponse(BaseModel):
    answer: str
    sources: list[ModuleSource]


class ModuleIngestResponse(BaseModel):
    module_id: str
    document_count: int
    chunk_count: int
    index_dir: str


class ModuleUploadResponse(BaseModel):
    module_id: str
    filename: str
    path: str
