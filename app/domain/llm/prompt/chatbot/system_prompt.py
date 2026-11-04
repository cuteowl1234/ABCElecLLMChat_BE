"""RAG 답변용 프롬프트. 검색된 문서만 근거로 답하게 해서 LLM이 내용을 지어내는 것을 막는다."""
# LLM이 받는 쪽은 여기로 작성

from app.domain.llm.model.retrieved_document import RetrievedDocument

SYSTEM_PROMPT = {
  "prompt": "당신은 ABC Electronics 고객지원 AI입니다. 제공된 참고 문서에 근거하여 한국어로 답변하고, 확인되지 않은 내용은 추측하지 마세요.\n\n[참고 문서 1: WAR-200]\nABC-200 보증 및 A/S 정책에서 추출한 청크 예시\n\n[참고 문서 2: WAR-200]\nABC-200 보증 및 수리 기준에 관한 청크 예시\n\n[참고 문서 3: MAN-200]\nABC-200 문제 해결 안내에 관한 청크 예시\n\n[사용자 질문]\nABC-200 식기세척기의 A/S 신청 방법은?"
}


def build_prompt(question: str, documents: list[RetrievedDocument]) -> str:
    context = "\n\n".join(
        f"[출처: {doc.source}, {doc.page}페이지]\n{doc.text}" for doc in documents
    )
    return f"{SYSTEM_PROMPT}\n\n[참고 문서]\n{context}\n\n[고객 질문]\n{question}"