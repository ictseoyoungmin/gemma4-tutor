import type { DashboardDetail } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

export async function fetchDashboardDetail(userId: string): Promise<DashboardDetail> {
  const response = await fetch(`${API_BASE}/v1/dashboard/${userId}/detail`);
  if (!response.ok) {
    throw new Error(`Failed to fetch dashboard: ${response.status}`);
  }
  return response.json();
}

export async function queuePrebuildJob(userId: string, topic: string) {
  const response = await fetch(`${API_BASE}/v1/jobs/queue`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: userId,
      job_type: "prebuild_quiz",
      payload: { topic, mode: "grammar", difficulty: "medium" },
    }),
  });
  if (!response.ok) {
    throw new Error(`Failed to queue job: ${response.status}`);
  }
  return response.json();
}
