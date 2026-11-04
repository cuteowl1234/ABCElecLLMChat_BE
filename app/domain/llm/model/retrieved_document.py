"""Chroma 검색 결과 한 건. repository가 Chroma의 원본 응답(dict)을 이 모양으로 바꿔서 service에 넘긴다."""
from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievedDocument:
    text: str             # 문서 내용 (chunk)
    source: str           # 출처 파일명
    page: int | None      # 페이지 번호
    chunk_id: int | None  # 조각 번호
    score: float          # 질문과의 유사도 (1에 가까울수록 비슷)
