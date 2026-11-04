"""요청 처리 담당: 요청 받기 → service 호출 → 공통 응답 구조로 반환"""
import logging
from dataclasses import asdict

import requests
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.common.type.http_code import HttpStatusCode
from app.domain.llm.dto.request.chat_request import ChatRequest
from app.core.common.response.api_response import ApiResponse
from app.domain.llm.dto.response.chat_response import ChatResponse
from app.domain.llm.service import llm_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["llm"])



@router.post("/chat", response_model=ApiResponse[ChatResponse])
def chat(request: ChatRequest) -> ApiResponse:
    try:
        return ApiResponse.ok(llm_service.chat(request))
    except requests.RequestException:
        # Ollama(또는 n8n)가 꺼져 있거나 연결 실패
        logger.exception("LLM service unavailable")
        return ApiResponse.fail(HttpStatusCode.service_unavailable)
    except Exception:
        # 그 밖의 모든 오류
        logger.exception("Chat failed")
        return ApiResponse.fail(HttpStatusCode.internal_server_error)

