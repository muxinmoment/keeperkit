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


class ModulePrepFullResponse(BaseModel):
    module_id: str
    answer: str
    sources: list[ModuleSource]
    document_count: int
    character_count: int


class ModuleIngestResponse(BaseModel):
    module_id: str
    document_count: int
    chunk_count: int
    index_dir: str


class ModuleUploadResponse(BaseModel):
    module_id: str
    filename: str
    path: str


class ModuleStructureItem(BaseModel):
    label: str
    source: str
    title_path: list[str] = Field(default_factory=list)
    content_type: str
    preview: str


class ModuleStructureGroup(BaseModel):
    content_type: str
    label: str
    items: list[ModuleStructureItem]


class ModuleStructureResponse(BaseModel):
    module_id: str
    groups: list[ModuleStructureGroup]


class ModuleTimelineEvent(BaseModel):
    order: int
    title: str
    source: str
    content_type: str
    location: str | None = None
    npcs: list[str] = Field(default_factory=list)
    clues: list[str] = Field(default_factory=list)
    trigger: str | None = None
    preview: str


class ModuleTimelineResponse(BaseModel):
    module_id: str
    events: list[ModuleTimelineEvent]


class ModulePrepSummaryItem(BaseModel):
    title: str
    content_type: str
    source: str
    preview: str


class ModulePrepSummaryResponse(BaseModel):
    module_id: str
    highlights: list[ModulePrepSummaryItem]
    clues: list[ModulePrepSummaryItem]
    npcs: list[ModulePrepSummaryItem]
    warnings: list[str] = Field(default_factory=list)


class ModulePrepMapNode(BaseModel):
    id: str
    label: str
    kind: str
    source: str | None = None
    summary: str | None = None


class ModulePrepMapEdge(BaseModel):
    source_id: str
    target_id: str
    label: str


class ModulePrepMapResponse(BaseModel):
    module_id: str
    nodes: list[ModulePrepMapNode]
    edges: list[ModulePrepMapEdge]
    warnings: list[str] = Field(default_factory=list)
