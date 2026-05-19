import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.schemas.rules import RuleAskRequest, RuleAskResponse
from app.services.rule_qa_service import RuleQAService


router = APIRouter(prefix="/rules", tags=["rules"])
service = RuleQAService()


@router.post("/ask", response_model=RuleAskResponse)
def ask_rules(request: RuleAskRequest) -> RuleAskResponse:
    return service.ask(request)


@router.post("/ask/stream")
def stream_rules(request: RuleAskRequest) -> StreamingResponse:
    def event_stream():
        response = service.ask(request)
        for token in response.answer:
            yield f"event: token\ndata: {json.dumps({'text': token}, ensure_ascii=False)}\n\n"
        yield f"event: sources\ndata: {response.model_dump_json()}\n\n"
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
