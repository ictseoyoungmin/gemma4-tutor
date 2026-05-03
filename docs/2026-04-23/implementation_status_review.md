# 2026-04-23 구현 상태 점검 정리

기준 문서:

- `docs/2026-04-22/docker_compose_llamacpp_gemma4_migration_plan.md`
- `docs/2026-04-22/chat_session_multiturn_and_workspace_followup.md`
- `docs/2026-04-22/prioritized_workspace_followup_slices.md`

점검 기준:

- 문서에 적힌 완료 주장과 현재 코드 상태를 다시 대조했다.
- 가능하면 관련 테스트/빌드까지 확인했다.
- 분류는 `구현됨`, `부분 구현`, `미구현`으로 나눴다.

## 1. 구현됨

### A. 채팅 멀티턴 세션 문맥 유지

- `chat_sessions` 테이블이 실제로 추가되어 있다.
- `/v1/chat` 처리 시 `session_id` 기준 히스토리를 읽고 다시 저장하는 흐름이 구현되어 있다.
- 관련 근거:
  - `src/gemma_tutor_edge/storage.py`
  - `src/gemma_tutor_edge/services.py`
  - `tests/test_chat_sessions.py`

정리:

- 2026-04-22 문서의 "같은 세션 내 문맥 유지" 항목은 현재 구현되어 있다.

### B. 채팅 첨부 이미지를 실제 API로 보내는 흐름

- 프론트에서 첨부 이미지를 `FormData`로 `/v1/image/analyze`에 전송한다.
- `model_name`도 함께 전달한다.
- 응답은 기존 채팅 transcript 안에 assistant turn으로 표시된다.
- 관련 근거:
  - `web/src/api.ts`
  - `web/src/components/workspace/TutorChatPanel.tsx`
  - `src/gemma_tutor_edge/app.py`
  - `src/gemma_tutor_edge/services.py`
  - `tests/test_image_analyze_api.py`

정리:

- 2026-04-22 follow-up 문서에서 미구현으로 적혀 있던 이미지 첨부 실전 흐름은 현재 구현 완료 상태다.
- `prioritized_workspace_followup_slices.md`의 Slice 1 완료 표기도 코드와 일치한다.

### C. 채팅 auto-scroll near-bottom 정책

- transcript는 더 이상 무조건 맨 아래로 이동하지 않는다.
- 현재 스크롤 위치가 하단 근처일 때만 자동 하단 고정이 유지된다.
- 새 메시지를 보낼 때는 다시 하단 고정이 켜진다.
- 관련 근거:
  - `web/src/components/workspace/TutorChatPanel.tsx`

정리:

- 2026-04-22 follow-up 문서에서 후속 항목으로 적혀 있던 auto-scroll 고도화는 지금은 구현되어 있다.
- `prioritized_workspace_followup_slices.md`의 Slice 2 완료 표기와 일치한다.

### D. 첨부 상태의 배열 구조 전환

- 첨부 상태가 `File | null`이 아니라 `ChatAttachment[]` 구조로 바뀌어 있다.
- 썸네일 preview URL 생성/정리도 같이 처리한다.
- 관련 근거:
  - `web/src/components/workspace/TutorChatPanel.tsx`

정리:

- follow-up 문서의 "단일 첨부만 지원" 이슈는 현재 해소되었다.
- `prioritized_workspace_followup_slices.md`의 Slice 5 완료 표기와 일치한다.

### E. Ready Pack 상태 관리 reducer 전환

- `ReadyPackPanel`에서 `useReducer` 기반 `readyPackFlowReducer`로 상태 전이를 관리한다.
- launch, answer, navigate, timer toggle, submit, finish, workspace 복귀가 action으로 정리되어 있다.
- 관련 근거:
  - `web/src/components/workspace/ReadyPackPanel.tsx`

정리:

- follow-up 문서의 "reducer/state-machine 정리 미구현"은 현재 기준으로는 해소되었다.
- `prioritized_workspace_followup_slices.md`의 Slice 4 완료 표기와 일치한다.

### F. 모바일 드로어 불편 완화 패스

- 모바일에서 좌우 패널이 overlay처럼 동작한다.
- 모바일 진입 시 양쪽 패널이 자동 collapse 된다.
- 한쪽 패널을 열면 다른 패널을 닫는다.
- 모바일 backdrop 탭으로 닫을 수 있다.
- 관련 근거:
  - `web/src/components/LearnerWorkspace.tsx`
  - `web/src/components/workspace/workspace.css`

정리:

- 영속 저장은 아니지만, `prioritized_workspace_followup_slices.md`에서 조정된 Slice 3 범위인 "mobile discomfort pass"는 구현되어 있다.

### G. Docker Compose baseline + `.venv_hug` 다운로드 흐름

- `docker-compose.yml`, `Dockerfile.api`, `Dockerfile.web`, `.dockerignore`, `.env.compose.example`가 존재한다.
- README에 compose 기반 개발 흐름이 정리되어 있다.
- `.venv_hug` 전용 다운로드 스크립트가 Linux/PowerShell 양쪽으로 존재한다.
- 관련 근거:
  - `docker-compose.yml`
  - `Dockerfile.api`
  - `Dockerfile.web`
  - `.dockerignore`
  - `.env.compose.example`
  - `README.md`
  - `scripts/download_gemma4.sh`
  - `scripts/download_gemma4.ps1`

