먼저 우선순위부터 고정하겠습니다.

웹↔API 연결 경로 정상화
백엔드 전환 시 세션/히스토리 격리
llama.cpp도 동일한 응답 계약 유지
런타임 헬스체크를 실제 downstream probe로 변경
운영성 개선: worker, queue, 버전 고정

현재 이 순서가 맞는 이유는, 지금 코드 기준으로는 포트/프록시 불일치와 세션 재사용만으로도 “curl은 되는데 UI 챗은 실패”가 충분히 재현되기 때문입니다.

1) web/src/components/workspace/TutorChatPanel.tsx
수정 목표
모델 변경 시 기존 sessionId 폐기
backend 변경 시 기존 turns와 streaming state 정리
런타임이 local인지 hosted인지 UI에 명확히 표시
선택 모델과 실제 런타임 모델이 다를 때 경고
지금 문제
selectedModel은 바뀌는데 sessionId는 그대로 유지됩니다.
그래서 Gemini 대화 히스토리를 들고 local llama.cpp로 이어붙일 수 있습니다.
프론트는 health 결과만 보고 “연결됨”으로 표시하지만, 실제로는 downstream llama 연결 실패를 구분하지 못합니다.
패치 내용
selectedModel 또는 selectedModelBackend가 바뀌면:
setSessionId(null)
현재 진행 중 스트림이 있으면 취소
선택적으로 turns를 유지하되, 이전 세션과 분리되었다는 시스템 메시지 추가
runtime.backend !== selectedModelBackend인 상태에서 전송 시:
전송 자체를 막거나
최소한 “현재 런타임과 선택 모델 backend가 다름” 경고 표시
fetchHealth() 결과를 받을 때, 단순 상태 문구 대신
runtime backend
runtime model
selected model
를 분리해서 보여주기
완료 기준
Google로 대화하다가 local 모델로 바꾸면 새 세션으로 시작
local→google, google→local 둘 다 히스토리 오염 없음
“연결됨”인데 실제 전송 실패하는 misleading 상태가 줄어듦
2) web/src/api.ts
수정 목표
스트리밍 요청 취소 가능하게 만들기
런타임 정보와 모델 목록 조회 API 추가 대응
에러 메시지를 더 구조적으로 처리
지금 문제
streamChatMessage()는 AbortController가 없어서 모델 전환/패널 닫기 때 기존 스트림이 살아남을 수 있습니다.
프론트 모델 목록이 하드코딩이라 실제 서버 모델과 어긋날 수 있습니다.
패치 내용
streamChatMessage()에 signal?: AbortSignal 추가
새 요청 시작 전 이전 controller abort
신규 API 함수 추가:
fetchRuntimeHealth()
fetchRuntimeModels()
스트리밍 error event 수신 시 원문 문자열만 던지지 말고
status
backend
model_name
message
형태로 래핑
완료 기준
모델 전환 시 이전 stream이 UI에 섞여 들어오지 않음
프론트 모델 picker가 서버 live state와 동기화됨
3) web/vite.config.ts
수정 목표
프록시 타깃을 하드코딩하지 않고 env 기반으로 통일
지금 문제
프록시는 http://127.0.0.1:8000
compose API는 8009
.env.compose.example도 VITE_API_BASE=http://127.0.0.1:8000
서로 모순입니다.
패치 내용
const apiBase = process.env.VITE_PROXY_TARGET ?? "http://127.0.0.1:8009"
proxy target을 env로 받도록 변경
allowedHosts는 계속 유지하되, dev/prod 분리 검토
완료 기준
로컬 dev, compose dev, tunnel dev에서 프록시 대상이 한 군데로 맞음
4) .env.compose.example
수정 목표
문서상 기본값과 실제 compose 동작 일치
패치 내용
VITE_API_BASE=http://127.0.0.1:8009 로 수정
가능하면 아래처럼 명시:
VITE_PROXY_TARGET=http://api:8009 또는 로컬 접근 규칙 문서화
APP_PORT=8009와 일치하도록 전체 예시 재정리
완료 기준
README, compose, frontend env 예시가 모두 같은 포트 사용
5) docker-compose.yml
수정 목표
포트/서비스 계약 통일
local profile 구조 정리
API health가 단순 app boot가 아니라 실제 backend readiness를 반영하도록 설계
지금 문제
api는 8009, web는 container 내부 5173인데 포트 매핑은 5174:5174
api는 llama 의존성이 없음
llama는 텍스트 채팅에도 항상 --mmproj를 강제합니다.
패치 내용
web 포트 매핑을 5173:5173으로 수정
local 전용 프로파일 도입:
llama-text
llama-vision
최소한 텍스트 챗 경로는 mmproj 없이도 뜨게 분리
api healthcheck는 /v1/health가 아니라 /v1/runtime/health 또는 deep health 사용
depends_on는 단순 추가보다, backend unreachable 시 health가 fail 되도록 설계하는 쪽이 낫습니다
완료 기준
docker compose up --build api web
docker compose --profile local up --build llama-text api web
두 경로가 모두 일관되게 동작
6) src/gemma_tutor_edge/config.py
수정 목표
설정을 “문자열 추정”이 아니라 “명시 계약”으로 바꾸기
패치 내용

