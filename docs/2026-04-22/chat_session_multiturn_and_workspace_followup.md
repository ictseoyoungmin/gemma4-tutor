# 2026-04-22 Chat Session Multiturn And Workspace Follow-up

## 오늘 변경사항 정리

### 1. 튜터 채팅 멀티 턴 세션 문맥 유지 수정

문제:

- 프론트엔드는 같은 `session_id`를 계속 전달하고 있었지만, 서버는 이전 대화 히스토리를 다시 모델에 넣지 않고 매 요청마다 현재 입력만 처리하고 있었다.
- 그 결과 장기 기억(`memories`)은 동작해도, 같은 세션 안의 직전 대화 문맥은 이어지지 않았다.

적용 내용:

- `chat_sessions` 테이블을 추가해 세션별 모델 메시지 히스토리를 저장하도록 변경했다.
- `/v1/chat` 처리 시 `session_id` 기준으로 기존 히스토리를 읽어 `message_history`로 주입하도록 변경했다.
- 응답 후 `result.all_messages_json()`을 다시 저장해 다음 턴에서 이어서 사용할 수 있게 했다.

대상 파일:

- [src/gemma_tutor_edge/services.py](/home/ubuntu/gemma_tutor_edge/src/gemma_tutor_edge/services.py:38)
- [src/gemma_tutor_edge/storage.py](/home/ubuntu/gemma_tutor_edge/src/gemma_tutor_edge/storage.py:164)

효과:

- 같은 세션에서 두 번째, 세 번째 질문을 보낼 때 이전 사용자 발화와 튜터 응답이 함께 전달된다.
- 장기 기억과 별개로, 세션 내부 멀티 턴 문맥이 유지된다.

### 2. 멀티 턴 세션 회귀 테스트 추가

적용 내용:

- 첫 요청 후 저장된 세션 히스토리가 두 번째 요청의 `message_history`로 실제 전달되는지 검증하는 테스트를 추가했다.

대상 파일:

- [tests/test_chat_sessions.py](/home/ubuntu/gemma_tutor_edge/tests/test_chat_sessions.py:1)

실행 결과:

- `.venv/bin/pytest tests/test_chat_sessions.py tests/test_store.py tests/test_harness_runner.py`
- `4 passed`

### 3. 채팅 모델 목록 보정

확인 내용:

- 채팅 패널의 모델 선택 라벨이 일부 업데이트되어 있었고, `Gemma 4 26B (MoE)` 옵션이 노출된 상태다.

대상 파일:

- [web/src/components/workspace/TutorChatPanel.tsx](/home/ubuntu/gemma_tutor_edge/web/src/components/workspace/TutorChatPanel.tsx:44)

## `docs/2026-04-21/ui_study_workspace_slice_plan.md` 기준 미구현/후속 항목

문서의 각 Slice 상태는 `completed`로 적혀 있지만, 실제 코드 기준으로 아래 항목들은 아직 후속 구현 여지가 남아 있다.

### 1. 패널 열림 상태와 너비의 영속 저장 미구현

관련 문서 의도:

- 사용자 제어 UI 상태인 패널 open/close 상태와 width를 보존한다는 방향이 있었다.

현재 상태:

- 좌우 패널의 collapse 상태와 width는 [web/src/components/LearnerWorkspace.tsx](/home/ubuntu/gemma_tutor_edge/web/src/components/LearnerWorkspace.tsx:8) 내부 `useState`로만 관리된다.
- 새로고침이나 재방문 시 이전 사용자의 패널 설정은 복원되지 않는다.

정리:

- "사용자 제어 UI 상태"는 구현되어 있지만, "보존"은 세션 내 메모리 수준에 머물러 있다.
- `localStorage` 또는 서버 선호도 저장이 아직 없다.

### 2. 채팅 자동 스크롤 정책 고도화 미구현

관련 문서 메모:

- 사용자가 이미 하단 근처에 있을 때만 자동 스크롤하고, 아니라면 현재 위치를 보존하는 정책이 권장되어 있었다.

현재 상태:

