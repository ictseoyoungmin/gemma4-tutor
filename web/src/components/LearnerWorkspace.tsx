import { AudioPanelPlaceholder } from "./AudioPanelPlaceholder";
import { ImageLessonPlaceholder } from "./ImageLessonPlaceholder";
import { TutorChatPanel } from "./TutorChatPanel";

const practiceModules = [
  {
    title: "TOEIC Part 5 Sprint",
    description: "Quick grammar-and-vocabulary rounds tuned for short, repeatable practice.",
    badge: "Live",
    tone: "featured" as const,
  },
  {
    title: "Sentence Repair",
    description: "Turn awkward English into natural phrasing with guided correction patterns.",
    badge: "",
    tone: "neutral" as const,
  },
  {
    title: "Warm-up Questions",
    description: "Low-friction prompts to start speaking or writing before a focused session.",
    badge: "",
    tone: "accent" as const,
  },
];

const nextQueue = [
  { label: "Review the last tutor suggestion and convert it into one practice item.", status: "queued" },
  { label: "Launch a ready quiz pack directly from this learner surface.", status: "planned" },
  { label: "Capture wrong answers and turn them into a focused retry loop.", status: "next" },
];

export function LearnerWorkspace({ userId }: { userId: string }) {
  return (
    <div style={workspaceShellStyle}>
      <div style={workspaceNavStyle}>
        <div style={brandStyle}>
          <div style={logoFrameStyle}>
            <div style={logoCoreStyle} />
          </div>
          <div>
            <div style={brandNameStyle}>StudyOS</div>
            <div style={brandSubStyle}>Learner Workspace</div>
          </div>
        </div>

        <div style={workspaceMetaStyle}>
          <div style={streakStyle}>study streak <strong style={{ color: "#ef9f27" }}>12 days</strong></div>
          <div style={avatarStyle}>{userId.slice(0, 2).toUpperCase()}</div>
        </div>
      </div>

      <div style={bodyGridStyle}>
        <aside style={sidebarStyle}>
          <TutorChatPanel userId={userId} />
        </aside>

        <main style={mainStyle}>
          <section style={heroStyle}>
            <div>
              <div style={heroEyebrowStyle}>Focused learning surface</div>
              <h2 style={heroTitleStyle}>Practice, review, and tutor guidance in one calm workspace.</h2>
              <p style={heroCopyStyle}>
                Keep analytics in the dashboard, but move the actual learning flow here. This space is designed to
                feel like a study console: low-noise, session-oriented, and ready for the TOEIC loop.
              </p>
            </div>

            <div style={heroStatsStyle}>
              <div style={heroStatCardStyle}>
                <span style={heroStatNumberStyle}>3</span>
                <span style={heroStatLabelStyle}>focus modes</span>
              </div>
              <div style={heroStatCardStyle}>
                <span style={{ ...heroStatNumberStyle, color: "#ef9f27" }}>1</span>
                <span style={heroStatLabelStyle}>live tutor</span>
              </div>
              <div style={heroStatCardStyle}>
                <span style={heroStatNumberStyle}>2</span>
                <span style={heroStatLabelStyle}>media panels</span>
              </div>
              <div style={heroStatCardStyle}>
                <span style={heroStatNumberStyle}>next</span>
                <span style={heroStatLabelStyle}>adaptive TOEIC loop</span>
              </div>
            </div>
          </section>

          <section>
            <div style={sectionHeadStyle}>
              <div style={sectionLabelStyle}>Practice modules</div>
              <div style={sectionActionStyle}>choose a study lane</div>
            </div>

            <div style={moduleGridStyle}>
              {practiceModules.map((module) => (
                <article
                  key={module.title}
                  style={
                    module.tone === "featured"
                      ? featuredModuleCardStyle
                      : module.tone === "accent"
                        ? accentModuleCardStyle
                        : moduleCardStyle
                  }
                >
                  {module.badge ? <div style={moduleBadgeStyle}>{module.badge}</div> : null}
                  <div
                    style={
                      module.tone === "featured"
                        ? featuredIconWrapStyle
                        : module.tone === "accent"
                          ? accentIconWrapStyle
                          : iconWrapStyle
                    }
                  >
                    <div
                      style={
                        module.tone === "accent"
                          ? accentIconShapeStyle
                          : module.tone === "featured"
                            ? featuredIconShapeStyle
                            : iconShapeStyle
                      }
                    />
                  </div>
                  <div style={moduleTitleStyle}>{module.title}</div>
                  <div style={moduleCopyStyle}>{module.description}</div>
                </article>
              ))}
            </div>
          </section>

          <section style={queueCardStyle}>
            <div style={sectionHeadStyle}>
              <div style={sectionLabelStyle}>Learning queue</div>
              <div style={sectionActionStyle}>what this workspace should do next</div>
            </div>

            <div style={queueListStyle}>
              {nextQueue.map((item, index) => (
                <div key={item.label} style={queueItemStyle}>
                  <div style={queueIndexStyle}>{index + 1}</div>
                  <div style={queueBodyStyle}>{item.label}</div>
                  <div style={queueStatusStyle}>{item.status}</div>
                </div>
              ))}
            </div>
          </section>

          <div style={mediaGridStyle}>
            <section style={mediaCardStyle}>
              <div style={mediaTitleStyle}>Image-Based Study</div>
              <div style={mediaCopyStyle}>
                Upload a page, sign, worksheet, or screenshot and turn it into vocabulary and practice material.
              </div>
              <div style={placeholderWrapStyle}>
                <ImageLessonPlaceholder />
              </div>
              <div style={comingBadgeStyle}>coming soon</div>
            </section>

            <section style={mediaCardStyle}>
              <div style={mediaTitleStyle}>Audio Practice</div>
              <div style={mediaCopyStyle}>
                Reserve this lane for shadowing, pronunciation scoring, and tutor-led repeat-after-me drills.
              </div>
              <div style={placeholderWrapStyle}>
                <AudioPanelPlaceholder />
              </div>
              <div style={comingBadgeStyle}>coming soon</div>
            </section>
          </div>
        </main>
      </div>
    </div>
  );
}

