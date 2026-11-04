"""/chat 질문 처리 순서(RAG): 질문 임베딩 → Chroma 검색 → 근거 확인 → 프롬프트 → LLM 답변"""
from datetime import datetime, timedelta, timezone
import logging                                          # logging 추가
from app.core.config import MIN_SCORE, TOP_K            # top K 추가
from app.core.infra.embedding import embed              # 임베드 호출
from app.domain.llm.prompt.chatbot.system_prompt import build_prompt        # system_prompt 추가
from app.domain.llm.repository import llm_repository                        # llm_repository 호출
from app.core.infra import n8n                                              # n8n 호출
from app.domain.llm.model.retrieved_document import RetrievedDocument
from app.domain.llm.dto.request.chat_request import ChatRequest
from app.domain.llm.dto.response.chat_response import ChatResponse

logger = logging.getLogger(__name__)                    # logger 추가

KST = timezone(timedelta(hours=9))      # 응답했을 때 KST 기준으로 고정

# 근거 문서가 없을 때는 LLM을 부르지 않고 이 문구로 답한다 (지어낸 답변 방지)
NO_RESULT_ANSWER = "제공된 문서에서 관련 내용을 확인할 수 없습니다. 자세한 내용은 고객센터로 문의해 주세요."

def now_kst() -> str:
    """현재 한국 시간을 'YYYY-MM-DD HH:mm:ss' 문자열로 반환"""
    return datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
# 출처 표시 소스 추가-------------------------------------------------------
def format_sources(documents: list[RetrievedDocument]) -> str:
    """검색된 문서의 파일명·페이지로 출처 문구를 만든다. 같은 출처는 한 번만, 'unknown'은 제외"""
    items = []
    for doc in documents:
        if doc.source == "unknown":
            continue
        item = f"{doc.source} {doc.page}페이지" if doc.page is not None else doc.source
        if item not in items:
            items.append(item)
    return f"\n\n[출처] {', '.join(items)}" if items else ""
#--------------------------------------------------------------------------
def chat(request: ChatRequest) -> ChatResponse:         # query, document, relevant 추가
    query_vector = embed([request.question])[0]
    documents = llm_repository.search(query_vector, TOP_K)
    relevant = [doc
                for doc in documents
                if doc.score >= MIN_SCORE]
    if relevant:
        # 점수까지 보려고 로그에도 남긴다 (질문 원문은 개인정보일 수 있어 남기지 않음)
        logger.info("RAG sources: %s", [(doc.source, doc.page, doc.score) for doc in relevant])
        answer = n8n.generate(build_prompt(request.question, relevant))
        # 출처 관련 추가 코드 : 출처는 LLM에게 맡기지 않고, 실제 검색된 문서 정보로 코드에서 붙인다
        answer += format_sources(relevant)
    else:
        logger.info("RAG no result: best score=%s", max((d.score for d in documents), default=None))
        answer = NO_RESULT_ANSWER

    return ChatResponse(
        user_id="system",
        session_id=request.session_id,
        date=now_kst(),
        answer=answer,
    )


