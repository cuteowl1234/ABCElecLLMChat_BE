"""Chroma에서 질문 벡터와 비슷한 문서를 검색해 RetrievedDocument 목록으로 돌려준다."""
from app.core.common.exception.vector_store_unavailable_error import VectorStoreUnavailableError
from app.core.infra.chroma_client import get_collection
from app.domain.llm.model.retrieved_document import RetrievedDocument


#def search(query_vector: list[float], top_k: int) -> list[RetrievedDocument]:
def search(query_vector: list[float], top_k: int, product_id: str | None = None) -> list[RetrievedDocument]:
    """product_id를 주면 그 제품 문서 안에서만 검색한다 (메타데이터 필터)"""
    options = {"where": {"product_id": product_id}} if product_id else {}   # 제품 번호가 있으면 받고 없으면 빈 딕셔너리 생성
    try:
        #result = get_collection().query(query_embeddings=[query_vector], n_results=top_k)
        result = get_collection().query(query_embeddings=[query_vector], n_results=top_k, **options)
    except Exception as exc:
        # 서버 꺼짐, 연결 끊김 등 원인이 여러 가지라 한 예외로 바꾸고, 원인(exc)은 로그용으로 보존
        raise VectorStoreUnavailableError("Chroma 검색에 실패했습니다.") from exc

    documents = []
    for text, meta, distance in zip(
        result["documents"][0], result["metadatas"][0], result["distances"][0]
    ):
        meta = meta or {}
        documents.append(RetrievedDocument(
            text=text,
            source=meta.get("source_file", "unknown"),
            page=meta.get("page"),                          # 현재 데이터에는 None이지만, 추가 시 자동 표시
            chunk_id=meta.get("chunk_index"),
            score=round(1 - distance, 4),  # 컬렉션이 cosine 거리라서 1 - 거리 = 유사도
        ))
    return documents