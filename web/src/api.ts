import type {
  ChatResponse,
  DashboardDetail,
  DeleteResourceResponse,
  HealthResponse,
  HarnessRunResponse,
  ImageAnalysisResponse,
  ProblemGenerationResponse,
  ProblemInventoryResponse,
  PracticeItemDetail,
  QuizSubmitResponse,
  ReadyPackDetail,
  ReadyPackLaunchResponse,
  ReadyQuizSummary,
  ToeicAnswerResponse,
  ToeicNextResponse,
  WorkerStatusResponse,
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE}/v1/health`);
  if (!response.ok) {
    throw new Error(`Failed to fetch health: ${response.status}`);
  }
  return response.json();
}

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

export async function fetchReadyPackDetail(userId: string, readyPackId: string): Promise<ReadyPackDetail> {
  const response = await fetch(`${API_BASE}/v1/problems/${userId}/ready-packs/${readyPackId}`);
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Failed to fetch ready pack detail: ${response.status} ${detail}`);
  }
  return response.json();
}

export async function deleteReadyPack(
  userId: string,
  readyPackId: string,
): Promise<DeleteResourceResponse> {
  const response = await fetch(`${API_BASE}/v1/problems/${userId}/ready-packs/${readyPackId}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Failed to delete ready pack: ${response.status} ${detail}`);
  }
  return response.json();
}

export async function fetchPracticeItemDetail(
  userId: string,
  itemId: string,
): Promise<PracticeItemDetail> {
  const response = await fetch(`${API_BASE}/v1/problems/${userId}/practice-items/${itemId}`);
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Failed to fetch practice item detail: ${response.status} ${detail}`);
  }
  return response.json();
}

export async function deletePracticeItem(
  userId: string,
  itemId: string,
): Promise<DeleteResourceResponse> {
  const response = await fetch(`${API_BASE}/v1/problems/${userId}/practice-items/${itemId}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Failed to delete practice item: ${response.status} ${detail}`);
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
  modelName?: string | null,
  reasoningEnabled?: boolean | null,
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/v1/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: userId,
      session_id: sessionId ?? undefined,
      message,
      model_name: modelName ?? undefined,
      reasoning_enabled: reasoningEnabled ?? undefined,
    }),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Failed to send chat message: ${response.status} ${detail}`);
  }
  return response.json();
}

type ChatStreamEvent =
  | { type: "metadata"; session_id: string; backend: string; model_name: string }
  | {
      type: "metrics";
      first_chunk_ms?: number;
      elapsed_ms?: number;
      output_tokens?: number;
      reasoning_tokens?: number;
      total_tokens?: number;
      tokens_per_second?: number;
    }
  | { type: "reasoning_delta"; delta: string }
  | { type: "message_delta"; delta: string }
  | { type: "final"; response: ChatResponse }
  | { type: "error"; message: string };

function handleChatStreamEvent(
  line: string,
  options: {
    onMetadata?: (event: Extract<ChatStreamEvent, { type: "metadata" }>) => void;
    onMetrics?: (event: Extract<ChatStreamEvent, { type: "metrics" }>) => void;
    onReasoningDelta?: (delta: string) => void;
    onMessageDelta?: (delta: string) => void;
  },
): ChatResponse | null {
  const event = JSON.parse(line) as ChatStreamEvent;
  if (event.type === "metadata") {
    options.onMetadata?.(event);
    return null;
  }
  if (event.type === "metrics") {
    options.onMetrics?.(event);
    return null;
  }
  if (event.type === "reasoning_delta") {
    options.onReasoningDelta?.(event.delta);
    return null;
  }
  if (event.type === "message_delta") {
    options.onMessageDelta?.(event.delta);
    return null;
  }
  if (event.type === "error") {
    throw new Error(event.message);
  }
  if (event.type === "final") {
    return event.response;
  }
  return null;
}

function buildIncompleteStreamResponse(args: {
  sessionId?: string | null;
  modelName?: string | null;
  message: string;
  reasoning: string;
  firstChunkMs?: number | null;
}): ChatResponse {
  return {
    session_id: args.sessionId || `incomplete-${Date.now()}`,
    run_id: `stream-incomplete-${Date.now()}`,
    output: {
      message:
        args.message.trim() ||
        "응답을 이어서 정리하는 중이에요.",
      detected_intent: "chat",
      memory_to_store: [],
      suggested_next_actions: [],
    },
    reasoning: args.reasoning || null,
    diagnostics: {
      streaming: true,
      incomplete_stream: true,
      model_name: args.modelName ?? "unknown",
      first_chunk_ms: args.firstChunkMs ?? undefined,
    },
    usage: {},
  };
}

function estimateTokenCount(text: string): number {
  const trimmed = text.trim();
  if (!trimmed) return 0;
  return Math.max(1, Math.round(trimmed.length / 3.6));
}

