"""RAG 답변용 프롬프트. 검색된 문서만 근거로 답하게 해서 LLM이 내용을 지어내는 것을 막는다."""
# LLM이 받는 쪽은 여기로 작성

from app.domain.llm.model.retrieved_document import RetrievedDocument

'''
SYSTEM_PROMPT = {
  "prompt": "당신은 ABC Electronics 고객지원 AI입니다. 제공된 참고 문서에 근거하여 한국어로 답변하고, 확인되지 않은 내용은 추측하지 마세요.\n\n[참고 문서 1: WAR-200]\nABC-200 보증 및 A/S 정책에서 추출한 청크 예시\n\n[참고 문서 2: WAR-200]\nABC-200 보증 및 수리 기준에 관한 청크 예시\n\n[참고 문서 3: MAN-200]\nABC-200 문제 해결 안내에 관한 청크 예시\n\n[사용자 질문]\nABC-200 식기세척기의 A/S 신청 방법은?"
}


def build_prompt(question: str, documents: list[RetrievedDocument]) -> str:
    context = "\n\n".join(
        f"[출처: {doc.source}, {doc.page}페이지]\n{doc.text}" for doc in documents
    )
    return f"{SYSTEM_PROMPT}\n\n[참고 문서]\n{context}\n\n[고객 질문]\n{question}"
'''

SYSTEM_PROMPT = (
    "당신은 ABC Electronics의 고객지원 상담원입니다. 아래 규칙을 지켜 한국어로 답하세요.\n"
    "1. [참고 문서]에 있는 내용만 근거로 답하세요.\n"
    "2. 문서에 없는 연락처, 숫자, 절차는 절대 지어내지 마세요.\n"
    "3. [이전 대화]는 질문이 무엇을 가리키는지(어떤 제품 이야기인지 등) 파악하는 데만 쓰세요.\n"
    "4. 고객 질문에 대한 답만 친절하고 간결하게 말하고, '참고 문서', '자료', '제공된 정보' 같은 말이나 출처는 쓰지 마세요.\n"
    "5. [참고 문서]로 답할 수 없으면 '제공된 문서에서 확인할 수 없습니다.'라고만 답하세요."
)


def build_prompt(
    question: str,
    documents: list[RetrievedDocument],
    history: list[tuple[str, str]] | None = None,
) -> str:
    context = "\n\n".join(
        f"[출처: {doc.source}, {doc.page}페이지]\n{doc.text}" for doc in documents
    )
    parts = [SYSTEM_PROMPT]
    if history:
        history_text = "\n".join(f"고객: {q}\n상담원: {a}" for q, a in history)
        parts.append(f"[이전 대화]\n{history_text}")
    parts.append(f"[참고 문서]\n{context}")
    parts.append(f"[고객 질문]\n{question}")
    return "\n\n".join(parts)