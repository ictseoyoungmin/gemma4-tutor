import { useEffect, useMemo, useState } from "react";
import { fetchDashboardDetail, queuePrebuildJob } from "./api";
import { AudioPanelPlaceholder } from "./components/AudioPanelPlaceholder";
import { ChatWorkspacePlaceholder } from "./components/ChatWorkspacePlaceholder";
import { ImageLessonPlaceholder } from "./components/ImageLessonPlaceholder";
import { SectionCard } from "./components/SectionCard";
import { StatCard } from "./components/StatCard";
import type { DashboardDetail } from "./types";

const defaultUserId = "demo-user";

export default function App() {
  const [userId, setUserId] = useState(defaultUserId);
  const [detail, setDetail] = useState<DashboardDetail | null>(null);
  const [status, setStatus] = useState("Loading dashboard...");

  useEffect(() => {
    void loadDashboard(userId);
  }, [userId]);

  async function loadDashboard(targetUserId: string) {
    try {
      setStatus("Loading dashboard...");
      const data = await fetchDashboardDetail(targetUserId);
      setDetail(data);
      setStatus("Dashboard ready");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Unknown error");
    }
  }

  async function handleQueueJob() {
    try {
      setStatus("Queueing background job...");
      await queuePrebuildJob(userId, "Daily commuting expressions");
      await loadDashboard(userId);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Unknown error");
    }
  }

  const stats = useMemo(() => {
    if (!detail) return [];
    return [
      {
        label: "Average Score",
        value: `${Math.round(detail.overview.average_score * 100)}%`,
        hint: "Auto-updates after quiz submissions",
      },
      {
        label: "Saved Memories",
        value: String(detail.overview.memory_count),
        hint: "Conversation facts and learning context",
      },
      {
        label: "Quiz Attempts",
        value: String(detail.overview.attempts_count),
        hint: "Feeds skill analytics and prebuild jobs",
      },
      {
        label: "Ready Packs",
        value: String(detail.ready_packs.length),
        hint: "Prebuilt quiz packs from background worker",
      },
    ];
  }, [detail]);

  return (
    <div style={pageStyle}>
      <header style={headerStyle}>
        <div>
          <div style={{ fontSize: 12, letterSpacing: 1.2, textTransform: "uppercase", opacity: 0.65 }}>
            Gemma Tutor Edge
          </div>
          <h1 style={{ margin: "8px 0 0", fontSize: 34 }}>Frontend Dashboard Scaffold</h1>
          <p style={{ marginTop: 8, maxWidth: 820, lineHeight: 1.55, opacity: 0.8 }}>
            Competition demo UI for learner progress, ready quiz packs, achievements, and background job visibility.
            Chat, image learning, and detailed analytics panels are intentionally scaffolded for later implementation.
          </p>
        </div>
        <div style={toolbarStyle}>
          <input value={userId} onChange={(e) => setUserId(e.target.value)} style={inputStyle} />
          <button onClick={() => void loadDashboard(userId)} style={primaryButtonStyle}>Refresh</button>
          <button onClick={() => void handleQueueJob()} style={secondaryButtonStyle}>Queue Prebuild Job</button>
        </div>
      </header>

      <div style={statusStyle}>{status}</div>

      <div style={statsGridStyle}>
        {stats.map((item) => (
          <StatCard key={item.label} label={item.label} value={item.value} hint={item.hint} />
        ))}
      </div>

      <div style={twoColGridStyle}>
        <SectionCard title="Skill Snapshot">
          <table style={tableStyle}>
            <thead>
              <tr>
                <th>Skill</th>
                <th>Score</th>
                <th>Delta</th>
                <th>Evidence</th>
              </tr>
            </thead>
            <tbody>
              {detail?.skill_snapshots.map((skill) => (
                <tr key={skill.skill_name}>
                  <td>{skill.skill_name}</td>
                  <td>{Math.round(skill.score * 100)}%</td>
                  <td>{skill.delta >= 0 ? "+" : ""}{Math.round(skill.delta * 100)}%</td>
                  <td>{skill.evidence_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </SectionCard>

        <SectionCard title="Background Queue & Ready Packs">
          <div style={{ marginBottom: 16, fontWeight: 600 }}>Active Jobs</div>
          <ul style={listStyle}>
            {detail?.active_jobs.map((job) => (
              <li key={job.job_id}>{job.job_type} · {job.status}</li>
            ))}
          </ul>
          <div style={{ margin: "20px 0 12px", fontWeight: 600 }}>Ready Quiz Packs</div>
          <ul style={listStyle}>
            {detail?.ready_packs.map((pack) => (
              <li key={pack.ready_pack_id}>{pack.title} · {pack.mode} · {pack.difficulty}</li>
            ))}
          </ul>
        </SectionCard>
      </div>


      <div style={twoColGridStyle}>
        <SectionCard title="Chat Workspace (Placeholder)">
          <ChatWorkspacePlaceholder />
        </SectionCard>

        <SectionCard title="Image & Audio Learning (Placeholders)">
          <div style={{ display: "grid", gap: 16 }}>
            <ImageLessonPlaceholder />
            <AudioPanelPlaceholder />
          </div>
        </SectionCard>
      </div>

      <div style={twoColGridStyle}>
        <SectionCard title="Achievements">
          <ul style={listStyle}>
            {detail?.achievements.map((achievement) => (
              <li key={achievement.achievement_id}>
                <strong>{achievement.title}</strong>
                <div style={{ opacity: 0.75 }}>{achievement.description}</div>
              </li>
            ))}
          </ul>
        </SectionCard>

        <SectionCard title="Placeholder Modules">
          <ul style={listStyle}>
            {detail?.roadmap_placeholders.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </SectionCard>
      </div>
    </div>
  );
}

const pageStyle: React.CSSProperties = {
  minHeight: "100vh",
  background: "#f8fafc",
  color: "#0f172a",
  padding: 24,
  fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif",
};

const headerStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  gap: 16,
  alignItems: "flex-start",
  marginBottom: 20,
  flexWrap: "wrap",
};

const toolbarStyle: React.CSSProperties = {
  display: "flex",
  gap: 10,
  alignItems: "center",
  flexWrap: "wrap",
};

const inputStyle: React.CSSProperties = {
  borderRadius: 12,
  border: "1px solid #cbd5e1",
  padding: "10px 12px",
  minWidth: 180,
};

const primaryButtonStyle: React.CSSProperties = {
  borderRadius: 12,
  border: "none",
  padding: "10px 14px",
  background: "#111827",
  color: "white",
  cursor: "pointer",
};

const secondaryButtonStyle: React.CSSProperties = {
  borderRadius: 12,
  border: "1px solid #cbd5e1",
  padding: "10px 14px",
  background: "white",
  color: "#111827",
  cursor: "pointer",
};

const statusStyle: React.CSSProperties = {
  marginBottom: 16,
  padding: 12,
  borderRadius: 14,
  background: "#e2e8f0",
};

const statsGridStyle: React.CSSProperties = {
  display: "grid",
  gap: 16,
  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
  marginBottom: 20,
};

const twoColGridStyle: React.CSSProperties = {
  display: "grid",
  gap: 16,
  gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
  marginBottom: 16,
};

const tableStyle: React.CSSProperties = {
  width: "100%",
  borderCollapse: "collapse",
};

const listStyle: React.CSSProperties = {
  paddingLeft: 18,
  margin: 0,
  display: "grid",
  gap: 10,
};
