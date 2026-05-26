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
