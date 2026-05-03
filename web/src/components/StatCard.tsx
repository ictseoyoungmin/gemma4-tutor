type Props = {
  label: string;
  value: string;
  hint?: string;
};

export function StatCard({ label, value, hint }: Props) {
  return (
    <div style={cardStyle}>
      <div style={{ fontSize: 13, opacity: 0.7 }}>{label}</div>
      <div style={{ fontSize: 30, fontWeight: 700, marginTop: 8 }}>{value}</div>
      {hint ? <div style={{ fontSize: 12, opacity: 0.65, marginTop: 8 }}>{hint}</div> : null}
    </div>
  );
}

const cardStyle: React.CSSProperties = {
  border: "1px solid #e5e7eb",
  borderRadius: 20,
  padding: 18,
  background: "white",
  boxShadow: "0 8px 24px rgba(15, 23, 42, 0.06)",
};
