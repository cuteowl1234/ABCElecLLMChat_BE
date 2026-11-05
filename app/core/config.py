"""설정값 모음: 주소, 모델 이름 등은 여기서만 관리진행"""
import os


LOCALHOST = "localhost"
REMOTEHOST = "192.168.10.1"
CURRENT_HOST = REMOTEHOST

# Ollama (LLM)
OLLAMA_URL = os.getenv("OLLAMA_URL", f"http://{CURRENT_HOST}:11434").rstrip("/")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:3b")

# n8n (FastAPI → n8n Webhook → Ollama워크플로를 동작하는 주소)
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", f"http://{CURRENT_HOST}:5678/webhook/n8n/chat")

# Chroma / 임베딩 (저장 담당자와 값 맞추기)
CHROMA_HOST = os.getenv("CHROMA_HOST", CURRENT_HOST)
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))  # FastAPI(8080)와 겹치지 않게
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "abc_support_docs")
EMBED_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-m3")
TOP_K = int(os.getenv("TOP_K", "3"))                 # 검색해서 가져올 문서 개수 3
MIN_SCORE = float(os.getenv("MIN_SCORE", "0.55"))    # 이 점수보다 낮으면 "근거 없음" (RAG 단계에서 사용)