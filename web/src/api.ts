import type { ChatResponse, DashboardDetail, ToeicAnswerResponse, ToeicNextResponse } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

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

export async function sendChatMessage(
  userId: string,
  message: string,
  sessionId?: string | null,
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/v1/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: userId,
      session_id: sessionId ?? undefined,
      message,
    }),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Failed to send chat message: ${response.status} ${detail}`);
  }
  return response.json();
}

export async function fetchNextToeicItem(userId: string): Promise<ToeicNextResponse> {
  const response = await fetch(`${API_BASE}/v1/quiz/next`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: userId,
      part_type: "part5",
    }),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Failed to fetch TOEIC item: ${response.status} ${detail}`);
  }
  return response.json();
}

export async function submitToeicAnswer(
  userId: string,
  itemId: string,
  selectedOption: string,
  responseTimeMs: number,
): Promise<ToeicAnswerResponse> {
  const response = await fetch(`${API_BASE}/v1/quiz/answer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: userId,
      item_id: itemId,
      selected_option: selectedOption,
      response_time_ms: responseTimeMs,
    }),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Failed to submit TOEIC answer: ${response.status} ${detail}`);
  }
  return response.json();
}
