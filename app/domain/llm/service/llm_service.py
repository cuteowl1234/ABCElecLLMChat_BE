"""/chat 질문 처리 순서(RAG): 대화 조회 -> 주제 확인 -> Chroma 검색(제품 필터 적용) -> 근거 확인 -> prompt -> LLM 답변 -> 기록 저장"""
from datetime import datetime, timedelta, timezone
import logging                                                              # logging 추가                            # top K 추가
from app.core.config import MIN_SCORE, TOP_K, TOPIC_MIN_SCORE               # top K, MIN_SCORE, TOPIC_MIN_SCORE 추가
from app.core.infra.embedding import embed                                  # 임베드 호출
from app.domain.llm.prompt.chatbot.system_prompt import build_prompt        # system_prompt 추가
from app.domain.llm.repository import llm_repository                        # llm_repository 호출
from app.domain.llm.repository import chat_history_repository               # 대화 기록 저장소
from app.core.infra import n8n                                              # n8n 호출
import re
from app.domain.llm.model.retrieved_document import RetrievedDocument
from app.domain.llm.dto.request.chat_request import ChatRequest
from app.domain.llm.dto.response.chat_response import ChatResponse


logger = logging.getLogger(__name__)                    # logger 추가

KST = timezone(timedelta(hours=9))      # 응답했을 때 KST 기준으로 고정

# 근거 문서가 없을 때는 LLM을 부르지 않고 이 문구로 답한다 (지어낸 답변 방지)
# 질문 자체가 제품·서비스와 관련 없어 보일 때 (인사말, 의미 없는 말 등)
UNCLEAR_ANSWER = "질문을 정확히 이해하지 못했어요. 궁금하신 제품과 내용을 함께 말씀해 주세요."
NO_RESULT_ANSWER = "제공된 문서에서 관련 내용을 확인할 수 없습니다. 자세한 내용은 고객센터로 문의해 주세요."
# 이전 대화의 제품을 이어 붙여 검색했을 때, 고객이 다른 제품을 뜻했을 수 있으니 안내
INHERITED_PRODUCT_NOTICE = "\n\n※ {product} 기준으로 안내드렸어요. 다른 제품이라면 제품명을 함께 말씀해 주세요."

# 제품 모델명 표기: ABC-200, abc200, ABC 200 모두 인식
PRODUCT_ID_PATTERN = re.compile(r"ABC[-\s]?(\d{3})", re.IGNORECASE)
# 고객이 모델명 대신 제품 이름으로 말하는 경우
PRODUCT_NAMES = {
    "광파오븐": "ABC-100", "오븐": "ABC-100",
    "식기세척기": "ABC-200", "세척기": "ABC-200",
    "정수기": "ABC-300",
}

def now_kst() -> str:
    """현재 한국 시간을 'YYYY-MM-DD HH:mm:ss' 문자열로 반환"""
    return datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")

# 출처 표시 소스 추가
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

def find_product(text: str) -> str | None:
    """문장에서 제품을 찾아 모델명(ABC-200 형태)으로 돌려준다. 없으면 None"""
    found = PRODUCT_ID_PATTERN.search(text)
    if found:
        return f"ABC-{found.group(1)}"
    for name, product_id in PRODUCT_NAMES.items():
        if name in text:
            return product_id
    return None

def normalize_product(text: str) -> str:
    """검색이 잘 되도록 모델명 표기를 문서와 같은 형태로 통일한다 (abc300, ABC 300 → ABC-300)"""
    return PRODUCT_ID_PATTERN.sub(lambda m: f"ABC-{m.group(1)}", text)

# ABC-300 보증기간 물어보고 ABC-200은? 이라고 했을 때 ABC-200의 보증기간에 대해 답변하도록 하는 기능
# def remove_product, def_chat의 if not relevant 함수 4줄 추가
def remove_product(text: str) -> str:
    """문장에서 제품 모델명과 제품 이름을 지운다"""
    text = PRODUCT_ID_PATTERN.sub("", text)
    for name in PRODUCT_NAMES:
        text = text.replace(name, "")
    return text.strip()