정리:

- migration plan의 Slice 1은 구현되어 있다.
- Slice 4도 "다운로드 스크립트와 문서화" 범위까지는 구현되어 있다.

### H. 백엔드 런타임 스위칭 기반

- `LLM_BACKEND=google | llama_cpp | test` 구성이 살아 있다.
- `google_model`, `llama_base_url`, `llama_model` 설정이 분리되어 있다.
- 모델 선택은 provider abstraction을 통해 이루어진다.
- `/v1/image/analyze`에서도 `model_name`을 별도로 받을 수 있다.
- 관련 근거:
  - `src/gemma_tutor_edge/config.py`
  - `src/gemma_tutor_edge/llm.py`
  - `src/gemma_tutor_edge/app.py`
  - `src/gemma_tutor_edge/services.py`

정리:

- migration plan의 Slice 3 목표 중 "환경변수 기반 backend switching" 핵심은 이미 구현되어 있다.

## 2. 부분 구현

### A. Docker migration plan의 Slice 4

현재 구현된 부분:

- `.venv_hug` 분리 전략 문서화
- 다운로드 helper script 추가
- 예상 모델 경로 안내

아직 부족한 부분:

- 로컬 `llama.cpp` 기동 전 GGUF/mmproj 존재 여부를 앱 또는 compose에서 검증하는 로직은 없다.
- Hugging Face 인증 가정이 README 수준에서 충분히 명시되었다고 보긴 어렵다.

정리:

- Slice 4는 "도구와 문서"는 구현됐지만, "실행 전 자산 검증"까지는 아직 아니다.

### B. 타이머 토글 정책

현재 상태:

- 토글을 끄면 interval 업데이트가 멈추고 UI에는 `paused`가 표시된다.

남은 점:

- 이것이 단순 표시 중단인지, 학습 기록 기준의 공식 시간 측정 중단인지에 대한 제품 정책은 코드상 명시적으로 닫혀 있지 않다.

정리:

- 기능은 구현되어 있지만, 2026-04-22 follow-up 문서에서 말한 정책 확정은 아직 부분적으로만 정리된 상태다.

### C. Docker Compose 검증 범위

현재 확인된 부분:

- `docker compose config`는 현재 워크스페이스에서 정상 해석된다.

아직 확인하지 못한 부분:

- 실제 `docker compose up api web`
- 실제 `llama` 서비스 포함 기동
- 컨테이너 간 통신까지 포함한 end-to-end 확인

정리:

- 구성 파일은 유효하지만, 전체 런타임 검증이 끝났다고 보기에는 아직 이르다.

## 3. 미구현

### A. Compose 내 `llama` 서비스 통합

- 현재 `docker-compose.yml`에는 `api`, `web`만 있고 `llama` 서비스는 없다.
- 모델 디렉터리 mount, `llama-server` 실행 옵션, `mmproj` 연결도 compose에 들어가 있지 않다.

정리:

- migration plan의 Slice 2는 아직 미구현이다.

### B. 패널 width / collapse 상태 영속 저장

- 좌우 패널 상태와 width는 `LearnerWorkspace.tsx` 내부 state로만 관리된다.
- `localStorage` 또는 서버 저장은 없다.

정리:

- 2026-04-22 follow-up 문서 기준 후속 항목 중 이 부분은 아직 미구현이다.
- `prioritized_workspace_followup_slices.md`도 실제로는 영속 저장을 구현하지 않고 모바일 개선으로 범위를 줄여 처리했다.

### C. Healthcheck와 개발 편의 하드닝

- compose에 `healthcheck`가 없다.
- `llama` healthcheck도 없다.
- migration plan에서 언급한 추가 DX hardening은 아직 보강되지 않았다.

정리:

- migration plan의 Slice 5는 아직 미구현이다.

### D. 로컬 Gemma 4 자산 존재 검사와 기동 차단

- 모델 파일이 없을 때 앱/compose 시작 전에 명확히 실패시키는 검증 로직이 없다.

정리:

- migration plan의 acceptance 중 "missing model files fail with a clear, actionable error"는 아직 충족되지 않았다.

## 4. 실행 확인 결과

확인한 항목:

- `./.venv/bin/pytest tests/test_chat_sessions.py tests/test_image_analyze_api.py tests/test_worker_control.py tests/test_cors.py`
- 결과: `4 passed`

- `cd web && npm run build`
- 결과: 성공

- `docker compose config`
- 결과: 성공

## 5. 최종 요약

현재 기준으로 2026-04-22 문서들에서 가장 크게 남아 있는 미구현 축은 아래 두 가지다.

- Docker 전환의 후반부:
  - compose 내 `llama` 서비스
  - healthcheck/DX hardening
  - 모델 자산 존재 검증

- 학습 워크스페이스의 영속 설정:
  - 좌우 패널 collapse/width 저장

반대로 2026-04-22 시점에 후속 과제로 적혀 있던 사용자 체감 기능 중 상당수는 이미 구현되어 있다.

- 멀티턴 세션 문맥 유지
- 이미지 첨부 실전 전송
- near-bottom auto-scroll
- attachment 배열 구조
- Ready Pack reducer 정리
- 모바일 drawer 불편 완화
