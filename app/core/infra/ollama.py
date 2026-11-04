import requests
from app.core.config import OLLAMA_URL, LLM_MODEL

""""Ollama LLM을 호출하는 코드입니다. 프롬프트를 받아 답변 텍스트를 반환합니다. 
Ollama의 /api/generate에 모델명과 프롬프트를 보내고, 응답에서 답변만 꺼냅니다. 
같은 질문에 같은 답이 나오도록 temperature를 0으로 설정했고, 답변이 비어 있으면 에러를 발생시킵니다."""
"""n8n을 통해 ollama를 호출하는 방식으로 바꿀 시 해당 파일은 필요없음.
현재 코드는 ollama를 직접 호출하는 방식"""

def generate(prompt: str) -> str:
    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={"model": LLM_MODEL, "prompt": prompt, "stream": False,
              "options": {"temperature": 0}},
        timeout=120)
    response.raise_for_status()
    answer = response.json().get("response", "").strip()
    if not answer:
        raise RuntimeError("Empty LLM response")
    return answer