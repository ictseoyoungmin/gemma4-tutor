import { useEffect, useMemo, useState } from "react";
import { fetchDashboardDetail, fetchWorkerStatus, queuePrebuildJob, startWorker, stopWorker } from "./api";
import { LearnerWorkspace } from "./components/LearnerWorkspace";
import { SectionCard } from "./components/SectionCard";
import { StatCard } from "./components/StatCard";
import type { DashboardDetail, WorkerStatusResponse } from "./types";

const defaultUserId = "demo-user";
type FrontendView = "dashboard" | "workspace";

export default function App() {
  const [userId, setUserId] = useState(defaultUserId);
  const [detail, setDetail] = useState<DashboardDetail | null>(null);
  const [workerStatus, setWorkerStatus] = useState<WorkerStatusResponse | null>(null);
  const [status, setStatus] = useState("Loading dashboard...");
  const [view, setView] = useState<FrontendView>("dashboard");

  useEffect(() => {
    void loadDashboard(userId);
    void loadWorkerStatus();
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

  async function loadWorkerStatus() {
    try {
      const current = await fetchWorkerStatus();
      setWorkerStatus(current);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Unknown error");
    }
  }

  async function handleQueueJob() {
    try {
      setStatus("Queueing background job...");
      await queuePrebuildJob(userId, "Daily commuting expressions");
      await loadDashboard(userId);
      await loadWorkerStatus();
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Unknown error");
    }
  }

  async function handleStartWorker() {
    try {
      setStatus("Starting worker...");
      const current = await startWorker(1);
      setWorkerStatus(current);
      setStatus("Worker running");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Unknown error");
    }
  }

  async function handleStopWorker() {
    try {
      setStatus("Stopping worker...");
      const current = await stopWorker();
      setWorkerStatus(current);
      setStatus("Worker stopped");
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
          <h1 style={{ margin: "8px 0 0", fontSize: 34 }}>Dashboard + Learner Workspace</h1>
          <p style={{ marginTop: 8, maxWidth: 820, lineHeight: 1.55, opacity: 0.8 }}>
            Keep the analytics dashboard for progress visibility while adding a dedicated learner workspace for
            tutoring, practice, and multimodal study. The two surfaces are intentionally separated.
          </p>
        </div>
        <div style={toolbarStyle}>
          <input value={userId} onChange={(e) => setUserId(e.target.value)} style={inputStyle} />
          <button onClick={() => void loadDashboard(userId)} style={primaryButtonStyle}>Refresh</button>
          <button onClick={() => void handleQueueJob()} style={secondaryButtonStyle}>Queue Prebuild Job</button>
        </div>
      </header>

      <div style={viewSwitchStyle}>
        <button
          onClick={() => setView("dashboard")}
          style={view === "dashboard" ? activeViewButtonStyle : inactiveViewButtonStyle}
        >
          Dashboard
        </button>
        <button
          onClick={() => setView("workspace")}
          style={view === "workspace" ? activeViewButtonStyle : inactiveViewButtonStyle}
        >
          Learner Workspace
        </button>
      </div>

      <div style={statusStyle}>{status}</div>

      {view === "workspace" ? <LearnerWorkspace userId={userId} /> : null}
      {view === "dashboard" ? (
        <>
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
        <SectionCard title="Worker Control">
          <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 14, flexWrap: "wrap" }}>
            <button onClick={() => void handleStartWorker()} style={primaryButtonStyle}>Start Worker</button>
            <button onClick={() => void handleStopWorker()} style={secondaryButtonStyle}>Stop Worker</button>
            <button onClick={() => void loadWorkerStatus()} style={secondaryButtonStyle}>Refresh Status</button>
          </div>
          <ul style={listStyle}>
            <li>State: {workerStatus?.state ?? "unknown"}</li>
            <li>PID: {workerStatus?.pid ?? "-"}</li>
            <li>Poll interval: {workerStatus?.poll_interval ?? "-"}</li>
            <li>Last exit code: {workerStatus?.last_exit_code ?? "-"}</li>
          </ul>
        </SectionCard>

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
        </>
      ) : null}
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

const viewSwitchStyle: React.CSSProperties = {
  display: "inline-flex",
  gap: 8,
  padding: 6,
  borderRadius: 16,
  background: "white",
  border: "1px solid #e2e8f0",
  marginBottom: 16,
};

const activeViewButtonStyle: React.CSSProperties = {
  borderRadius: 12,
  border: "none",
  padding: "10px 14px",
  background: "#111827",
  color: "white",
  cursor: "pointer",
  fontWeight: 600,
};

const inactiveViewButtonStyle: React.CSSProperties = {
  borderRadius: 12,
  border: "none",
  padding: "10px 14px",
  background: "transparent",
  color: "#334155",
  cursor: "pointer",
  fontWeight: 600,
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
