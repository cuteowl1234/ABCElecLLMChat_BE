"""명세의 response 객체(ChatResponse): 서버가 돌려주는 AI 응답 데이터의 형식"""
from dataclasses import asdict, dataclass


@dataclass
class ChatResponse:
    user_id: str     # 응답 주체 ("system")
    session_id: str  # 요청과 같은 세션 ID
    date: str        # 응답 생성 일시 (KST)
    answer: str      # AI 답변

    @classmethod
    def from_json(cls, data: dict) -> "ChatResponse":
        """딕셔너리(JSON)로 새 ChatResponse를 만든다"""
        return cls(**data)

    def to_json(self) -> dict:
        """ChatResponse를 딕셔너리(JSON)로 바꾼다"""
        return asdict(self)
