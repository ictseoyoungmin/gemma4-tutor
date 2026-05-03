# 2026-04-21 LC Asset Preparation Plan

## Background

LC 파트는 현재 텍스트 기반 문제 생성 안정화와 별개로, 실제 학습 경험에 필요한 이미지와 오디오 자산 준비 방식이 먼저 정리되어야 한다.

특히 다음 파트는 자산 전략이 다르다.

- `part1`: 이미지가 핵심이며, 필요하면 설명용 음성도 붙을 수 있음
- `part2`: 짧은 질문-응답 오디오가 핵심
- `part3`: 대화형 오디오가 핵심
- `part4`: 공지/안내/메시지형 오디오가 핵심

현재는 문제 텍스트와 generation metadata 중심으로 저장/검증하고 있으므로, LC 전용 asset lifecycle을 별도로 설계해야 한다.

## Goal

다음 개발 전에 아래를 합의 가능한 수준으로 문서화한다.

- LC 문제의 이미지/오디오 자산을 언제 생성할지
- seed asset과 generated asset을 어떻게 구분할지
- 자산 생성 실패 시 어떤 fallback을 사용할지
- 저장 스키마와 UI 노출을 어디까지 확장할지
- 운영자가 검수해야 하는 단계가 어디인지

## Open Decisions

### 1. Asset sourcing strategy

선택지:

- `seed-first`
- `generated-first`
- `hybrid`

권장 방향:

- `hybrid`

이유:

- 초기에는 품질과 운영 안정성을 위해 검증된 seed asset이 반드시 필요하다.
- 동시에 장기적으로는 generated asset을 실험할 수 있어야 한다.
- 따라서 기본 사용자 경험은 seed asset 위에 두고, generated asset은 별도 상태값과 검수 단계를 거쳐 승격시키는 구조가 가장 안전하다.

### 2. When assets are created

후보 시점:

- 문제 pack 생성 시점에 동기 생성
- 문제 pack 저장 후 백그라운드 후속 job으로 생성
- 미리 seed library를 구축하고 pack에는 reference만 연결

권장 방향:

- 이미지/오디오는 `pack 저장 후 후속 job`으로 생성하거나 연결한다.

이유:

- 텍스트 문제 생성과 asset 생성은 실패 유형이 다르다.
- 오디오/TTS 또는 이미지 생성은 latency가 크고 외부 의존성이 더 많다.
- pack 자체는 먼저 저장하고, asset 상태는 비동기적으로 채우는 편이 운영 관찰성과 복구성이 좋다.

### 3. Fallback behavior

필수 fallback 규칙:

- generated asset 생성 실패 시 즉시 `seed asset`으로 대체 가능해야 한다.
- seed asset도 없으면 해당 LC pack은 `asset_pending` 또는 `asset_missing` 상태로 남겨야 한다.
- 문제 텍스트는 성공했지만 asset이 비어 있으면 UI에서 노출 정책을 따로 정해야 한다.

권장 노출:

- 학습자 UI에서는 `ready` 상태 asset만 노출
- 운영자 UI에서는 `generated`, `seed`, `pending`, `failed`를 모두 구분 표시

### 4. Review workflow

검수 필요 수준:

- `part1` 이미지: 장면-문장 정합성 검수 필요
- `part2` 오디오: 질문/응답 길이, 발음, 잡음 검수 필요
- `part3/4` 오디오: 화자 수, 대화 분리, 길이 검수 필요

권장 정책:

- seed asset은 사전 검수 후 `approved`
- generated asset은 초기에 기본 `needs_review`
- 운영자가 승인하면 `approved_generated`

## Proposed Data Model

LC 자산 메타데이터는 Ready Pack 본문과 분리된 서브 구조로 두는 것이 적절하다.

초안 필드:

- `asset_type`: `image` | `audio`
- `part_type`
- `source`: `seed` | `generated` | `uploaded`
- `status`: `pending` | `ready` | `failed` | `needs_review` | `approved`
- `storage_path`
- `duration_ms`
- `voice_name`
- `image_prompt`
- `generation_model`
- `review_note`
- `linked_item_ids`

