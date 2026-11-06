"""요청 형식: POST /chat 명세의 Request
user_id, session_id, date, question을 받음. date는 비우거나 생략하면 서버가 현재 KST기준으로 채움.
빈 질문, 형식이 틀린 날짜가 들어오면 FastAPI가 자동으로 422 에러를 반환."""
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from app.core.utils.datetime_util import DATE_FORMAT, now_kst


class ChatRequest(BaseModel):
    user_id: str = Field(min_length=1, description="메시지 작성 주체")
    session_id: str = Field(min_length=1, description="채팅 세션 식별자, 같은 값일 시 이전 대화 기억")
    # 보내면 그 값을 사용하고, 안 보내거나 비워 보내면 서버가 요청이 도착한 시간(KST)으로 채운다
    date: str = Field(
        default_factory=now_kst,
        description="질문 생성 일시 (YYYY-MM-DD HH:mm:ss, KST). 생략하거나 비우면 서버 도착 시간",
    )
    question: str = Field(min_length=1, max_length=2000, description="사용자 질문")

    @field_validator("date", mode="before")
    @classmethod
    def check_date(cls, value):
        """비어 있으면 현재 시간으로 채우고, 값이 있으면 실제 날짜/시간인지 검사 (틀리면 422)"""
        if value is None or (isinstance(value, str) and not value.strip()):
            return now_kst()
        datetime.strptime(value, DATE_FORMAT)
        return value
