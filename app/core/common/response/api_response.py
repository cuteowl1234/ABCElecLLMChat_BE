"""{success, response, error}를 만드는 클래스"""
from dataclasses import dataclass, asdict
from typing import TypeVar
from app.core.common.exception.api_error import ApiError
from app.core.common.type.http_code import HttpStatusCode

T = TypeVar('T')

@dataclass
class ApiResponse[T]:
    success: bool
    response: T | None
    error: ApiError | None

    @classmethod
    def ok(cls, data: T) -> "ApiResponse[T]":
        """성공 응답"""
        return cls(success=True, response=data, error=None)

    @classmethod
    def fail(cls, http_code: HttpStatusCode) -> "ApiResponse[None]":  # 💡 custom_msg에서 err_msg로 변경
        """실패 응답을"""
        api_error = ApiError(
            status_code=http_code.value[0],
            err_msg=http_code.value[1],  # 변수명 일치
        )
        return cls(
            success=False,
            response=None,
            error=api_error
        )

    def to_dict(self) -> dict:
        """JSONResponse에 바로 넣을 수 있도록 딕셔너리로 변환"""
        return asdict(self)

