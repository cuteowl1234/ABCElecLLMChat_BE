"""질문을 어떤 순서로 처리할지 정하는 코드입니다. 질문을 받아 답변을 반환합니다.
현재는 질문을 LLM에 바로 전달하고, 이후 임베딩 → Chroma 검색 → 근거 확인 → 답변 생성 순서로 확장할 예정입니다."""
from datetime import datetime, timedelta, timezone

from app.core.infra import ollama
from app.domain.llm.dto.request.chat_request import ChatRequest
from app.domain.llm.dto.response.chat_response import ChatResponse

KST = timezone(timedelta(hours=9))      # 한국 시간대로 고정 KST = 한국


def now_kst() -> str:
    """현재 한국 시간을 'YYYY-MM-DD HH:mm:ss' 문자열로 반환"""
    return datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")


def chat(request: ChatRequest) -> ChatResponse:
    prompt = (
        "당신은 10년차 전자제품 고객지원 상담원입니다. 친절하고 간결하게 한국어로 답하세요.\n\n"
        f"고객 질문: {request.question}"
    )
    answer = ollama.generate(prompt)
    return ChatResponse(
        user_id="system",
        session_id=request.session_id,
        date=now_kst(),
        answer=answer,
    )


