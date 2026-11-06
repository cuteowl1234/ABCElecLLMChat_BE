# ABC Electronics AI 고객지원 Backend

## 1. 프로젝트 개요
- ABC Electronics 고객의 제품 사용법, 보증·A/S, 배송·교환·반품 문의에 답하는 고객지원 챗봇의 Backend
- 회사 문서(제품 매뉴얼·보증 정책·배송 정책 PDF, FAQ)를 검색해 **문서에 근거한 답변** 제공

### 주요 기능
| 기능                    | 설명                                                                                       |
|-------------------------|--------------------------------------------------------------------------------------------|
| RAG 답변                | 질문 임베딩 → Chroma에서 관련 문서 조각 검색 → 해당 내용만 근거로 LLM 답변                 |
| 근거 없음 처리          | 검색 점수가 기준(`MIN_SCORE`) 미만이면 LLM 미호출, 고정 안내 문구로 응답                   |
| 출처 표시               | 실제 검색된 문서의 파일명을 코드에서 답변 끝에 `[출처]`로 추가                             |
| 대화 기억               | `session_id`별 최근 5턴 저장 후 프롬프트의 `[이전 대화]`로 전달                            |
| 제품 인식               | `ABC-200`, `abc200`, `ABC 200`, `식기세척기` 등을 하나의 모델명으로 인식                   |
| 모델명·제품명 이중 검색 | `ABC-200 사용법은?`과 `식기세척기 사용법은?`으로 둘 다 검색해 점수가 높은 조각 선택        |
| 제품 이어받기           | 질문에 제품이 없으면 최근 대화의 제품으로 검색, 답변에 기준 제품 안내                      |
| 무관한 질문 거르기      | 질문 자체의 관련도가 기준(`TOPIC_MIN_SCORE`) 미만이면 되묻는 문구로 응답                   |
| 할루시네이션 방지       | 프롬프트 규칙으로 문서 밖 내용 생성 금지, 문서에 없는 기능(`OO 기능`) 질문은 코드에서 차단 |

### 지원 범위
- 지원 제품: ABC-100(스마트 광파오븐), ABC-200(스마트 식기세척기), ABC-300(데스크 정수기)
- 지원 문서: 제품 매뉴얼(MAN), 보증·A/S 정책(WAR), 배송·교환·반품 정책(SHP), FAQ
- 범위 외: 회원/인증, 주문 조회, 상담원 연결

### 기술 stack
| 구분 | 사용 기술 |
|---|---|
| Web framework | FastAPI, Uvicorn |
| 임베딩 | sentence-transformers (`BAAI/bge-m3`) |
| Vector DB | Chroma (HTTP client) |
| LLM 호출 | n8n Webhook → Ollama (모델은 n8n 워크플로에서 지정) |

---

## 2. 개발 환경

| 항목 | 요구 사항 |
|---|---|
| Python | **3.12 이상**, 개발 환경 3.14 |
| 운영체제 | Windows에서 개발·검증, 그 외 OS 미검증 |
| 외부 service | Chroma 서버, n8n(워크플로 Published 상태), Ollama — 모두 실행 중이어야 `/chat` 동작 |
| Frontend | React (개발 서버 포트 3000 또는 5173) |

---

## 3. 설치·실행·검증

### 의존성 설치
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows PowerShell
pip install -r requirements.txt
```
- 성공 기준: 오류 없이 설치 완료
- 첫 실행 시 임베딩 모델(`BAAI/bge-m3`)을 Hugging Face에서 다운로드하여 시간 소요

### 실행
```bash
python -m uvicorn app.main:app --reload --port 8080
```
- 성공 기준: 터미널에 `Application startup complete.` 출력, `http://localhost:8080/docs`(Swagger) 접속 가능

---

## 4. 설정과 환경

- 설정 관리 위치: `app/core/config.py`
- 적용 방식: 환경 변수가 있으면 환경 변수 값, 없으면 코드 기본값 사용 (`os.getenv`)

