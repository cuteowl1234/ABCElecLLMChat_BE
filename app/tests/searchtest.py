"""[테스트용] Chroma에서 질문과 비슷한 문서를 검색해 결과를 출력한다.

실행: temporary_BE 폴더에서  python -m scripts.search_test "ABC-100 보증기간이 얼마야?"
"""
import sys

from app.core.config import TOP_K
from app.core.infra.chroma_client import get_collection
from app.core.infra.embedding import embed


def main():
    question = sys.argv[1] if len(sys.argv) > 1 else "ABC-100 보증기간이 얼마야?"
    result = get_collection().query(query_embeddings=embed([question]), n_results=TOP_K)

    print(f"질문: {question}\n")
    for rank, (text, meta, distance) in enumerate(
            zip(result["documents"][0], result["metadatas"][0], result["distances"][0]), start=1
    ):
        score = round(1 - distance, 4)  # 거리 → 유사도 (1에 가까울수록 비슷)
        print(f"{rank}위 | 점수 {score} | {meta['source']} p.{meta['page']}")
        print(f"     {text}\n")


if __name__ == "__main__":
    main()