export const navTabs = ["학습 공간", "분석", "Ready Pack"];

export const heroTags = ["TOEIC 준비중", "LC · RC"];

export const heroStats = [
  { value: "87", label: "평균 점수", delta: "+3.2 이번 주", accent: true },
  { value: "24", label: "퀴즈 완료", delta: "이번 달" },
  { value: "142", label: "학습 메모리", delta: "+12 오늘" },
];

export const skillProgress = [
  { name: "Part 5 문법", score: "82%", width: "82%", tone: "default" },
  { name: "어휘", score: "74%", width: "74%", tone: "amber" },
  { name: "작문 교정", score: "68%", width: "68%", tone: "green" },
  { name: "독해 속도", score: "91%", width: "91%", tone: "cream" },
];

export const readyPacks = [
  { name: "Part 5 핵심 문법 40선", meta: "40문항 · 30분", difficulty: "easy" },
  { name: "비즈니스 어휘 실전편", meta: "60문항 · 45분", difficulty: "med" },
  { name: "RC 고난도 모의고사", meta: "100문항 · 75분", difficulty: "hard" },
];

export const practiceModules = [
  {
    title: "다음 학습 과제",
    description: "튜터에게 맞춤형 TOEIC 문제 또는 학습 태스크를 요청합니다.",
    badge: "추천",
    variant: "primary",
  },
  {
    title: "작문 교정",
    description: "문장을 입력하고 즉각적인 교정과 상세 설명을 받아보세요.",
    variant: "slate",
  },
  {
    title: "Ready Pack 실행",
    description: "저장된 퀴즈 팩으로 집중 모드 학습을 시작합니다.",
    variant: "green",
  },
];

export const queueItems = [
  "Ready Pack 런처 — 대시보드에서 준비된 팩을 학습 화면으로 즉시 실행",
  "작문 교정 워크스페이스 — 첨삭 및 재작성 보조 도구",
  "성찰 및 추천 패널 — 학습 후 요약과 다음 단계 추천",
];

export const attendance = [
  { day: "월", value: "1", state: "done" },
  { day: "화", value: "2", state: "done" },
  { day: "수", value: "3", state: "done" },
  { day: "목", value: "4", state: "done" },
  { day: "금", value: "5", state: "done" },
  { day: "토", value: "6", state: "missed" },
  { day: "일", value: "7", state: "done" },
  { day: "월", value: "8", state: "done" },
  { day: "화", value: "9", state: "done" },
  { day: "수", value: "10", state: "done" },
  { day: "목", value: "11", state: "done" },
  { day: "금", value: "12", state: "done" },
  { day: "토", value: "13", state: "today" },
  { day: "일", value: "14", state: "idle" },
];

export const achievements = [
  { icon: "🏆", title: "10일 연속 학습", description: "꾸준한 학습 습관 형성", unlocked: true },
  { icon: "⚡", title: "빠른 학습자", description: "퀴즈 20개 완료", unlocked: true },
  { icon: "🎯", title: "90점 돌파", description: "평균 점수 90점 이상 달성", unlocked: false },
  { icon: "📚", title: "메모리 마스터", description: "학습 메모리 200개 저장", unlocked: false },
];

export const starterPrompts = ["TOEIC Part 5", "문장 교정", "워밍업", "어휘"];