| 환경 변수 | 의미 | 필수 | 예시 형식 |
|---|---|---|---|
| `N8N_WEBHOOK_URL` | LLM 답변을 받을 n8n Webhook 운영 URL | 사실상 필수 | `http://<host>:5678/webhook/n8n/chat` |
| `CHROMA_HOST` | Chroma 서버 주소 | 사실상 필수 | `localhost` 또는 `<host>` |
| `CHROMA_PORT` | Chroma 서버 포트 | 선택 (기본 8000) | `8000` |
| `COLLECTION_NAME` | Chroma 컬렉션 이름 (데이터 적재 담당자와 일치 필요) | 선택 | `abc_support_docs` |
| `EMBED_MODEL` | 임베딩 모델 (데이터 적재 시 모델과 **반드시 동일**) | 선택 | `BAAI/bge-m3` |
| `TOP_K` | 검색해서 가져올 문서 조각 수 | 선택 (기본 3) | `3` |
| `MIN_SCORE` | 근거로 인정할 최소 유사도 | 선택 (기본 0.55) | `0.55` |
| `TOPIC_MIN_SCORE` | 제품을 이어받기 전 질문 자체의 최소 관련도 | 선택 (기본 0.45) | `0.45` |
| `OLLAMA_URL`, `LLM_MODEL` | 현재 코드에서 미사용 (`config.py`에만 남음, 모델은 n8n 워크플로에서 지정) | 해당 없음 | `http://<host>:11434`, `qwen2.5:3b` |

### 점수 기준값 근거`  
- 측정 모델: `bge-m3` (2026-11-04 측정)
- 무관한 질문 최고 점수 약 0.38~0.40, 관련 질문 0.67 이상 → `MIN_SCORE` 0.55
- `TOPIC_MIN_SCORE`: 무관한 말(~0.40)과 이어지는 질문 사이 값으로 임시 설정, 추가 측정 필요

### 환경별 차이
- 해당 없음: 로컬 개발·시연 환경만 존재 (development/staging/production 구분 없음)

### Secret
- 사용 중인 비밀값(API key, token 등) 없음
- production secret management와 rotation 책임: 결정 필요

---

## 5. 구조와 Architecture

```
app/
├── main.py                               서버 생성, 로그 설정, CORS, 422 처리, 라우터 등록, Swagger 예시
├── core/                                 공통 부품
│   ├── config.py                         설정값
│   ├── common/
│   │   ├── exception/http_code.py        에러 코드·메시지 (422/500/503)
│   │   ├── exception/vector_store_unavailable_error.py   Chroma 실패 예외
│   │   └── response/api_response.py      공통 응답 {success, response, error}와 error 칸 형식(ApiError)
│   ├── utils/
│   │   └── datetime_util.py              KST 현재 시각(now_kst) 등 날짜 공통 기능
│   └── infra/                            외부 시스템 연결
│       ├── embedding.py                  문장 → 벡터
│       ├── chroma_client.py              Chroma 접속
│       └── n8n.py                        n8n Webhook 호출 (LLM 답변)
└── domain/llm/                           /chat 기능
    ├── controller/llm_controller.py      요청 수신, 예외 → 503/500 변환
    ├── dto/request/chat_request.py       요청 형식·검증
    ├── dto/response/chat_response.py     응답 형식
    ├── service/llm_service.py            처리 순서 (RAG 흐름)
    ├── repository/llm_repository.py      Chroma 검색 (제품 필터)
    ├── repository/chat_history_repository.py   세션별 대화 기록 (메모리)
    ├── model/retrieved_document.py       검색 결과 한 건의 형식
    └── prompt/chatbot/system_prompt.py   프롬프트 조립
```

### 계층 책임
| 계층 | 책임 |
|---|---|
| controller | 요청 수신, service 호출, 예외를 HTTP 상태 코드와 공통 응답으로 변환 |
| service | 처리 순서 결정 (검색어·제품 결정, 검색, 근거 판단, 없는 기능 차단, 프롬프트, LLM, 출처, 기록) |
| repository | 데이터 조회·저장 (Chroma 검색, 대화 기록) |
| infra | 외부 시스템 통신 (임베딩 모델, Chroma, n8n) |