const workspaceShellStyle: React.CSSProperties = {
  background: "#0e0c0a",
  color: "#f5ede0",
  borderRadius: 24,
  border: "1px solid rgba(255,255,255,0.08)",
  overflow: "hidden",
  boxShadow: "0 18px 60px rgba(2, 6, 23, 0.28)",
};

const workspaceNavStyle: React.CSSProperties = {
  height: 56,
  background: "#161310",
  borderBottom: "1px solid rgba(255,255,255,0.08)",
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  padding: "0 22px",
};

const brandStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 12,
};

const logoFrameStyle: React.CSSProperties = {
  width: 28,
  height: 28,
  borderRadius: 8,
  background: "#854f0b",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
};

const logoCoreStyle: React.CSSProperties = {
  width: 12,
  height: 12,
  borderRadius: 3,
  background: "#fac775",
};

const brandNameStyle: React.CSSProperties = {
  fontSize: 15,
  fontWeight: 500,
};

const brandSubStyle: React.CSSProperties = {
  fontSize: 11,
  color: "#7d6f5e",
};

const workspaceMetaStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 16,
};

const streakStyle: React.CSSProperties = {
  fontSize: 13,
  color: "#7d6f5e",
};

const avatarStyle: React.CSSProperties = {
  width: 30,
  height: 30,
  borderRadius: "50%",
  background: "#27211a",
  border: "1px solid rgba(255,255,255,0.13)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  color: "#fac775",
  fontSize: 12,
  fontWeight: 600,
};

const bodyGridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "340px minmax(0, 1fr)",
  minHeight: 900,
};

const sidebarStyle: React.CSSProperties = {
  background: "#161310",
  borderRight: "1px solid rgba(255,255,255,0.08)",
  minHeight: "100%",
};

const mainStyle: React.CSSProperties = {
  padding: 24,
  display: "grid",
  gap: 20,
  background: "#0e0c0a",
};

const heroStyle: React.CSSProperties = {
  borderRadius: 20,
  padding: 26,
  background: "#161310",
  border: "1px solid rgba(255,255,255,0.08)",
  display: "grid",
  gridTemplateColumns: "minmax(0, 1fr) 220px",
  gap: 24,
  alignItems: "center",
};

const heroEyebrowStyle: React.CSSProperties = {
  fontSize: 10,
  letterSpacing: 1.8,
  textTransform: "uppercase",
  color: "#ba7517",
  marginBottom: 8,
};

const heroTitleStyle: React.CSSProperties = {
  margin: 0,
  fontSize: 30,
  lineHeight: 1.15,
  fontFamily: "\"Lora\", Georgia, serif",
  fontWeight: 400,
  color: "#f5ede0",
};

const heroCopyStyle: React.CSSProperties = {
  marginTop: 12,
  maxWidth: 520,
  lineHeight: 1.7,
  fontSize: 13,
  color: "#c4b49a",
};

const heroStatsStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "1fr 1fr",
  gap: 8,
};

const heroStatCardStyle: React.CSSProperties = {
  padding: 12,
  borderRadius: 12,
  background: "#1e1a15",
  border: "1px solid rgba(255,255,255,0.08)",
  textAlign: "center",
};

const heroStatNumberStyle: React.CSSProperties = {
  display: "block",
  fontSize: 22,
  fontFamily: "\"Lora\", Georgia, serif",
  fontWeight: 400,
  color: "#f5ede0",
};

const heroStatLabelStyle: React.CSSProperties = {
  display: "block",
  marginTop: 2,
  fontSize: 11,
  color: "#7d6f5e",
};

const sectionHeadStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  gap: 16,
  marginBottom: 12,
  flexWrap: "wrap",
};

const sectionLabelStyle: React.CSSProperties = {
  fontSize: 10,
  letterSpacing: 1.4,
  textTransform: "uppercase",
  color: "#7d6f5e",
};

const sectionActionStyle: React.CSSProperties = {
  fontSize: 12,
  color: "#ba7517",
};

const moduleGridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
  gap: 10,
};

const moduleCardBaseStyle: React.CSSProperties = {
  position: "relative",
  overflow: "hidden",
  borderRadius: 16,
  border: "1px solid rgba(255,255,255,0.08)",
  padding: 18,
  minHeight: 180,
};

const moduleCardStyle: React.CSSProperties = {
  ...moduleCardBaseStyle,
  background: "#161310",
};

const featuredModuleCardStyle: React.CSSProperties = {
  ...moduleCardBaseStyle,
  background: "#1c1005",
  border: "1px solid #854f0b",
};

const accentModuleCardStyle: React.CSSProperties = {
  ...moduleCardBaseStyle,
  background: "#141b0e",
  border: "1px solid rgba(138,184,90,0.28)",
};

const moduleBadgeStyle: React.CSSProperties = {
  position: "absolute",
  top: 12,
  right: 12,
  padding: "3px 8px",
  borderRadius: 999,
  background: "#854f0b",
  color: "#fac775",
  fontSize: 10,
};

const iconWrapStyle: React.CSSProperties = {
  width: 32,
  height: 32,
  borderRadius: 9,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  background: "#27211a",
  marginBottom: 12,
};

const featuredIconWrapStyle: React.CSSProperties = {
  ...iconWrapStyle,
  background: "#854f0b",
};

const accentIconWrapStyle: React.CSSProperties = {
  ...iconWrapStyle,
  background: "#1a2710",
  border: "1px solid rgba(138,184,90,0.3)",
};

const iconShapeStyle: React.CSSProperties = {
  width: 14,
  height: 14,
  borderRadius: 3,
  background: "#7d6f5e",
};

const featuredIconShapeStyle: React.CSSProperties = {
  ...iconShapeStyle,
  background: "#fac775",
};

const accentIconShapeStyle: React.CSSProperties = {
  width: 14,
  height: 14,
  borderRadius: "50%",
  background: "#8ab85a",
};

const moduleTitleStyle: React.CSSProperties = {
  fontSize: 13,
  fontWeight: 600,
  color: "#f5ede0",
  marginBottom: 6,
};

const moduleCopyStyle: React.CSSProperties = {
  fontSize: 12,
  lineHeight: 1.6,
  color: "#7d6f5e",
};

const queueCardStyle: React.CSSProperties = {
  borderRadius: 16,
  border: "1px solid rgba(255,255,255,0.08)",
  background: "#161310",
  padding: "14px 20px 8px",
};

const queueListStyle: React.CSSProperties = {
  display: "grid",
};

const queueItemStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 12,
  padding: "12px 0",
  borderBottom: "1px solid rgba(255,255,255,0.08)",
};

const queueIndexStyle: React.CSSProperties = {
  width: 22,
  height: 22,
  borderRadius: 6,
  background: "#27211a",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  fontSize: 11,
  color: "#7d6f5e",
  flexShrink: 0,
};

const queueBodyStyle: React.CSSProperties = {
  fontSize: 13,
  lineHeight: 1.45,
  color: "#c4b49a",
};

const queueStatusStyle: React.CSSProperties = {
  marginLeft: "auto",
  fontSize: 10,
  color: "#7d6f5e",
  textTransform: "uppercase",
  letterSpacing: 0.8,
};

const mediaGridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "1fr 1fr",
  gap: 10,
};

const mediaCardStyle: React.CSSProperties = {
  borderRadius: 16,
  border: "1px solid rgba(255,255,255,0.08)",
  background: "#161310",
  padding: 20,
};

const mediaTitleStyle: React.CSSProperties = {
  fontSize: 14,
  fontWeight: 600,
  color: "#f5ede0",
  marginBottom: 6,
};

const mediaCopyStyle: React.CSSProperties = {
  fontSize: 12,
  lineHeight: 1.65,
  color: "#7d6f5e",
  marginBottom: 14,
};

const placeholderWrapStyle: React.CSSProperties = {
  borderRadius: 12,
  background: "#1e1a15",
  border: "1px dashed rgba(255,255,255,0.13)",
  minHeight: 140,
  padding: 16,
  color: "#c4b49a",
};

const comingBadgeStyle: React.CSSProperties = {
  display: "inline-flex",
  marginTop: 12,
  padding: "4px 9px",
  borderRadius: 999,
  fontSize: 10,
  letterSpacing: 0.9,
  textTransform: "uppercase",
  background: "#27211a",
  color: "#7d6f5e",
  border: "1px solid rgba(255,255,255,0.13)",
};
