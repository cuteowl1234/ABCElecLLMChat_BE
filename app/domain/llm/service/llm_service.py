"""/chat 질문 처리 순서(RAG): 대화 조회 -> 주제 확인 -> Chroma 검색(제품 필터 적용) -> 근거 확인 -> prompt -> LLM 답변 -> 기록 저장"""
import logging
import re
from app.core.config import MIN_SCORE, TOP_K, TOPIC_MIN_SCORE
from app.core.infra import n8n
from app.core.infra.embedding import embed
from app.core.utils.datetime_util import now_kst
from app.domain.llm.dto.request.chat_request import ChatRequest
from app.domain.llm.dto.response.chat_response import ChatResponse
from app.domain.llm.model.retrieved_document import RetrievedDocument
from app.domain.llm.prompt.chatbot.system_prompt import build_prompt
from app.domain.llm.repository import chat_history_repository
from app.domain.llm.repository import llm_repository


logger = logging.getLogger(__name__)

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
    "정수기": "ABC-300"
}
# abc200, ABC-200, 식기세척기 뭘 하든 다 답변 제대로 하기 위한 코드
# 검색할 때 모델명 대신 쓸 대표 제품 이름 (모델명 검색은 FAQ 행으로, 이름 검색은 매뉴얼로 쏠리는 차이 보완)
PRODUCT_LABELS = {"ABC-100": "광파오븐", "ABC-200": "식기세척기", "ABC-300": "정수기"}
# 할루시네이션 방지 기능
# "건조 기능", "온수기능"처럼 기능을 묻는 질문에서 기능 이름(건조, 온수)을 뽑는 패턴
FEATURE_PATTERN = re.compile(r"([가-힣A-Za-z0-9]{2,}?)\s*기능")

# 출처 표시 소스 추가
def __format_sources(documents: list[RetrievedDocument]) -> str:
    """검색된 문서의 파일명·페이지로 출처 문구를 만든다. 같은 출처는 한 번만, 'unknown'은 제외"""
    items = []
    for doc in documents:
        if doc.source == "unknown":
            continue
        item = f"{doc.source} {doc.page}페이지" if doc.page is not None else doc.source
        if item not in items:
            items.append(item)
    return f"\n\n[출처] {', '.join(items)}" if items else ""

def __find_product(text: str) -> str | None:
    """문장에서 제품을 찾아 모델명(ABC-200 형태)으로 돌려준다. 없으면 None"""
    found = PRODUCT_ID_PATTERN.search(text)
    if found:
        return f"ABC-{found.group(1)}"
    for name, product_id in PRODUCT_NAMES.items():
        if name in text:
            return product_id
    return None

def __normalize_product(text: str) -> str:
    """검색이 잘 되도록 모델명 표기를 문서와 같은 형태로 통일한다 (abc300, ABC 300 → ABC-300)"""
    return PRODUCT_ID_PATTERN.sub(lambda m: f"ABC-{m.group(1)}", text)

# ABC-300 보증기간 물어보고 ABC-200은? 이라고 했을 때 ABC-200의 보증기간에 대해 답변하도록 하는 기능
# def remove_product, def_chat의 if not relevant 함수 4줄 추가
def __remove_product(text: str) -> str:
    """문장에서 제품 모델명과 제품 이름을 지운다"""
    text = PRODUCT_ID_PATTERN.sub("", text)
    for name in PRODUCT_NAMES:
        text = text.replace(name, "")
    return text.strip()

def __to_product_name(text: str) -> str:
    """검색어의 모델명을 제품 이름으로 바꾼다 (ABC-200 사용법은? → 식기세척기 사용법은?)"""
    return PRODUCT_ID_PATTERN.sub(lambda m: PRODUCT_LABELS.get(f"ABC-{m.group(1)}", m.group(0)), text)

def __make_search_text(question: str, history: list[tuple[str, str]]) -> tuple[str, str | None]:
    """이번 질문에 제품이 없으면, 이전 대화에서 마지막으로 나온 제품 모델명만 붙여서 검색한다.
    반환: (검색어, 이어 붙인 제품명 또는 None)
    ("그럼 보증기간은?" → "ABC-300 그럼 보증기간은?") 직전 질문 전체를 붙이면 다른 주제가 검색을 방해한다."""
    question = __normalize_product(question)  # 검색어용으로만 표기 통일 (LLM·기록에는 원문 사용)
    if __find_product(question):
        return question, None
    for past_question, _ in reversed(history):
        product_id = __find_product(past_question)
        if product_id:
            return f"{product_id} {question}", product_id
    return question, None

