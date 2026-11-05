"""서버 실행 담당: 앱 생성, CORS 설정, 공통 에러 처리, 라우터 등록"""
import logging # 환각 현상 로그 기록 확인
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from app.core.common.response.api_response import ApiResponse
from app.core.common.type.http_code import HttpStatusCode
from app.domain.llm.controller import llm_controller
from app.domain.llm.dto.request.chat_request import now_kst

# 0. 로그 설정: RAG 검색 결과(출처·점수·제품 필터)를 터미널에서 볼 수 있게 INFO 등급부터 출력
logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(name)s - %(message)s")
# 1. 서버 생성
app = FastAPI(title="AI 고객지원 및 고객문의 서비스", version="1.0.0")

# 2. React(FE)에서 호출할 수 있도록 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. 요청 형식 오류(422)도 공통 응답 구조로 반환
@app.exception_handler(RequestValidationError)
async def validation_error_handler(request, exc):
    body = ApiResponse.fail(
        HttpStatusCode.unprocessable_entity
    )

    return JSONResponse(
        status_code=422,
        content=body.to_dict(),
    )

# 4. controller 등록
app.include_router(llm_controller.router)

# 5. Swagger 문서를 열 때마다 새로 만들기
#    요청 예시를 명세 순서대로 넣고, date는 문서를 연 시점의 현재 시간(KST)으로 채운다
def fresh_openapi():
    schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
    schema["components"]["schemas"]["ChatRequest"]["examples"] = [{
        "user_id": "user",
        "session_id": "test-session",
        "date": now_kst(),
        "question": "안녕하세요.",
    }]
    return schema

app.openapi = fresh_openapi




