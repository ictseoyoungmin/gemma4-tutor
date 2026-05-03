export function ImageLessonPlaceholder() {
  return (
    <div style={wrapStyle}>
      <svg width="24" height="22" viewBox="0 0 22 20" fill="none" aria-hidden="true">
        <rect x="1" y="1" width="20" height="18" rx="3" stroke="#4a3f31" strokeWidth="1.2" />
        <circle cx="7" cy="7" r="2" stroke="#4a3f31" strokeWidth="1.2" />
        <path d="M1 14l5-5 4 4 3-3 5 5" stroke="#4a3f31" strokeWidth="1.2" strokeLinejoin="round" />
      </svg>
      <div style={titleStyle}>이미지 드롭 또는 클릭</div>
      <div style={copyStyle}>
        교재 사진, 표지판, 스크린샷, 문제집 일부를 올리면 어휘 추출, 장면 설명, 이미지 기반 미니 퀴즈로 이어지게 만들 예정입니다.
      </div>
      <div style={hintStyle}>지원 예정: PNG, JPG, 교재 캡처</div>
      <div style={hintStyle}>예시 흐름: 어휘 추출 → 설명 → 미니 퀴즈</div>
    </div>
  );
}

const wrapStyle: React.CSSProperties = {
  display: "grid",
  justifyItems: "center",
  textAlign: "center",
  gap: 6,
  minHeight: 96,
  alignContent: "center",
};

const titleStyle: React.CSSProperties = {
  fontSize: 11,
  color: "#c4b49a",
  fontWeight: 600,
};

const copyStyle: React.CSSProperties = {
  fontSize: 11,
  lineHeight: 1.6,
  color: "#7d6f5e",
  maxWidth: 280,
};

const hintStyle: React.CSSProperties = {
  fontSize: 10,
  color: "#6d6153",
  lineHeight: 1.5,
};
