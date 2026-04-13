import type {
  ChatResponse,
  DashboardDetail,
  HarnessRunResponse,
  ProblemGenerationResponse,
  ProblemInventoryResponse,
  QuizSubmitResponse,
  ReadyPackLaunchResponse,
  ReadyQuizSummary,
  ToeicAnswerResponse,
  ToeicNextResponse,
  WorkerStatusResponse,
} from "./types";

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

export async function fetchWorkerStatus(): Promise<WorkerStatusResponse> {
  const response = await fetch(`${API_BASE}/v1/worker/status`);
  if (!response.ok) {
    throw new Error(`Failed to fetch worker status: ${response.status}`);
  }
  return response.json();
}

export async function startWorker(pollInterval = 1): Promise<WorkerStatusResponse> {
  const response = await fetch(`${API_BASE}/v1/worker/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ poll_interval: pollInterval }),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Failed to start worker: ${response.status} ${detail}`);
  }
  return response.json();
}

export async function stopWorker(): Promise<WorkerStatusResponse> {
  const response = await fetch(`${API_BASE}/v1/worker/stop`, {
    method: "POST",
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Failed to stop worker: ${response.status} ${detail}`);
  }
  return response.json();
}

export async function fetchReadyPacks(userId: string): Promise<ReadyQuizSummary[]> {
  const response = await fetch(`${API_BASE}/v1/packs/ready/${userId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch ready packs: ${response.status}`);
  }
  return response.json();
}

export async function fetchProblemInventory(
  userId: string,
  readyPackPage = 1,
  practiceItemPage = 1,
  pageSize = 5,
): Promise<ProblemInventoryResponse> {
  const params = new URLSearchParams({
    ready_pack_page: String(readyPackPage),
    practice_item_page: String(practiceItemPage),
    page_size: String(pageSize),
  });
  const response = await fetch(`${API_BASE}/v1/problems/${userId}?${params.toString()}`);
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Failed to fetch problem inventory: ${response.status} ${detail}`);
  }
  return response.json();
}

export async function queueProblemGeneration(
  userId: string,
  counts: Record<string, number>,
): Promise<ProblemGenerationResponse> {
  const response = await fetch(`${API_BASE}/v1/problems/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: userId,
      part1: counts.part1 ?? 0,
      part2: counts.part2 ?? 0,
      part3: counts.part3 ?? 0,
      part4: counts.part4 ?? 0,
      part5: counts.part5 ?? 0,
      part6: counts.part6 ?? 0,
      part7: counts.part7 ?? 0,
    }),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Failed to queue problem generation: ${response.status} ${detail}`);
  }
  return response.json();
}

export async function runHarness(mode: "asgi" | "http" = "asgi"): Promise<HarnessRunResponse> {
  const response = await fetch(`${API_BASE}/v1/harness/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode }),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Failed to run harness: ${response.status} ${detail}`);
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

export async function launchReadyPack(
  userId: string,
  readyPackId: string,
): Promise<ReadyPackLaunchResponse> {
  const response = await fetch(`${API_BASE}/v1/packs/ready/${readyPackId}/launch`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId }),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Failed to launch ready pack: ${response.status} ${detail}`);
  }
  return response.json();
}

export async function submitQuizAnswers(
  userId: string,
  quizId: string,
  answers: string[],
): Promise<QuizSubmitResponse> {
  const response = await fetch(`${API_BASE}/v1/quiz/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: userId,
      quiz_id: quizId,
      answers,
    }),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Failed to submit quiz: ${response.status} ${detail}`);
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
