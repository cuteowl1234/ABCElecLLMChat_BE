"""요청 처리 담당: 요청 받기 → service 호출 → 공통 응답 구조로 반환"""
import logging
import requests
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.core.common.exception.vector_store_unavailable_error import VectorStoreUnavailableError
from app.core.common.response.api_response import ApiResponse
from app.core.common.type.http_code import HttpStatusCode
from app.domain.llm.dto.request.chat_request import ChatRequest
from app.domain.llm.dto.response.chat_response import ChatResponse
from app.domain.llm.service import llm_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["llm"])

def error_response(http_code: HttpStatusCode) -> JSONResponse:
    # ApiResponse를 그대로 return하면 HTTP 상태 코드가 200으로 나가므로, 상태 코드를 직접 지정해서 보낸다
    return JSONResponse(status_code=http_code.value[0], content=ApiResponse.fail(http_code).to_dict())


@router.post("/chat", response_model=ApiResponse[ChatResponse])
def chat(request: ChatRequest) -> ApiResponse | JSONResponse:
    try:
        return ApiResponse.ok(llm_service.chat(request))
    except (requests.RequestException, VectorStoreUnavailableError):
    # Ollama(또는 n8n) 또는 Chroma가 꺼져 있거나 연결 실패
        logger.exception("LLM service unavailable")
        return error_response(HttpStatusCode.service_unavailable)
    except Exception:
        # 그 밖의 모든 오류
        logger.exception("Chat failed")
        return error_response(HttpStatusCode.internal_server_error)

