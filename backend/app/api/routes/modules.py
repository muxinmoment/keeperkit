from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.modules import (
    ModuleAskRequest,
    ModuleAskResponse,
    ModuleCreateRequest,
    ModuleDetail,
    ModuleIngestResponse,
    ModuleSummary,
    ModuleUploadResponse,
)
from app.services.module_ingest_service import ModuleIngestService
from app.services.module_service import ModuleService
from app.services.module_qa_service import ModuleQAService


router = APIRouter(prefix="/modules", tags=["modules"])
service = ModuleService()
ingest_service = ModuleIngestService(service)
qa_service = ModuleQAService(service)


@router.get("", response_model=list[ModuleSummary])
def list_modules() -> list[ModuleSummary]:
    return service.list_modules()


@router.post("", response_model=ModuleDetail, status_code=201)
def create_module(request: ModuleCreateRequest) -> ModuleDetail:
    return service.create_module(request)


@router.get("/{module_id}", response_model=ModuleDetail)
def get_module(module_id: str) -> ModuleDetail:
    try:
        return service.get_module(module_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{module_id}/upload", response_model=ModuleUploadResponse)
async def upload_module_document(module_id: str, file: UploadFile = File(...)) -> ModuleUploadResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file must have a filename.")
    try:
        saved_path = service.save_document(module_id, file.filename, await file.read())
        return ModuleUploadResponse(
            module_id=module_id,
            filename=saved_path.name,
            path=str(saved_path),
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{module_id}/ingest", response_model=ModuleIngestResponse)
def ingest_module(module_id: str) -> ModuleIngestResponse:
    try:
        return ModuleIngestResponse(**ingest_service.ingest(module_id))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{module_id}/ask", response_model=ModuleAskResponse)
def ask_module(module_id: str, request: ModuleAskRequest) -> ModuleAskResponse:
    try:
        return qa_service.ask(module_id, request)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