### 요청 처리 흐름 (`POST /chat`)
```
Client
  → controller: ChatRequest 검증 (실패 시 422)
  → service.chat()
      1. 대화 기록 조회 (session_id)
      2. 검색어·제품 결정 (표기 통일, 제품 이어받기)
      3. 제품을 이어받은 경우: 원래 질문 관련도 확인 → 기준 미만이면 되묻기 응답
      4. 임베딩 → Chroma 검색
         - 제품 있음: 제품 필터 + 모델명·이름 이중 검색 → 점수 높은 조각 TOP_K개 (결과 없으면 전체 검색)
         - 제품 없음: 전체 검색
      5. MIN_SCORE 이상만 근거로 사용 / 없으면 주제를 빌려 재검색
      6. 기능 질문인데 기능 이름이 근거 문서에 없으면 근거 없음으로 처리
      7. 근거 있음 → 프롬프트 조립 → n8n(Ollama) → 답변 + 안내 + [출처]
         답변에 한자·일본어가 섞이면 한 번 재요청, 그래도 남으면 해당 문자 제거
         근거 없음 → 고정 안내 문구 (LLM 미호출)
      8. 대화 기록 저장 (안내·출처 제외)
  → controller: ApiResponse로 감싸서 반환

---

## 6. API

### 명세 위치와 version
- API 명세 위치: 팀 관리 명세 문서 (위치 기재 결정 필요)
- Swagger 문서: 서버 실행 후 `/docs`
- version 정책: 해당 없음 (단일 버전 `1.0.0`)

### `POST /chat`

**Request**
```json
{
  "user_id": "user",
  "session_id": "test-session",
  "date": "2026-11-05 10:00:00",
  "question": "ABC-100 보증기간은 얼마나 되나요?"
}
```
| 필드 | 규칙 |
|---|---|
| `user_id`, `session_id` | 1자 이상, 같은 `session_id`면 이전 대화(최근 5턴) 이어서 사용 |
| `date` | `YYYY-MM-DD HH:mm:ss` (KST), 생략하거나 비우면 서버 도착 시각으로 채움, 존재하지 않는 날짜면 422 |
| `question` | 1~2000자 |

**Response (성공, 200)**
```json
{
  "success": true,
  "response": {
    "user_id": "system",
    "session_id": "test-session",
    "date": "2026-11-05 10:00:05",
    "answer": "ABC-100의 무상 보증기간은 구매일로부터 12개월입니다.\n\n[출처] faq.csv"
  },
  "error": null
}
```
- `answer`에 줄바꿈(`\n`) 포함 → Frontend에서 `white-space: pre-line` 등으로 표시

**Response (실패)**
```json
{ "success": false, "response": null, "error": { "status_code": 503, "err_msg": "AI 서버에 연결할 수 없습니다." } }
```

| 상태 코드 | 상황 | err_msg |
|---|---|---|
| 422 | 요청 형식 오류 (빈 질문, 잘못된 날짜 등) | 예상치 못한 문제가 발생했습니다. |
| 503 | Chroma 또는 n8n 연결 실패, n8n 오류 응답 | AI 서버에 연결할 수 없습니다. |
| 500 | 그 밖의 오류 (n8n 빈 응답 등) | AI 응답 생성 중 오류가 발생했습니다. |

---

## 7. Database와 Migration

| 저장소 | 용도 | 비고 |
|---|---|---|
| Chroma (외부) | 문서 조각과 임베딩 벡터 | 이 Backend는 **조회만** 수행, 적재·스키마 관리는 데이터 담당 |
| 메모리 (`chat_history_repository`) | 세션별 최근 5턴 대화 | 서버 재시작 시 삭제, `Lock`으로 동시 접근 보호 |

- 사용하는 Chroma 메타데이터 키
  - `source_file`: 출처 표시
  - `chunk_index`: 조각 번호
  - `product_id`: 제품 필터
  - `page`: 현재 데이터에 없음, 추가 시 출처에 자동 표시
- 데이터에 있지만 현재 미사용: `document_code`(예: `MAN-200`), `product_name`, `category`
- migration, backup, data 보존 정책: 해당 없음 (이 Backend가 관리하는 영속 데이터 없음)

---

## 8. 외부 연동

| 대상 | 책임 경계 | timeout | 실패 시 |
|---|---|---|---|
| Chroma | 문서 검색 (적재는 데이터 담당) | chromadb 클라이언트 기본값 | `VectorStoreUnavailableError` → 503 |
| n8n Webhook | 프롬프트 전달 → Ollama 호출 → `{"answer": ...}` 반환 | 150초 (n8n 내부 Ollama 호출 120초보다 길게 설정) | 연결 실패·4xx/5xx → 503, 빈 답변 → 500 |
| Ollama | n8n 워크플로에서 호출 (이 Backend는 직접 호출 안 함) | n8n 워크플로 설정 | n8n 오류로 전달 |
| Hugging Face | 첫 실행 시 임베딩 모델 다운로드 | 라이브러리 기본값 | 서버 시작 후 첫 요청 실패 |

- retry: 해당 없음 (재시도 없이 즉시 503/500 반환)
- rate limit: 해당 없음
- local/test 대체
  - 환경 변수로 로컬 Chroma(`chroma run --path <dir> --port 8001`, 예시)와 로컬 n8n 주소 지정 가능
  - 로컬 데이터는 `EMBED_MODEL`·`COLLECTION_NAME`·메타데이터 키가 운영 데이터와 동일해야 함

### n8n 워크플로 구성
- 노드: Webhook → HTTP Request(Ollama `/api/generate`) → Respond to Webhook
- 입력: `body.prompt`
- 출력: `{"answer": "<Ollama response>"}`
- 워크플로 수정 후 반드시 **다시 Publish** (운영 URL 반영)
- 같은 질문에 답변이 달라지지 않도록 Ollama 옵션 `temperature: 0` 권장 (설정 여부 확인 필요)

---

## 9. 테스트

| 범위 | 상태 |
|---|---|
| unit / integration / contract / e2e | **미구성**: 이번 개발 범위에서 자동 테스트 생략 (가이드라인 MUST 예외, 승인·재검토 기록 필요) |
| 수동 검증 | Swagger와 Frontend 챗봇으로 시나리오 검증 (아래) |
| CI gate | 해당 없음 (미구성) |

### 수동 검증 시나리오 (같은 `session_id`로 순서대로)
1. `ABC-100 보증기간은 얼마나 되나요?` → 12개월 + `[출처]`
2. `그럼 배송은 얼마나 걸려?` → 2~3영업일 + `※ ABC-100 기준으로 안내드렸어요...`
3. `abc200은?` → ABC-200 배송 5~7영업일
4. `정수기 설치는 누가 해?` → ABC-300 전문기사 설치
5. `뿌릿` → `질문을 정확히 이해하지 못했어요...`
6. `ABC-200 사용법은?`, `abc200 사용법은?`, `식기세척기 사용법은?` → 모두 `ABC-200_manual.pdf` 근거로 절차 안내
7. `식기세척기 음성인식 기능 있어?` → `제공된 문서에서 관련 내용을 확인할 수 없습니다...` (로그 `Feature not in documents: 음성인식`)

- 예상 답변(보증기간, 배송 기간 등)은 Chroma 적재 데이터 기준으로 달라질 수 있음, 시연 전 실제 답변 확인 필요

---

## 10. 알려진 한계와 개선 방향

| 한계 | 현재 방식 | 개선 방향 |
|---|---|---|
| 제품명 없이 오래전 주제를 가리키는 질문 | 가장 최근 제품을 이어받음 | LLM 기반 질문 재작성 (Query Rewriting) |
| 무관한 질문 판단이 점수 기준 | `TOPIC_MIN_SCORE` | 의도 분류 (Intent Classification) |
| 비슷하지만 정답이 아닌 조각이 상위에 오는 경우 | 제품 필터 + 점수 | Reranker 도입 |
| 서버 재시작 시 대화 기록 삭제 | 메모리 저장 | Redis 등 외부 저장소 (`chat_history_repository`만 교체) |
| 작은 LLM의 문장 품질 | 프롬프트 규칙 | 더 큰 모델 (n8n 워크플로의 모델명 변경) |
| 제품 목록 하드코딩 | `PRODUCT_NAMES`, `PRODUCT_LABELS` | 제품 정보를 설정 파일이나 DB에서 로드 |
| 없는 기능 차단은 `OO 기능` 표현만 인식 | `FEATURE_PATTERN` 정규식 | 의도 분류 또는 LLM 검증 단계 추가 |
| 기능 이름이 문서에 글자 그대로 있어야 통과 (`건조`는 통과, 동의어는 차단될 수 있음) | 본문 문자열 포함 검사 | 동의어 사전 또는 임베딩 기반 비교 |
| 제품 필터 검색 시 임베딩·검색 2회 | 모델명·이름 이중 검색 | 적재 시 FAQ 문장 형식 통일 또는 Reranker |
| 같은 질문에도 답변 문장이 달라질 수 있음 | 작은 LLM의 무작위성 | n8n Ollama 옵션 `temperature: 0` |
| 출처에 문서 코드 미표시 | 파일명만 표시 | 메타데이터 `document_code`를 출처에 추가 (예: `MAN-200 (ABC-200_manual.pdf)`) |
| `config.py` 기본값에 외부 서버 주소 포함 | 코드 기본값 | 기본값을 `localhost`로 두고 환경 변수로 주입 |

- 규칙 기반 방식 선택 이유
  - 사용 중인 3B 규모 LLM은 질문 재작성 정확도가 낮음
  - LLM 2회 호출 시 응답 시간 약 2배 증가
