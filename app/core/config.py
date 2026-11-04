"""설정값 모음: 주소, 모델 이름 등은 여기서만 관리"""
import os

# Ollama (LLM)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
LLM_MODEL = os.getenv("LLM_MODEL", "gemma3:4b")

# Chroma / 임베딩 (저장 담당자와 값 맞추기)
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8001"))  # FastAPI(8000)와 겹치지 않게
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "documents")
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
TOP_K = int(os.getenv("TOP_K", "3"))                 # 검색해서 가져올 문서 개수
MIN_SCORE = float(os.getenv("MIN_SCORE", "0.35"))    # 이 점수보다 낮으면 "근거 없음" (RAG 단계에서 사용)