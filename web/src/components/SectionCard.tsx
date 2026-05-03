import type { PropsWithChildren } from "react";

export function SectionCard({ title, children }: PropsWithChildren<{ title: string }>) {
  return (
    <section style={cardStyle}>
      <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 14 }}>{title}</div>
      {children}
    </section>
  );
}

const cardStyle: React.CSSProperties = {
  border: "1px solid #e5e7eb",
  borderRadius: 20,
  padding: 20,
  background: "white",
  boxShadow: "0 8px 24px rgba(15, 23, 42, 0.06)",
};
