"""문장을 벡터(숫자 목록)로 바꾸는 임베딩 담당
저장할 때와 검색할 때 반드시 같은 모델을 써야 검색이 된다."""
from functools import lru_cache
from sentence_transformers import SentenceTransformer
from app.core.config import EMBED_MODEL


@lru_cache(maxsize=1)  # 모델은 처음 한 번만 불러옴 (불러오는 데 몇 초 걸림)
def get_model() -> SentenceTransformer:
    return SentenceTransformer(EMBED_MODEL)


def embed(texts: list[str]) -> list[list[float]]:
    """문장 목록 → 벡터 목록 (길이를 1로 맞춰서 코사인 유사도 계산이 쉬워짐)"""
    return get_model().encode(texts, normalize_embeddings=True).tolist()