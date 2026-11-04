"""n8n Webhook을 호출해 LLM 답변을 받아오는 담당"""
import requests

from app.core.config import N8N_WEBHOOK_URL


def generate(question: str, context: str) -> str:
    response = requests.post(
        N8N_WEBHOOK_URL,
        json={"question": question, "context": context},
        timeout=120,
    )
    response.raise_for_status()
    answer = response.json().get("answer", "").strip()
    if not answer:
        raise RuntimeError("Empty n8n response")
    return answer