export async function streamChatMessage(
  userId: string,
  message: string,
  options: {
    sessionId?: string | null;
    modelName?: string | null;
    reasoningEnabled?: boolean | null;
    signal?: AbortSignal;
    onMetadata?: (event: Extract<ChatStreamEvent, { type: "metadata" }>) => void;
    onMetrics?: (event: Extract<ChatStreamEvent, { type: "metrics" }>) => void;
    onReasoningDelta?: (delta: string) => void;
    onMessageDelta?: (delta: string) => void;
  } = {},
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/v1/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: userId,
      session_id: options.sessionId ?? undefined,
      message,
      model_name: options.modelName ?? undefined,
      reasoning_enabled: options.reasoningEnabled ?? undefined,
    }),
    signal: options.signal,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Failed to stream chat message: ${response.status} ${detail}`);
  }
  if (!response.body) {
    throw new Error("Streaming response body was not available.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let finalResponse: ChatResponse | null = null;
  let streamSessionId: string | null = options.sessionId ?? null;
  let streamModelName: string | null = options.modelName ?? null;
  let firstChunkMs: number | null = null;
  let streamedMessage = "";
  let streamedReasoning = "";
  const streamStartedAt = performance.now();

  function emitLiveMetrics() {
    const elapsedMs = Math.max(1, performance.now() - streamStartedAt);
    const outputTokens = estimateTokenCount(streamedMessage);
    const reasoningTokens = estimateTokenCount(streamedReasoning);
    const totalTokens = outputTokens + reasoningTokens;
    options.onMetrics?.({
      type: "metrics",
      first_chunk_ms: firstChunkMs ?? undefined,
      elapsed_ms: elapsedMs,
      output_tokens: outputTokens,
      reasoning_tokens: reasoningTokens,
      total_tokens: totalTokens,
      tokens_per_second: totalTokens > 0 ? totalTokens / (elapsedMs / 1000) : 0,
    });
  }

  const streamOptions = {
    ...options,
    onMetadata: (event: Extract<ChatStreamEvent, { type: "metadata" }>) => {
      streamSessionId = event.session_id;
      streamModelName = event.model_name;
      options.onMetadata?.(event);
    },
    onMetrics: (event: Extract<ChatStreamEvent, { type: "metrics" }>) => {
      if (event.first_chunk_ms !== undefined) {
        firstChunkMs = event.first_chunk_ms;
      }
      options.onMetrics?.(event);
    },
    onReasoningDelta: (delta: string) => {
      if (firstChunkMs === null) {
        firstChunkMs = performance.now() - streamStartedAt;
      }
      streamedReasoning += delta;
      options.onReasoningDelta?.(delta);
      emitLiveMetrics();
    },
    onMessageDelta: (delta: string) => {
      if (firstChunkMs === null) {
        firstChunkMs = performance.now() - streamStartedAt;
      }
      streamedMessage += delta;
      options.onMessageDelta?.(delta);
      emitLiveMetrics();
    },
  };

  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done });

    let newlineIndex = buffer.indexOf("\n");
    while (newlineIndex >= 0) {
      const line = buffer.slice(0, newlineIndex).trim();
      buffer = buffer.slice(newlineIndex + 1);
      if (line) {
        finalResponse = handleChatStreamEvent(line, streamOptions) ?? finalResponse;
      }
      newlineIndex = buffer.indexOf("\n");
    }

    if (done) break;
  }

  const trailingLine = buffer.trim();
  if (trailingLine) {
    finalResponse = handleChatStreamEvent(trailingLine, streamOptions) ?? finalResponse;
  }

  if (!finalResponse) {
    if (!streamedMessage.trim()) {
      try {
        return await sendChatMessage(
          userId,
          message,
          streamSessionId,
          streamModelName,
          options.reasoningEnabled,
        );
      } catch {
        // Fall through to a non-error fallback so the learner-facing chat does not flip to request.error.
      }
    }
    return buildIncompleteStreamResponse({
      sessionId: streamSessionId,
      modelName: streamModelName,
      message: streamedMessage,
      reasoning: streamedReasoning,
      firstChunkMs,
    });
  }
  return finalResponse;
}

export async function analyzeChatImage(
  userId: string,
  file: File,
  prompt?: string | null,
  modelName?: string | null,
): Promise<ImageAnalysisResponse> {
  const formData = new FormData();
  formData.append("user_id", userId);
  formData.append("prompt", prompt?.trim() || "Analyze this image and turn it into English learning material.");
  formData.append("file", file);
  if (modelName) {
    formData.append("model_name", modelName);
  }

  const response = await fetch(`${API_BASE}/v1/image/analyze`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Failed to analyze image: ${response.status} ${detail}`);
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
