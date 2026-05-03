import { LearnerWorkspace } from "./components/LearnerWorkspace";

const defaultUserId = "demo-user";

export default function App() {
  return (
    <div style={pageStyle}>
      <LearnerWorkspace userId={defaultUserId} />
    </div>
  );
}

const pageStyle: React.CSSProperties = {
  minHeight: "100dvh",
  background: "#050403",
  padding: 0,
};