새 필드 추가:

frontend_allowed_origins: list[str]
health_probe_timeout_sec: float = 3.0
runtime_models_cache_ttl_sec: int = 10
llama_require_same_session_backend: bool = True

기존 필드 보완:

llama_base_url는 /v1 포함 여부를 내부에서 normalize
validate_llama_assets는 텍스트-only local 모드에서는 mmproj를 필수로 보지 않게 분기
완료 기준
CORS와 health probe 동작이 코드에 하드코딩되지 않음
7) src/gemma_tutor_edge/llm.py
수정 목표
backend 판별을 model_name.endswith(".gguf")에 의존하지 않기
런타임 모델 discovery 추가
provider별 capability를 명시적으로 관리
지금 문제
현재는 .gguf면 local, 아니면 google입니다.
이건 모델명 문자열 규칙에 서비스 라우팅을 맡기는 구조라 위험합니다.
패치 내용
resolve_backend_for_model_name() 폐기 또는 축소
요청 스키마를 바꿔서:
backend: "google" | "llama_cpp" | None
model_name: str | None
로 분리
list_runtime_models(settings) 추가:
google path: configured models
llama path: GET /v1/models
probe_llama_runtime(settings) 추가:
/v1/models
optional lightweight completion check
완료 기준
backend는 명시적으로 선택되고, model_name은 해당 backend 내부에서만 검증됨
8) src/gemma_tutor_edge/agents.py
수정 목표
local path도 TutorResponse 계약 유지
지금 문제
Google tutor agent는 TutorResponse
local tutor agent는 str
즉 앱의 core response schema가 backend별로 달라집니다.
패치 내용
build_local_tutor_agent()를 Agent[TutorDeps, TutorResponse]로 변경
tools는 그대로 꺼도 되지만 output type은 동일하게 맞춤
system prompt를 이렇게 수정:
Do not call tools.
Return structured tutor response.
정말 local structured output이 불안정하면,
1차 raw text
2차 server-side parser
실패 시 safe fallback TutorResponse(message=<raw>)
로 감쌈
완료 기준
local/google 모두 ChatResponse.output 구조 동일
_normalize_tutor_output() 임시 완충 로직 의존도 감소
9) src/gemma_tutor_edge/services.py
수정 목표
세션 격리
런타임 에러 명확화
스트리밍 실패 시 graceful fallback
지금 문제
message_history = await store.load_chat_history(...)
이때 backend/model 메타 없이 같은 세션을 그대로 재사용합니다.
패치 내용
A. 세션 격리
chat 시작 시 session metadata 조회:
previous backend
previous model_name
요청 backend와 다르면:
기존 히스토리 사용 금지
새 세션 생성 또는 자동 reset
B. 에러 모델링
llama downstream 예외를 그대로 500 detail=str(exc) 하지 말고
backend_unreachable
model_not_served
structured_output_failed
stream_interrupted
로 구분
C. stream fallback
/v1/chat/stream에서 local structured stream이 깨질 경우
sync /v1/chat fallback 옵션 제공 가능
D. model settings
thinking과 extra_body.reasoning_format는 local server capability와 맞지 않으면 끄기
capability probe 결과에 따라 넣을 필드를 결정
완료 기준
backend 전환 후 무응답/이상 응답 제거
에러 로그만 봐도 어디서 죽었는지 구분 가능
10) src/gemma_tutor_edge/storage.py
수정 목표
chat session metadata 저장
background job claim atomicity 확보
SQLite 운영성 보강
패치 내용
A. chat_sessions 확장

