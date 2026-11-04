"""Chroma DB 서버에 접속해서 컬렉션(문서를 담는 통)을 가져오는 담당"""
from functools import lru_cache

import chromadb

from app.core.config import CHROMA_HOST, CHROMA_PORT, COLLECTION_NAME


@lru_cache(maxsize=1)  # 접속은 한 번만 하고 재사용
def get_collection():
    client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},  # 코사인 거리로 비교 (1 - 거리 = 유사도)
    )