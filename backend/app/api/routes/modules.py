from fastapi import APIRouter, HTTPException

from app.schemas.modules import ModuleCreateRequest, ModuleDetail, ModuleSummary
from app.services.module_service import ModuleService


router = APIRouter(prefix="/modules", tags=["modules"])
service = ModuleService()


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