def make_search_text(question: str, history: list[tuple[str, str]]) -> tuple[str, str | None]:
    """이번 질문에 제품이 없으면, 이전 대화에서 마지막으로 나온 제품 모델명만 붙여서 검색한다.
    반환: (검색어, 이어 붙인 제품명 또는 None)
    ("그럼 보증기간은?" → "ABC-300 그럼 보증기간은?") 직전 질문 전체를 붙이면 다른 주제가 검색을 방해한다."""
    question = normalize_product(question)  # 검색어용으로만 표기 통일 (LLM·기록에는 원문 사용)
    if find_product(question):
        return question, None
    for past_question, _ in reversed(history):
        product_id = find_product(past_question)
        if product_id:
            return f"{product_id} {question}", product_id
    return question, None

def search_documents(search_text: str, product_id: str | None) -> list[RetrievedDocument]:
    """제품이 정해졌으면 그 제품 문서 안에서만 검색하고, 결과가 없으면 전체에서 다시 검색"""
    query_vector = embed([search_text])[0]
    documents = llm_repository.search(query_vector, TOP_K, product_id)
    if not documents and product_id:
        documents = llm_repository.search(query_vector, TOP_K)
    return documents


def chat(request: ChatRequest) -> ChatResponse:         # query, document, relevant 추가
    history = chat_history_repository.get(request.session_id)
    # 이어지는 질문도 찾을 수 있게 직전 질문을 붙여서 검색
    search_text, inherited_product = make_search_text(request.question, history)
    # 제품을 이어받기 전에, 원래 질문만으로도 문서와 관련 있는지 확인 (의미 없는 말·인사말 거르기)
    if inherited_product:
        raw_documents = search_documents(normalize_product(request.question), None)
        raw_best = max((d.score for d in raw_documents), default=0)
        logger.info("Topic check: best score=%s", raw_best)
        if raw_best < TOPIC_MIN_SCORE:
            chat_history_repository.add(request.session_id, request.question, UNCLEAR_ANSWER)
            return ChatResponse(user_id="system", session_id=request.session_id,
                                date=now_kst(), answer=UNCLEAR_ANSWER)
    # 이번 질문의 제품 → 없으면 이전 대화에서 이어받은 제품 → 없으면 필터 없이 전체 검색
    product_id = find_product(request.question) or inherited_product
    documents = search_documents(search_text, product_id)
    relevant = [doc
                for doc in documents
                if doc.score >= MIN_SCORE]
    # 제품만 말하고 주제가 없어("abc200은?") 검색이 실패하면, 직전 질문의 주제를 붙여 한 번 더 검색
    if not relevant and history and find_product(request.question):
        retry_text = f"{normalize_product(request.question)} {remove_product(history[-1][0])}"
        documents = search_documents(retry_text, product_id)
        relevant = [doc for doc in documents if doc.score >= MIN_SCORE]

    if relevant:
        # 점수까지 보려고 로그에도 남긴다 (질문 원문은 개인정보일 수 있어 남기지 않음)
        logger.info("RAG sources (product=%s): %s", product_id, [(doc.source, doc.page, doc.score) for doc in relevant])
        # 출처 관련 추가 코드 : 출처는 LLM에게 맡기지 않고, 실제 검색된 문서 정보로 코드에서 붙인다
        llm_answer = n8n.generate(build_prompt(request.question, relevant, history))
        answer = llm_answer + format_sources(relevant)
        if inherited_product:
            answer = llm_answer + INHERITED_PRODUCT_NOTICE.format(product=inherited_product) + format_sources(relevant)
    else:
        logger.info("RAG no result: best score=%s", max((d.score for d in documents), default=None))
        llm_answer = answer = NO_RESULT_ANSWER      # llm_answer로 변경

    # 기록에는 [출처]를 뺀 답변만 저장 (다음 프롬프트가 지저분해지지 않게)
    chat_history_repository.add(request.session_id, request.question, llm_answer)

    return ChatResponse(
        user_id="system",
        session_id=request.session_id,
        date=now_kst(),
        answer=answer,
    )


