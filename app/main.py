"""서버 실행 담당: 앱 생성, CORS 설정, 공통 에러 처리, 라우터 등록"""
from dataclasses import asdict

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from app.core.common.response.api_response import ApiResponse
from app.core.common.type.http_code import HttpStatusCode
from app.domain.llm.controller import llm_controller
from app.domain.llm.dto.request.chat_request import now_kst

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


# 4. 서버가 켜져 있는지 확인
# @app.get("/health")
# def health():
#     return {"status": "ok"}


# 5. controller 등록
app.include_router(llm_controller.router)


# 6. Swagger 문서를 열 때마다 새로 만들기
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




