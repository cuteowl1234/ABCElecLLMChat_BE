"""에러 응답에 쓰는 HTTP 상태 코드와 메시지 모음."""
from enum import Enum

class HttpStatusCode(Enum):
    unprocessable_entity = (422, "예상치 못한 문제가 발생했습니다.")
    service_unavailable = (503, "AI 서버에 연결할 수 없습니다.")
    internal_server_error = (500, "AI 응답 생성 중 오류가 발생했습니다.")