- [web/src/components/workspace/TutorChatPanel.tsx](/home/ubuntu/gemma_tutor_edge/web/src/components/workspace/TutorChatPanel.tsx:79)에서 `turns`나 `isSending`이 바뀔 때마다 무조건 맨 아래로 스크롤한다.

정리:

- transcript 전용 스크롤 영역은 구현되었지만,
- 사용자가 위쪽 과거 메시지를 읽는 중일 때 위치를 유지하는 정책은 아직 없다.

### 3. 첨부 이미지를 실제 API로 전송하는 흐름 미구현

관련 문서 의도:

- clip 버튼을 실제 이미지 업로드 이벤트에 연결하고, 이미지 첨부 기반 학습 흐름의 기반을 만든다는 계획이 있었다.

현재 상태:

- 파일 선택 UI와 첨부 chip 표시는 구현되어 있다.
- 하지만 [web/src/api.ts](/home/ubuntu/gemma_tutor_edge/web/src/api.ts:193)의 `sendChatMessage`는 `user_id`, `session_id`, `message`, `model_name`만 전송한다.
- 현재 첨부 파일은 UI 상태로만 존재하고, `/v1/chat` 요청 본문에 포함되지 않는다.
- 서버의 [src/gemma_tutor_edge/schemas.py](/home/ubuntu/gemma_tutor_edge/src/gemma_tutor_edge/schemas.py:22) `ChatRequest`도 파일 입력을 받지 않는다.

정리:

- "파일 선택 이벤트 연결"까지는 구현됨
- "첨부 이미지를 실제 채팅/비전 처리 경로로 전달"은 아직 미구현

### 4. 단일 첨부만 지원하고, attachment 배열 구조는 미구현

관련 문서 메모:

- v1이 단일 이미지여도, 상태 구조는 배열로 가져가는 것이 이후 확장에 유리하다는 메모가 있었다.

현재 상태:

- [web/src/components/workspace/TutorChatPanel.tsx](/home/ubuntu/gemma_tutor_edge/web/src/components/workspace/TutorChatPanel.tsx:60)에서 `attachment: File | null` 단일 상태만 사용한다.

정리:

- 다중 첨부 확장을 고려한 상태 구조는 아직 아니다.

### 5. Ready Pack 세션 상태의 reducer/state-machine 정리는 미구현

관련 문서 메모:

- 풀이, 제출, 리뷰 흐름이 얽혀 있으므로 reducer 또는 작은 state machine 구조가 더 안정적일 수 있다는 메모가 있었다.

현재 상태:

- [web/src/components/workspace/ReadyPackPanel.tsx](/home/ubuntu/gemma_tutor_edge/web/src/components/workspace/ReadyPackPanel.tsx:121)에서 여러 `useState`와 분산된 업데이트로 세션 상태를 관리한다.

정리:

- 현재 기능은 동작하지만, 상태 전이가 커질수록 유지보수 리스크가 남아 있다.
- 문서상의 권장 구조는 아직 반영되지 않았다.

### 6. 타이머 토글 정책은 구현되었지만 정의가 완전히 닫히지 않음

관련 문서 메모:

- 토글이 단순 표시 숨김인지, 실제 시간 측정 정지인지 먼저 정책을 정하자는 메모가 있었다.

현재 상태:

- [web/src/components/workspace/ReadyPackPanel.tsx](/home/ubuntu/gemma_tutor_edge/web/src/components/workspace/ReadyPackPanel.tsx:149)에서 `timerEnabled`가 꺼지면 interval 업데이트가 멈춘다.
- UI에는 `paused`가 표시된다.

정리:

- 현재 구현은 "표시 중단 + 실시간 카운트 정지"에 가깝다.
- 시험 히스토리 기준으로 계속 시간을 누적할지 여부는 아직 명시적으로 정리되어 있지 않다.

## 권장 후속 순서

1. 채팅 첨부 이미지를 실제 API로 전달하는 multipart 또는 별도 업로드 경로 추가
2. 채팅 auto-scroll을 near-bottom 정책으로 보완
3. 좌우 패널 width/collapse 상태 영속화
4. Ready Pack 세션 상태를 reducer 또는 state machine으로 정리
5. 첨부 상태를 배열 구조로 전환