Ready Pack 레벨에는 요약 필드만 두는 방향이 좋다.

- `asset_status_summary`
- `asset_ready_count`
- `asset_failed_count`
- `asset_source_summary`

## Proposed Pipeline

### Phase A. Seed library first

- `part1`용 seed image set 준비
- `part2/3/4`용 seed audio set 준비
- 각 seed asset에 대응하는 canonical prompt/script를 고정
- item과 asset 간 reference 규칙 정의

### Phase B. Asset job separation

- Ready Pack 생성 job은 텍스트 pack 저장까지만 담당
- 별도 `generate_pack_assets` job이 LC asset 생성/연결 담당
- asset job 결과를 pack metadata와 operator UI에 반영

### Phase C. Review queue

- generated asset만 모아보는 검수 큐 제공
- 승인/반려/seed로 교체 동작 제공

## Part-Specific Plan

### Part 1

우선순위:

- 이미지 seed library부터 준비

작업 방향:

- 자주 쓰는 사무실/출장/회의/창고/접수대 장면 seed image bank 구성
- 각 이미지에 대해 허용 정답 문장 1개와 distractor 문장 3개를 고정
- 장기적으로 generated image 실험 가능하되, 초기 운영은 seed 중심

### Part 2

우선순위:

- 짧은 질문/응답 오디오 seed bank 구축

작업 방향:

- 질문 스크립트와 정답/오답 응답 패턴을 텍스트 기준으로 먼저 확정
- 이후 TTS 생성 또는 사전 녹음 asset 연결
- 너무 긴 응답, 비자연 발화, 발음 이슈는 검수 단계에서 걸러냄

### Part 3

우선순위:

- 2인 대화형 오디오 script schema 정리

작업 방향:

- 화자 구분이 되는 script 포맷 정의
- 오디오 생성 시 speaker metadata 보존
- 대화 길이와 질문 수 매핑 규칙 정의

### Part 4

우선순위:

- 1인 화자 공지/방송형 오디오 seed/generation 전략 정리

작업 방향:

- announcement, voicemail, briefing 등 유형 taxonomy를 먼저 정함
- 유형별 음성 톤과 길이 기준 정의

## UI/Operator Impact

운영자 UI에 필요한 최소 요소:

- asset source 표시: `seed` / `generated`
- asset status 표시: `pending` / `ready` / `failed` / `needs_review`
- item별 asset preview
- 실패 사유 표시
- seed로 교체 액션

학습자 UI에 필요한 최소 요소:

- 재생 가능한 오디오 또는 이미지 미리보기
- 아직 asset이 준비되지 않은 pack은 숨기거나 비활성화

## Suggested Slice Plan

### Slice A. LC asset schema draft

- asset metadata schema 추가
- Ready Pack summary에 asset 상태 요약 필드 추가

### Slice B. Seed asset registry

- seed image/audio registry 구조 추가
- item-to-asset 연결 규칙 구현

### Slice C. Asset background job

- `generate_pack_assets` 또는 `attach_pack_assets` job 추가
- pack 생성과 asset 생성 파이프라인 분리

### Slice D. Operator asset visibility

- `문제` 탭에 asset source/status 표시
- failed/pending asset filter 추가

### Slice E. Generated asset experiment

- 특정 part부터 generated image/audio 실험
- review workflow와 승격 정책 추가

## Recommendation

바로 구현을 시작할 때는 다음 순서가 가장 안전하다.

1. LC asset schema 초안 추가
2. seed asset registry 도입
3. asset background job 분리
4. operator UI에서 asset 상태 가시화
5. generated asset 실험은 마지막 단계에서 제한적으로 시작

## Notes

- LC는 텍스트 문제 생성보다 asset 품질 편차가 더 크므로, `generated-first`로 바로 가면 운영 부담이 커질 가능성이 높다.
- 초기 운영 안정성을 생각하면 `seed-first + generated-experiment` 구조가 가장 현실적이다.
- 이후 실제 구현 전에는 TTS 엔진, 이미지 생성 경로, 저장소 위치, 파일 포맷까지 추가로 합의가 필요하다.