def __search_documents(search_text: str, product_id: str | None) -> list[RetrievedDocument]:
    """제품이 정해졌으면 그 제품 문서 안에서만 검색하고, 결과가 없으면 전체에서 다시 검색"""
    """
    query_vector = embed([search_text])[0]
    documents = llm_repository.search(query_vector, TOP_K, product_id)
    if not documents and product_id:
        documents = llm_repository.search(query_vector, TOP_K)
    return documents
    """
    """제품이 정해졌으면 그 제품 문서 안에서만 검색하고, 결과가 없으면 전체에서 다시 검색.
        필터 검색 때는 원래 검색어(ABC-200 ...)와 제품 이름 검색어(식기세척기 ...)로 둘 다 검색해서
        점수가 높은 조각을 고른다 (모델명 검색은 FAQ 행으로, 이름 검색은 매뉴얼로 쏠리는 차이를 보완)"""
    if product_id:
        candidates = {}
        for text in {search_text, __to_product_name(search_text)}:
            for doc in llm_repository.search(embed([text])[0], TOP_K, product_id):
                if doc.text not in candidates or doc.score > candidates[doc.text].score:
                    candidates[doc.text] = doc  # 같은 조각이 두 번 나오면 높은 점수만 남김
        if candidates:
            return sorted(candidates.values(), key=lambda d: d.score, reverse=True)[:TOP_K]
    # 제품이 없거나 필터 결과가 없으면 원래 검색어로 전체 검색
    return llm_repository.search(embed([search_text])[0], TOP_K)

# 건조기능 로그
def __is_unsupported_feature(question: str, documents: list[RetrievedDocument]) -> bool:
    """'건조 기능 있어?'처럼 기능을 묻는데, 그 기능 이름이 검색된 문서 본문 어디에도 없으면 True.
    LLM은 비슷한 내용으로 없는 기능을 지어내는 경향이 있어서, 코드에서 먼저 걸러낸다"""
    found = FEATURE_PATTERN.search(question)
    if not found:
        return False                       # 기능 질문이 아니면 검사하지 않음
    feature = found.group(1)
    if __find_product(feature):
        return False                       # "식기세척기 기능"처럼 제품명이 잡히면 검사하지 않음
    return not any(feature in doc.text for doc in documents)

def chat(request: ChatRequest) -> ChatResponse:
    history = chat_history_repository.get(request.session_id)
    # 이어지는 질문도 찾을 수 있게 직전 질문을 붙여서 검색
    search_text, inherited_product = __make_search_text(request.question, history)
    # 제품을 이어받기 전에, 원래 질문만으로도 문서와 관련 있는지 확인 (의미 없는 말·인사말 거르기)
    if inherited_product:
        raw_documents = __search_documents(__normalize_product(request.question), None)
        raw_best = max((d.score for d in raw_documents), default=0)
        logger.info("Topic check: best score=%s", raw_best)
        if raw_best < TOPIC_MIN_SCORE:
            chat_history_repository.add(request.session_id, request.question, UNCLEAR_ANSWER)
            return ChatResponse(user_id="system", session_id=request.session_id,
                                date=now_kst(), answer=UNCLEAR_ANSWER)
    # 이번 질문의 제품 → 없으면 이전 대화에서 이어받은 제품 → 없으면 필터 없이 전체 검색
    product_id = __find_product(request.question) or inherited_product
    documents = __search_documents(search_text, product_id)
    relevant = [doc
                for doc in documents
                if doc.score >= MIN_SCORE]
    # 제품만 말하고 주제가 없어("abc200은?") 검색이 실패하면, 직전 질문의 주제를 붙여 한 번 더 검색
    if not relevant and history and __find_product(request.question):
        retry_text = f"{__normalize_product(request.question)} {__remove_product(history[-1][0])}"
        documents = __search_documents(retry_text, product_id)
        relevant = [doc for doc in documents if doc.score >= MIN_SCORE]

    # 문서에 없는 기능을 묻는 질문은 LLM에 넘기지 않음 (할루시네이션 방지)
    if relevant and __is_unsupported_feature(request.question, relevant):
        logger.info("Feature not in documents: %s", FEATURE_PATTERN.search(request.question).group(1))
        relevant = []

    if relevant:
        # 점수까지 보려고 로그에도 남긴다 (질문 원문은 개인정보일 수 있어 남기지 않음)
        logger.info("RAG sources (product=%s): %s", product_id, [(doc.source, doc.page, doc.score) for doc in relevant])
        # 출처 관련 추가 코드 : 출처는 LLM에게 맡기지 않고, 실제 검색된 문서 정보로 코드에서 붙인다
        llm_answer = n8n.generate(build_prompt(request.question, relevant, history))
        answer = llm_answer + __format_sources(relevant)
        if inherited_product:
            answer = llm_answer + INHERITED_PRODUCT_NOTICE.format(product=inherited_product) + __format_sources(relevant)
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
