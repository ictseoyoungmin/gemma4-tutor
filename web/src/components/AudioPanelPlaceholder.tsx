export function AudioPanelPlaceholder() {
  return (
    <div style={wrapStyle}>
      <div style={waveformStyle} aria-hidden="true">
        <span style={{ height: 5 }} />
        <span style={{ height: 11 }} />
        <span style={{ height: 7 }} />
        <span style={{ height: 15 }} />
        <span style={{ height: 9 }} />
        <span style={{ height: 13 }} />
        <span style={{ height: 6 }} />
        <span style={{ height: 10 }} />
        <span style={{ height: 4 }} />
      </div>
      <div style={titleStyle}>오디오 세션 준비 중</div>
      <div style={copyStyle}>
        음성 인식, TTS 재생, 쉐도잉 연습, 발음 피드백을 한 흐름으로 묶는 연습 공간을 이 위치에 둘 예정입니다.
      </div>
      <div style={hintStyle}>지원 예정: 녹음 업로드, 듣기 재생, 반복 연습</div>
      <div style={hintStyle}>예시 흐름: 듣기 → 따라 말하기 → 발음 점검</div>
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

const waveformStyle: React.CSSProperties = {
  display: "flex",
  gap: 2,
  alignItems: "flex-end",
  height: 18,
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
