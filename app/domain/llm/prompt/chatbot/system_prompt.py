"""RAG 답변용 프롬프트. 검색된 문서만 근거로 답하게 해서 LLM이 내용을 지어내는 것을 막음"""

from app.domain.llm.model.retrieved_document import RetrievedDocument

SYSTEM_PROMPT = (
    "당신은 ABC Electronics의 고객지원 상담원입니다. 아래 규칙을 지켜 한국어로 답하세요.\n"
    "1. [참고 문서]에 있는 내용만 근거로 답하세요.\n"
    "2. 문서에 없는 연락처, 숫자, 절차, 기능, 사양은 절대 지어내지 마세요.\n"
    "3. [이전 대화]는 질문이 무엇을 가리키는지(어떤 제품 이야기인지 등) 파악하는 데만 쓰세요.\n"
    "4. 고객 질문에 대한 답만 친절하고 간결하게 말하고, '참고 문서', '자료', '제공된 정보' 같은 말이나 출처는 쓰지 마세요.\n"
    "5. [참고 문서]에 질문과 관련된 내용이 전혀 없을 때만 '제공된 문서에서 확인할 수 없습니다.'라고만 답하세요. "
    "관련 내용이 일부라도 있으면 그 내용으로 답하세요.\n"
    "6. 고객이 묻는 기능이나 사양이 [참고 문서]의 내용으로 확인되지 않으면, 비슷한 내용을 근거로 "
    "'설정에 따라 다르다', '가능할 수 있다'처럼 추측하지 말고 5번처럼 답하세요. "
    "표현이 달라도 같은 뜻이면 문서 내용으로 답하세요.\n"
    "7. '사용법', '관리 방법'처럼 범위가 넓은 질문은 [참고 문서]의 관련 절차를 순서대로 정리해서 답하세요.\n"
    "8. 한자, 일본어, 중국어를 쓰지 말고 한글로만 답하세요. 문장 끝에는 '.'를 쓰세요."
)

# 작은 모델은 맨 앞의 규칙보다 가까운 내용을 더 따르므로, 답을 쓰기 직전 위치에 언어 규칙을 한 번 더 둔다
LANGUAGE_REMINDER = "※ 위 질문에 한국어(한글)로만 답하세요. 한자·일본어·중국어를 섞지 마세요."
# 첫 답변에 다른 언어가 섞였을 때 다시 요청하는 문구 (temperature 0이라 프롬프트가 같으면 같은 답이 나오므로 문구를 바꿔 보냄)
STRICT_LANGUAGE_REMINDER = (
    "※ 이전 답변에 한자나 일본어가 섞였습니다. 以下, の, 。 같은 문자를 쓰지 말고 "
    "'다음', '.'처럼 한글과 일반 문장부호로만 다시 답하세요."
)


def build_prompt(
    question: str,
    documents: list[RetrievedDocument],
    history: list[tuple[str, str]] | None = None,
    strict_language: bool = False,
) -> str:
    context = "\n\n".join(
        f"[출처: {__format_source(doc)}]\n{doc.text}" for doc in documents
    )
    parts = [SYSTEM_PROMPT]
    if history:
        history_text = "\n".join(f"고객: {q}\n상담원: {a}" for q, a in history)
        parts.append(f"[이전 대화]\n{history_text}")
    parts.append(f"[참고 문서]\n{context}")
    parts.append(f"[고객 질문]\n{question}")
    parts.append(STRICT_LANGUAGE_REMINDER if strict_language else LANGUAGE_REMINDER)
    return "\n\n".join(parts)


def __format_source(doc: RetrievedDocument) -> str:
    """페이지 정보가 없으면 'None페이지'가 들어가지 않도록 파일명만 표시"""
    return f"{doc.source}, {doc.page}페이지" if doc.page is not None else doc.source
