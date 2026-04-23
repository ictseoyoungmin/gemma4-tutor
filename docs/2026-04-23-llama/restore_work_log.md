# 2026-04-23 Llama Restore Work Log

## 완료한 작업

### 1. 세션 메타 저장 및 backend/model 전환 시 세션 분리
- `chat_sessions` 테이블에 `backend`, `model_name` 컬럼을 추가했다.
- 서버가 기존 `session_id`의 메타를 조회한 뒤, 현재 요청의 backend 또는 model이 다르면 새 `session_id`를 발급하도록 바꿨다.
- 분리된 경우 응답 `diagnostics`에 아래 정보를 남긴다.
  - `session_reset`
  - `replaced_session_id`
  - `session_reset_reason`

### 2. local tutor 응답 계약 복구
- `build_local_tutor_agent()`를 다시 `TutorResponse` 기반으로 맞췄다.
- local tutor도 기존 tutor tools를 공유하도록 바꿨다.
- 그 결과 local 경로에서도 아래 항목이 다시 살아날 수 있는 상태로 복구했다.
  - `detected_intent`
  - `memory_to_store`
  - `suggested_next_actions`
  - tool-based personalization / routing

### 3. 프론트 모델 전환 시 세션/스트림 정리
- 모델이 바뀌면 진행 중인 스트림을 `AbortController`로 중단한다.
- 모델이 바뀌면 기존 `sessionId`를 폐기하고 새 세션 안내 메시지를 넣는다.
- 첨부 이미지와 전송 상태도 함께 정리해서 이전 세션 흔적이 남지 않게 했다.
- helper 문구에서 runtime backend와 현재 선택 모델 backend가 다를 때 이를 명시한다.

### 4. 회귀 테스트 보강
- `tests/test_chat_sessions.py`에 model 변경 시 세션 분리 회귀 케이스를 추가했다.
- 기존 fake agent가 현재 `handle_chat()` 시그니처와 맞도록 `model_settings` 인자를 받게 고쳤다.

## 수정 파일
- `src/gemma_tutor_edge/agents.py`
- `src/gemma_tutor_edge/schemas.py`
- `src/gemma_tutor_edge/services.py`
- `src/gemma_tutor_edge/storage.py`
- `web/src/api.ts`
- `web/src/components/workspace/TutorChatPanel.tsx`
- `tests/test_chat_sessions.py`

## 확인 결과
- `npm run build` 통과
- Python 테스트는 이 세션에서 `pytest` 출력이 비정상적으로 멈추는 현상이 있어 완전한 종료 로그까지 확보하지 못했다.
  - 다만 수집 단계 경로 문제는 `APP_DB_PATH`, `APP_STORAGE_DIR`를 워크스페이스 경로로 고정하면 해소된다.

## 남은 확인 포인트
- 실제 local llama.cpp 런타임에서 structured output이 안정적으로 유지되는지 확인
- local path에서 tool 호출이 다시 발생하는지 실런타임 로그로 확인
- 필요하면 다음 단계에서 `/v1/runtime/models`, `/v1/runtime/health` 분리와 프론트 모델 목록 live sync까지 확장
