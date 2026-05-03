Pydantic-AI Streaming Migration Plan 설계 검토
전반적으로 잘 구조화된 계획입니다. 구체적인 피드백을 드리겠습니다.

✅ 잘 된 부분
점진적 접근 방식이 현실적입니다. raw → pydantic_text → pydantic_agent 순서로 검증하면서 올라가는 구조는, 프로덕션 안정성을 유지하면서 실험할 수 있는 좋은 패턴입니다.
의사결정 기준(Decision Criteria)이 명확합니다. "언제 pydantic_text로 승격할 것인가"를 주관적 느낌이 아닌 측정 가능한 지표로 정의한 점이 좋습니다.
위험(Risks) 항목이 솔직합니다. 특히 pydantic-ai 버전 의존성 문제와 히스토리 변환 이슈를 미리 명시한 점은 나중에 디버깅 시간을 줄여줄 것입니다.

⚠️ 보완이 필요한 부분
1. 히스토리 변환 전략이 불명확합니다
문서에서 "load short raw history or pydantic history only if it is compatible"라고만 되어 있는데, 이 "compatible"의 판단 기준이 없습니다. 모드 전환 시 기존 세션의 히스토리가 있는 사용자에게 어떤 일이 발생하는지 정의가 필요합니다.
python# 예: 명시적인 변환 계층이 필요합니다
class HistoryAdapter:
    @staticmethod
    def raw_to_pydantic(raw_messages: list[dict]) -> list[ModelMessage]:
        ...
    
    @staticmethod  
    def pydantic_to_raw(messages: list[ModelMessage]) -> list[dict]:
        ...
모드 전환이 세션 중간에도 일어날 수 있다면, 이 변환 레이어는 필수입니다.

2. <ui_json> 파서 공유 방식이 구체적이지 않습니다
두 경로(raw, pydantic_text) 모두 <ui_json> 파서를 공유한다고 했지만, 현재 raw 경로에 파서가 인라인으로 있는지, 이미 분리된 함수인지 언급이 없습니다. 파서 중복이 생기면 가장 먼저 버그 불일치가 납니다.
리팩토링 전에 현재 상태를 명시하고, 공유 모듈로 추출하는 단계를 Patch 4 이전에 독립 작업으로 추가하는 것을 권장합니다.

3. build_local_text_stream_agent 의 시스템 프롬프트 전략이 부족합니다
pythonsystem_prompt=LOCAL_TUTOR_SYSTEM_PROMPT + metadata instructions,
단순 문자열 연결로만 기술되어 있는데, 메타데이터 지시문(<ui_json> 관련)을 어떻게 주입할지 설계가 빠져 있습니다. raw 경로에서 이 프롬프트가 얼마나 큰지에 따라 로컬 Gemma의 context 소비량이 달라지므로, 크기 제한이나 요약 전략도 고려해야 합니다.

4. Smoke Workflow의 측정 기준이 주관적입니다
"first visible answer time"을 기록한다고 했지만, 어떤 threshold를 합격/불합격으로 볼 것인지 없습니다. 예를 들어:
합격 기준 예시:
- first token latency: raw 대비 130% 이내
- 제안(suggestions) 파싱 성공률: 95% 이상
- <ui_json> 누출: 0건
이 기준이 없으면 "충분히 빠른지" 판단이 팀원마다 달라집니다.

5. 도구(Tool) 재도입 시점의 의존성이 누락되어 있습니다
Patch 6에서 툴을 다시 추가할 때 메모리 쓰기 툴의 레이턴시 기준만 언급했지만, 툴 실행 실패(타임아웃, 예외)가 스트림 전체에 어떻게 영향을 미치는지 처리 전략이 없습니다. 로컬 모델 특성상 툴 호출 판단 자체가 불안정할 수 있으므로, 툴 실행 실패 시 graceful degradation 정책이 필요합니다.

💡 추가 제안
모드별 메트릭을 로그에 남기는 것을 고려하세요. 스모크 테스트뿐만 아니라 실제 사용 중에도 모드별 first-token latency를 수집하면, pydantic_text 승격 여부를 데이터 기반으로 결정할 수 있습니다.
pydantic_agent 모드는 삭제 일정을 미리 잡으세요. 세 가지 모드를 영구적으로 유지하면 테스트/유지보수 부담이 3배가 됩니다. pydantic_text가 검증되면 raw와 pydantic_agent 중 하나를 deprecate하는 타임라인을 지금부터 계획에 포함하는 게 좋습니다.

요약
항목평가전체 방향성✅ 적절리스크 인식✅ 충분히스토리 변환 전략⚠️ 보완 필요파서 공유 구체성⚠️ 보완 필요합격 기준 정의⚠️ 보완 필요툴 실패 처리❌ 누락모드 deprecation 계획❌ 누락
핵심 뼈대는 견고하고, 위에서 지적한 부분들은 비교적 작은 보완으로 채울 수 있습니다. 특히 히스토리 변환과 <ui_json> 파서 공유는 초기에 제대로 잡지 않으면 나중에 버그 원인이 되기 쉬우니 우선순위를 높이길 권장합니다.