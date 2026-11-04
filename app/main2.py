from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.domain.llm.controller import llm_controller

"""서버를 생성하고 실행 설정을 하는 코드입니다. FastAPI 앱을 만들고, React에서 호출할 수 있도록 CORS를 허용합니다. 
그리고 controller의 라우터를 등록합니다. 서버 상태를 확인하는 /health 주소도 여기에 있습니다."""

app = FastAPI(title="AI 고객지원 및 고객문의 서비스", version="1.0.0")

app.add_middleware(CORSMiddleware,
                   allow_origins=["http://localhost:3000", "http://localhost:5173"],
                   allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(llm_controller.router)