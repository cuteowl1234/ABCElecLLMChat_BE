"""요청 형식: POST /chat 명세의 Request
user_id, session_id, date, question을 받는다. date는 비우거나 생략하면 서버가 현재 한국 시간으로 채운다.
빈 질문, 형식이 틀린 날짜가 들어오면 FastAPI가 자동으로 422 에러를 반환한다."""
from datetime import datetime, timedelta, timezone

from pydantic import BaseModel, Field, field_validator

KST = timezone(timedelta(hours=9))  # 한국 시간대(UTC+9)로 고정
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"   # 명세 형식: YYYY-MM-DD HH:mm:ss


def now_kst() -> str:
    """현재 한국 시간을 'YYYY-MM-DD HH:mm:ss' 문자열로 반환"""
    return datetime.now(KST).strftime(DATE_FORMAT)


class ChatRequest(BaseModel):
    user_id: str = Field(min_length=1, description="메시지 작성 주체")
    session_id: str = Field(min_length=1, description="채팅 세션 식별자")
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


"""
#요청 형식: POST /chat 명세의 Request
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

#클라이언트가 보내는 요청의 형식을 정의한 코드입니다. question 문자열 하나를 받으며, 1~2000자로 길이를 제한합니다.
빈 질문이 들어오면 FastAPI가 자동으로 422 에러를 반환합니다.


class ChatRequest(BaseModel):
    user_id: str = Field(min_length=1, examples=["user"], description="메시지 작성 주체")
    session_id: str = Field(min_length=1, examples=["test-session"], description="채팅 세션 식별자")
    #date: str = Field(examples=[""], description="질문 생성 일시 (YYYY-MM-DD HH:mm:ss, KST)")
    question: str = Field(min_length=1, max_length=2000, examples=["안녕하세요"], description="사용자 질문")

    @field_validator("date")
    @classmethod
    def check_date(cls, value: str) -> str:
        #실제로 존재하는 날짜/시간인지 검사 (형식이 틀리거나 13월 같은 값이면 422)
        datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        return value



# 혹시 몰라 이전코드 그대로 남겨둠

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
    question: str = Field(min_length=1, max_length=2000)
"""