컬럼 추가:

backend TEXT
model_name TEXT
schema_version INTEGER

메서드 추가:

get_chat_session_meta()
reset_chat_session()
B. queue atomic claim

현재 fetch_next_job()는 queued row를 읽기만 합니다. 이걸 다음처럼 바꿔야 합니다.

transaction 시작
queued 1건 선택
즉시 running으로 update
commit
그 row 반환
C. SQLite pragma

init 시:

PRAGMA journal_mode=WAL
PRAGMA synchronous=NORMAL
완료 기준
멀티 worker/재시작 시 job 중복 실행 위험 감소
세션 backend 충돌 감지 가능
11) src/gemma_tutor_edge/app.py
수정 목표
shallow health를 deep health로 교체
앱 팩토리 구조로 이동 준비
CORS를 설정 기반으로 이동
지금 문제
/v1/health는 설정값만 반환합니다.
실제 llama 연결 여부를 전혀 반영하지 않습니다.
패치 내용

신규 엔드포인트:

GET /v1/health/live
GET /v1/health/ready
GET /v1/runtime/models

/v1/health/ready 반환 예:

app db ok
selected backend
downstream reachable
served model ids
active configured model present 여부

또한:

allow_origins 하드코딩 제거
가능하면 global singleton 대신 create_app() 형태로 점진 이관
완료 기준
프론트가 “연결됨” 표시 전에 실제 runtime readiness를 확인 가능
12) scripts/run_dev_api.sh / scripts/run_dev_api.ps1
수정 목표
local 전환을 막는 하드코딩 제거
지금 문제
두 스크립트 모두 LLM_BACKEND=google 강제입니다.
패치 내용
기존 env 존중:
export LLM_BACKEND="${LLM_BACKEND:-google}"
APP_PORT도 env 존중:
${APP_PORT:-8009}
startup 시 현재 backend/base_url/model 출력
완료 기준
.env만 바꿔도 dev script가 local/google 둘 다 정상 기동
13) scripts/smoke_test_local_llama.sh
수정 목표
실제 장애를 잡는 테스트로 강화
패치 내용

현재 smoke test는 local 호출 자체는 보지만, 아래를 추가해야 합니다.

모델 전환 후 세션 reset 검증
/v1/runtime/models 검증
/v1/health/ready 검증
stream 응답에서 final payload 누락 여부 검증

기본 API 포트도 8009 기준 유지되어야 합니다. 이 스크립트는 이미 8009 기준이라 오히려 compose/web/env 쪽을 여기에 맞춰야 합니다.

14) src/gemma_tutor_edge/harness/runner.py
수정 목표
기본 포트 통일
local backend 회귀 테스트 추가
지금 문제
기본 base_url이 아직 8000입니다.
패치 내용
default base_url → http://127.0.0.1:8009
sample cases에 backend/model variation 추가
“google 세션 후 local 요청” 회귀 케이스 추가
완료 기준
이번 버그가 harness에서 재발 방지됨
15) src/gemma_tutor_edge/worker_control.py
수정 목표
운영 로그 확보
지금 문제
worker stdout/stderr가 버려집니다. 장애 분석이 어렵습니다.
패치 내용
DEVNULL 대신 파일 로깅 또는 rotating log
최소한 최근 stderr tail을 status endpoint에서 볼 수 있게 함
exit code 외에 last_error_summary 보존
완료 기준
worker가 죽었을 때 원인 추적 가능
16) pyproject.toml
수정 목표
핵심 inference dependency 버전 고정 범위 설정
패치 내용
pydantic-ai
openai
google-genai
httpx
에 대해 최소/최대 범위 지정
dev와 prod lockfile 전략 명확화
완료 기준
로컬 OpenAI-compatible 경로가 라이브러리 업데이트로 갑자기 깨질 확률 감소
추천 구현 순서
1차 커밋
vite.config.ts
.env.compose.example
docker-compose.yml
run_dev_api.sh/.ps1
harness/runner.py

이 단계는 연결 경로 정상화입니다.

2차 커밋
TutorChatPanel.tsx
api.ts
storage.py
services.py

이 단계는 세션 격리와 스트리밍 안정화입니다.

3차 커밋
llm.py
agents.py
app.py

이 단계는 backend 계약 정리와 runtime health 정교화입니다.

4차 커밋
worker_control.py
pyproject.toml

이 단계는 운영성/유지보수성 보강입니다.