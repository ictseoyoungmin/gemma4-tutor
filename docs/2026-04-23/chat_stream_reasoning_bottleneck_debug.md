# 2026-04-23 Chat Stream + Reasoning Bottleneck Debug

## 요청 배경

- 로컬 `llama.cpp` 서버의 기본 Web UI에서는 reasoning과 답변이 즉시 보이는데,
- Learner Workspace의 자유 대화 패널에서는 몇 분이 지나도 응답이 보이지 않는 문제가 있었다.
- 목표는 병목 지점을 파악하고, 가능하면 자유 대화 패널에도 reasoning box를 추가하는 것이었다.

## 병목 분석

### 1. 가장 큰 병목은 프론트 렌더링 전 단계였다

- 기존 자유 대화 패널은 [web/src/api.ts](/home/ubuntu/gemma_tutor_edge/web/src/api.ts:180)의 `sendChatMessage()`로 `POST /v1/chat`을 호출한 뒤,
- 서버가 **완성된 최종 JSON**을 돌려줄 때까지 아무것도 렌더링하지 않았다.
- 따라서 실제 첫 토큰이 빨리 생성되더라도, 사용자 입장에서는 응답이 "아예 안 보이는" 상태가 길게 유지됐다.

### 2. 백엔드도 스트리밍 경로가 없었다

- 기존 [src/gemma_tutor_edge/app.py](/home/ubuntu/gemma_tutor_edge/src/gemma_tutor_edge/app.py:82)의 `/v1/chat`은 `handle_chat()` 완료 후 한 번에 응답했다.
- 기존 [src/gemma_tutor_edge/services.py](/home/ubuntu/gemma_tutor_edge/src/gemma_tutor_edge/services.py:38)의 `handle_chat()`도 `agent.run(...)` 완료를 기다린 뒤 저장과 응답을 수행했다.
- 즉, `llama.cpp` 자체가 느린 것만이 아니라, **앱 레이어가 스트리밍을 전혀 노출하지 않는 구조**가 체감 병목의 핵심이었다.

### 3. reasoning 정보는 완전히 불가능한 상태는 아니었다

- 설치된 `pydantic-ai` 내부를 확인해보니 OpenAI-compatible 스트림에서 `reasoning`/`reasoning_content`를 `ThinkingPart`로 매핑하는 코드가 이미 존재했다.
- 따라서 별도 SDK 교체 없이도, 스트림 이벤트를 열어주면 reasoning box를 붙일 수 있는 상태였다.

## 이번 작업

### 백엔드

- [src/gemma_tutor_edge/app.py](/home/ubuntu/gemma_tutor_edge/src/gemma_tutor_edge/app.py:94)에 `POST /v1/chat/stream` 추가
- [src/gemma_tutor_edge/services.py](/home/ubuntu/gemma_tutor_edge/src/gemma_tutor_edge/services.py:38)
  - 기존 `/v1/chat` 응답에 `reasoning`, `diagnostics` 추가
  - 새 `build_chat_stream()` 구현
  - `llama.cpp` 경로에서 `thinking` + `extra_body.reasoning_format=deepseek` 설정
  - 스트리밍 중 `reasoning_delta`, `message_delta`, `first_chunk_ms`, `final` 이벤트를 NDJSON으로 전달
- [src/gemma_tutor_edge/schemas.py](/home/ubuntu/gemma_tutor_edge/src/gemma_tutor_edge/schemas.py:36)
  - `ChatResponse`에 `reasoning`, `diagnostics` 필드 추가

### 프론트엔드

- [web/src/api.ts](/home/ubuntu/gemma_tutor_edge/web/src/api.ts:202)
  - `streamChatMessage()` 추가
  - `application/x-ndjson` 스트림 파서 추가
- [web/src/components/workspace/TutorChatPanel.tsx](/home/ubuntu/gemma_tutor_edge/web/src/components/workspace/TutorChatPanel.tsx:1)
  - 응답 대기 중 빈 상태로 멈추지 않도록 assistant placeholder turn 추가
  - reasoning delta와 answer delta를 실시간 반영
  - 최종 응답 후 intent, suggestion, diagnostics를 같은 turn에 정리
- [web/src/components/workspace/workspace.css](/home/ubuntu/gemma_tutor_edge/web/src/components/workspace/workspace.css:577)
  - assistant bubble 내부에 reasoning box 스타일 추가

### 검증 도구

- [scripts/smoke_test_local_llama.sh](/home/ubuntu/gemma_tutor_edge/scripts/smoke_test_local_llama.sh:16)
- [scripts/smoke_test_local_llama.ps1](/home/ubuntu/gemma_tutor_edge/scripts/smoke_test_local_llama.ps1:20)
  - `POST /v1/chat/stream` 스모크 테스트 추가

### 테스트

- [tests/test_llama_runtime_validation.py](/home/ubuntu/gemma_tutor_edge/tests/test_llama_runtime_validation.py:146)
  - 스트림 라우트 400 처리 테스트 추가
  - NDJSON 스트림 성공 응답 테스트 추가

## 기대 효과

- 기존에는 최종 JSON이 생성될 때까지 자유 대화창이 사실상 정지해 보였다.
- 이제는:
  - 먼저 reasoning box가 차기 시작하고,
  - 이어서 답변 본문이 점진적으로 보이며,
  - 마지막에 총 소요 시간과 첫 청크 시간을 확인할 수 있다.

## 남은 리스크 / 후속 과제

- 현재 reasoning이 실제로 얼마나 풍부하게 나오는지는 `llama-server`의 템플릿/옵션과 모델 특성에 영향을 받는다.
- structured output을 강제하는 현재 tutor agent 설계상, 원본 Web UI와 완전히 동일한 토큰 흐름은 아닐 수 있다.
- 필요하면 다음 단계에서:
  - 프론트에 reasoning 접기/펼치기,
  - diagnostics 전용 debug mode,
  - session history 길이에 따른 prompt 부하 표시
  를 추가할 수 있다.

## 요약 Plan

1. 자유 대화의 비가시 대기 시간을 줄이기 위해 스트리밍 경로를 노출한다.
2. `pydantic-ai`가 이미 처리 가능한 thinking stream을 그대로 reasoning box에 연결한다.
3. 첫 청크 시간과 총 응답 시간을 보여줘서 실제 병목을 UI에서도 확인 가능하게 만든다.
