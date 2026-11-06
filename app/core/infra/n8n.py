"""n8n Webhook을 호출해 LLM 답변을 받아오는 담당. n8n 워크플로가 Ollama를 대신 호출한다."""
import requests

from app.core.config import N8N_WEBHOOK_URL


def generate(prompt: str) -> str:
    response = requests.post(N8N_WEBHOOK_URL, json={"prompt": prompt}, timeout=15)
    response.raise_for_status()
    answer = response.json().get("answer", "").strip()
    if not answer:
        raise RuntimeError("Empty n8n response")
    return answer