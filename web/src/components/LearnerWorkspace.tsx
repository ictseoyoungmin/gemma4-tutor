import { AudioPanelPlaceholder } from "./AudioPanelPlaceholder";
import { ImageLessonPlaceholder } from "./ImageLessonPlaceholder";
import { SectionCard } from "./SectionCard";
import { TutorChatPanel } from "./TutorChatPanel";

export function LearnerWorkspace({ userId }: { userId: string }) {
  return (
    <div style={workspaceStyle}>
      <section style={heroStyle}>
        <div>
          <div style={eyebrowStyle}>Learner Workspace</div>
          <h2 style={heroTitleStyle}>Focused study flow for the learner</h2>
          <p style={heroCopyStyle}>
            This workspace is separate from the analytics dashboard. It is intended to become the
            main learning surface for tutoring, practice questions, review, and multimodal study.
          </p>
        </div>
        <div style={heroAsideStyle}>
          <div style={heroAsideLabelStyle}>Current shape</div>
          <ul style={heroListStyle}>
            <li>Start with tutor chat and guided prompts</li>
            <li>Move into practice or ready quiz packs</li>
            <li>Review explanations and keep studying in one place</li>
          </ul>
        </div>
      </section>

      <div style={gridStyle}>
        <SectionCard title="Tutor Chat">
          <TutorChatPanel userId={userId} />
        </SectionCard>

        <SectionCard title="Practice Flow">
          <div style={panelStackStyle}>
            <div style={focusCardStyle}>
              <div style={focusLabelStyle}>Primary learner action</div>
              <div style={focusTitleStyle}>Request the next study task</div>
              <div style={focusCopyStyle}>
                This area is reserved for the future TOEIC or tutoring loop: next question, answer
                submission, immediate explanation, and adaptive follow-up.
              </div>
            </div>

            <div style={queueCardStyle}>
              <div style={queueTitleStyle}>Planned learner modules</div>
              <ul style={queueListStyle}>
                <li>Single-item TOEIC question flow</li>
                <li>Writing correction workspace</li>
                <li>Ready-pack launch tray</li>
                <li>Reflection and recommendation panel</li>
              </ul>
            </div>
          </div>
        </SectionCard>
      </div>

      <div style={gridStyle}>
        <SectionCard title="Image-Based Study">
          <ImageLessonPlaceholder />
        </SectionCard>

        <SectionCard title="Audio Practice">
          <AudioPanelPlaceholder />
        </SectionCard>
      </div>
    </div>
  );
}

const workspaceStyle: React.CSSProperties = {
  display: "grid",
  gap: 18,
};

const heroStyle: React.CSSProperties = {
  display: "grid",
  gap: 16,
  gridTemplateColumns: "minmax(0, 1.6fr) minmax(280px, 1fr)",
  padding: 24,
  borderRadius: 24,
  background: "linear-gradient(135deg, #0f172a 0%, #1d4ed8 55%, #dbeafe 100%)",
  color: "white",
};

const eyebrowStyle: React.CSSProperties = {
  fontSize: 12,
  letterSpacing: 1.3,
  textTransform: "uppercase",
  opacity: 0.72,
  marginBottom: 10,
};

const heroTitleStyle: React.CSSProperties = {
  margin: 0,
  fontSize: 32,
  lineHeight: 1.1,
};

const heroCopyStyle: React.CSSProperties = {
  margin: "12px 0 0",
  lineHeight: 1.6,
  maxWidth: 680,
  color: "rgba(255,255,255,0.86)",
};

const heroAsideStyle: React.CSSProperties = {
  alignSelf: "stretch",
  borderRadius: 18,
  padding: 18,
  background: "rgba(255,255,255,0.12)",
  border: "1px solid rgba(255,255,255,0.18)",
};

const heroAsideLabelStyle: React.CSSProperties = {
  fontSize: 12,
  letterSpacing: 1.1,
  textTransform: "uppercase",
  opacity: 0.8,
  marginBottom: 10,
};

const heroListStyle: React.CSSProperties = {
  margin: 0,
  paddingLeft: 18,
  display: "grid",
  gap: 10,
  lineHeight: 1.5,
};

const gridStyle: React.CSSProperties = {
  display: "grid",
  gap: 16,
  gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
};

const panelStackStyle: React.CSSProperties = {
  display: "grid",
  gap: 14,
};

const focusCardStyle: React.CSSProperties = {
  borderRadius: 18,
  padding: 18,
  background: "#eff6ff",
  border: "1px solid #bfdbfe",
};

const focusLabelStyle: React.CSSProperties = {
  fontSize: 12,
  letterSpacing: 1,
  textTransform: "uppercase",
  color: "#1d4ed8",
  marginBottom: 8,
};

const focusTitleStyle: React.CSSProperties = {
  fontSize: 20,
  fontWeight: 700,
  marginBottom: 8,
  color: "#0f172a",
};

const focusCopyStyle: React.CSSProperties = {
  lineHeight: 1.55,
  color: "#334155",
};

const queueCardStyle: React.CSSProperties = {
  borderRadius: 18,
  padding: 18,
  background: "#f8fafc",
  border: "1px solid #e2e8f0",
};

const queueTitleStyle: React.CSSProperties = {
  fontWeight: 700,
  marginBottom: 10,
};

const queueListStyle: React.CSSProperties = {
  margin: 0,
  paddingLeft: 18,
  display: "grid",
  gap: 8,
  color: "#475569",
};
