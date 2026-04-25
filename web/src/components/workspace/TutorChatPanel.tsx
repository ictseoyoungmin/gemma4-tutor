import { useEffect, useMemo, useRef, useState, type ChangeEvent } from "react";
import { analyzeChatImage, fetchHealth, streamChatMessage } from "../../api";
import type { ChatResponse, HealthResponse } from "../../types";
import { starterPrompts } from "./workspaceData";

type ChatTurn = {
  id: string;
  role: "user" | "assistant";
  message: string;
  reasoning?: string;
  diagnostics?: string;
  streamMetrics?: string;
  meta?: string;
  suggestions?: string[];
  isStreaming?: boolean;
};

type ChatAttachment = {
  id: string;
  file: File;
  previewUrl: string;
};

const starterDrafts: Record<string, string> = {
  "TOEIC Part 5": "TOEIC Part 5 팁 하나 짧게 알려줘.",
  "문장 교정": "이 문장 교정해줘: I am agree with the plan.",
  워밍업: "가벼운 영어 워밍업 질문 하나 해줘.",
  어휘: "비즈니스 영어 어휘 3개만 알려줘.",
};

const introTurns: ChatTurn[] = [
  {
    id: "intro-1",
    role: "assistant",
    message: "안녕하세요! TOEIC Part 5, 문장 교정, 워밍업 중 어떤 것부터 시작할까요?",
    meta: "intent: chat",
    suggestions: ["Part 5 풀기", "문장 교정"],
  },
];

const initialTurns: ChatTurn[] = [
  ...introTurns,
  {
    id: "demo-user-1",
    role: "user",
    message: "TOEIC Part 5 팁 하나 짧게 알려줘.",
  },
  {
    id: "demo-ai-2",
    role: "assistant",
    message:
      "품사부터 확인하세요.\n빈칸 앞뒤 단어로 명사·동사·형용사·부사 중 어느 품사가 필요한지 먼저 파악하면 오답을 빠르게 제거할 수 있어요.",
    meta: "intent: chat · 메모리 저장됨",
    suggestions: ["예제 문제", "다음 팁"],
  },
];

const chatModelOptions = [
  { value: "gemini-3-flash-preview", label: "Gemini 3 Flash (Preview)", backend: "google" },
  { value: "gemini-3.1-flash-lite-preview", label: "Gemini 3.1 Lite (Preview)", backend: "google" },
  { value: "gemini-2.5-flash", label: "Gemini 2.5 Flash", backend: "google" },
  { value: "gemma-4-26b-a4b-it", label: "Gemma 4 26B", backend: "google" },
  { value: "gemma-4-E2B-it-Q4_K_M.gguf", label: "Gemma 4 E2B (llama.cpp)", backend: "llama_cpp" },
] as const;

const AUTO_SCROLL_THRESHOLD_PX = 48;
type ChatModelOption = {
  value: string;
  label: string;
  backend: "google" | "llama_cpp";
};

function normalizeEchoCandidate(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/\s+/g, " ")
    .replace(/[.!?。！？]+$/g, "");
}

function isPromptEcho(candidate: string, submittedMessage: string): boolean {
  const normalizedCandidate = normalizeEchoCandidate(candidate);
  const normalizedSubmittedMessage = normalizeEchoCandidate(submittedMessage);
  return (
    normalizedCandidate.length > 0 &&
    normalizedCandidate === normalizedSubmittedMessage
  );
}

function buildEchoFallbackMessage(submittedMessage: string): string {
  if (/toeic|part\s*5|품사|문법/i.test(submittedMessage)) {
    return "Part 5는 빈칸 앞뒤를 먼저 보세요.\n선택지를 뜻으로 읽기 전에 명사·동사·형용사·부사 중 어떤 품사가 필요한지부터 걸러내면 속도가 빨라져요.";
  }
  if (/교정|correct|문장/i.test(submittedMessage)) {
    return "문장을 보내주면 자연스러운 표현으로 고치고, 왜 그렇게 바꾸는지 한 줄로 설명해드릴게요.";
  }
  return "질문을 그대로 반복하지 않고 다시 정리해볼게요.\n원하는 목표를 한 가지 더 구체적으로 알려주면 짧고 바로 쓸 수 있는 답으로 도와드릴게요.";
}

function formatStreamMetrics(metrics: {
  elapsed_ms?: number;
  output_tokens?: number;
  reasoning_tokens?: number;
  total_tokens?: number;
  tokens_per_second?: number;
}): string {
  const totalTokens = Math.round(metrics.total_tokens ?? 0);
  const elapsedSeconds = (metrics.elapsed_ms ?? 0) / 1000;
  const tokensPerSecond = metrics.tokens_per_second ?? 0;
  const phase =
    (metrics.reasoning_tokens ?? 0) > 0 && (metrics.output_tokens ?? 0) === 0
      ? "Reading"
      : "Generation";
  return `${phase} · ${totalTokens} tokens · ${elapsedSeconds.toFixed(1)}s · ${tokensPerSecond.toFixed(2)} tokens/s`;
}

function formatElapsedSeconds(milliseconds: number): string {
  return `${(milliseconds / 1000).toFixed(1)}s`;
}

function resolveRuntimeDefaultModel(runtime: HealthResponse | null): string {
  if (!runtime) return "gemini-3-flash-preview";
  return runtime.model_name;
}

export function TutorChatPanel({ userId }: { userId: string }) {
  const [draft, setDraft] = useState(starterDrafts["TOEIC Part 5"]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [turns, setTurns] = useState<ChatTurn[]>(initialTurns);
  const [status, setStatus] = useState("연결됨");
  const [runtime, setRuntime] = useState<HealthResponse | null>(null);
  const [isSending, setIsSending] = useState(false);
  const [modelPickerOpen, setModelPickerOpen] = useState(false);
  const [attachments, setAttachments] = useState<ChatAttachment[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>("gemini-3-flash-preview");
  const [reasoningEnabled, setReasoningEnabled] = useState(false);
  const [openReasoningTurnIds, setOpenReasoningTurnIds] = useState<Record<string, boolean>>({});
  const transcriptRef = useRef<HTMLDivElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const shouldStickToBottomRef = useRef(true);
  const activeStreamControllerRef = useRef<AbortController | null>(null);
  const didInitializeRuntimeModelRef = useRef(false);
  const primaryAttachment = attachments[0] ?? null;
  const runtimeBackend = runtime?.backend ?? "google";
  const availableModelOptions = useMemo<ChatModelOption[]>(() => {
    const options: ChatModelOption[] = [...chatModelOptions];
    if (
      runtime?.model_name &&
      !options.some((option) => option.value === runtime.model_name)
    ) {
      options.push({
        value: runtime.model_name,
        label:
          runtime.backend === "llama_cpp"
            ? `Local Model · ${runtime.model_name}`
            : `Hosted Model · ${runtime.model_name}`,
        backend: runtime.backend === "llama_cpp" ? "llama_cpp" : "google",
      });
    }
    return options;
  }, [runtime?.backend, runtime?.model_name]);

  const selectedModelOption = useMemo(
    () => availableModelOptions.find((option) => option.value === selectedModel) ?? null,
    [availableModelOptions, selectedModel],
  );

  const selectedModelBackend = selectedModelOption?.backend ?? runtimeBackend;
  const selectedModelLabel = useMemo(
    () => selectedModelOption?.label ?? selectedModel,
    [selectedModelOption, selectedModel],
  );

  const helperText = useMemo(() => {
    if (isSending) return "튜터가 다음 학습 흐름을 준비하고 있어요.";
    if (runtime && runtime.backend !== selectedModelBackend) {
      return `현재 런타임은 ${runtime.backend} · ${runtime.model_name} 이고, 선택 모델은 ${selectedModelBackend} · ${selectedModelLabel} 입니다. 새 세션으로 분리해 전송합니다.`;
    }
    if (sessionId) {
      return `현재 세션이 이어지고 있어요. reasoning ${reasoningEnabled ? "on" : "off"} · ${selectedModelLabel}`;
    }
    if (primaryAttachment) return `이미지 첨부됨 · ${primaryAttachment.file.name}`;
    return runtimeBackend === "llama_cpp"
      ? `로컬 llama.cpp 런타임이 연결되어 있어요. reasoning ${reasoningEnabled ? "on" : "off"}`
      : "Hosted Google 기본 런타임이 연결되어 있어요. picker에서 local llama.cpp 모델도 선택할 수 있어요.";
  }, [isSending, primaryAttachment, reasoningEnabled, runtime, runtimeBackend, selectedModelBackend, selectedModelLabel, sessionId]);

  const runtimeBadgeLabel = useMemo(() => {
    if (!runtime) return "Runtime 확인 중";
    if (runtime.backend === "llama_cpp") return `Local · ${runtime.model_name}`;
    if (runtime.backend === "google") return `Hosted · ${runtime.model_name}`;
    return `${runtime.backend} · ${runtime.model_name}`;
  }, [runtime]);

  useEffect(() => {
    let cancelled = false;

    async function loadRuntime() {
      try {
        const nextRuntime = await fetchHealth();
        if (cancelled) return;
        const runtimeDefaultModel = resolveRuntimeDefaultModel(nextRuntime);
        setRuntime(nextRuntime);
        setSelectedModel((current) => {
          if (didInitializeRuntimeModelRef.current) {
            return current;
          }
          didInitializeRuntimeModelRef.current = true;
          return runtimeDefaultModel;
        });
        const runtimeDefaultLabel =
          availableModelOptions.find((option) => option.value === runtimeDefaultModel)?.label
          ?? runtimeDefaultModel;
        setStatus(`연결됨 · ${runtimeDefaultLabel}`);
      } catch (error) {
        if (cancelled) return;
        setStatus(error instanceof Error ? error.message : "Runtime 상태를 확인하지 못했습니다.");
      }
    }

    void loadRuntime();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!runtime) return;
    setSelectedModel((current) => {
      const stillAvailable = availableModelOptions.some((option) => option.value === current);
      return stillAvailable ? current : resolveRuntimeDefaultModel(runtime);
    });
  }, [availableModelOptions, runtime]);

  useEffect(() => {
    const transcript = transcriptRef.current;
    if (!transcript) return;
    if (!shouldStickToBottomRef.current) return;
    transcript.scrollTop = transcript.scrollHeight;
  }, [isSending, turns]);

  useEffect(() => {
    const attachmentUrls = attachments.map((attachment) => attachment.previewUrl);
    return () => {
      attachmentUrls.forEach((previewUrl) => URL.revokeObjectURL(previewUrl));
    };
  }, [attachments]);

  useEffect(() => {
    return () => {
      activeStreamControllerRef.current?.abort();
    };
  }, []);

  function updateAutoScrollState() {
    const transcript = transcriptRef.current;
    if (!transcript) return;
    const distanceFromBottom =
      transcript.scrollHeight - transcript.scrollTop - transcript.clientHeight;
    shouldStickToBottomRef.current = distanceFromBottom <= AUTO_SCROLL_THRESHOLD_PX;
  }

  function buildImageLearningMessage(summary: {
    scene_summary: string;
    vocabulary: string[];
    suggested_question_types: string[];
    generated_prompt_seed: string;
  }) {
    return [
      `Scene: ${summary.scene_summary}`,
      summary.vocabulary.length ? `Vocabulary: ${summary.vocabulary.join(", ")}` : "",
      summary.suggested_question_types.length
        ? `Try next: ${summary.suggested_question_types.join(", ")}`
        : "",
      `Prompt seed: ${summary.generated_prompt_seed}`,
    ]
      .filter(Boolean)
      .join("\n");
  }

  function toggleReasoning(turnId: string) {
    setOpenReasoningTurnIds((current) => ({
      ...current,
      [turnId]: !current[turnId],
    }));
  }

  function resetConversationForModelSwitch(nextModelLabel: string, nextModelBackend: string) {
    activeStreamControllerRef.current?.abort();
    activeStreamControllerRef.current = null;
    setIsSending(false);
    setSessionId(null);
    setAttachments((current) => {
      current.forEach((attachment) => URL.revokeObjectURL(attachment.previewUrl));
      return [];
    });
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
    setTurns([
      ...introTurns,
      {
        id: `session-reset-${Date.now()}`,
        role: "assistant",
        message: `모델이 ${nextModelLabel}로 바뀌어서 새 세션으로 다시 시작할게요.`,
        meta: `session reset · ${nextModelBackend}`,
      },
    ]);
    setStatus(`새 세션 준비됨 · ${nextModelLabel}`);
  }

  async function handleSubmit(message: string) {
    const trimmed = message.trim();
    if ((!trimmed && attachments.length === 0) || isSending) return;
    const currentAttachments = attachments;
    const currentAttachment = currentAttachments[0] ?? null;
    const pendingAssistantId = `assistant-${Date.now()}`;
    const streamStartedAt = performance.now();
    let liveMetricSnapshot = {
      elapsed_ms: 0,
      output_tokens: 0,
      reasoning_tokens: 0,
      total_tokens: 0,
      tokens_per_second: 0,
    };
    let streamMetricsTimer: number | null = null;
    shouldStickToBottomRef.current = true;
    if (reasoningEnabled) {
      setOpenReasoningTurnIds((current) => ({
        ...current,
        [pendingAssistantId]: true,
      }));
    }

    setTurns((current) => [
      ...current,
      {
        id: `user-${Date.now()}`,
        role: "user",
        message: currentAttachment
          ? `${trimmed || "이미지 학습 요청"}\n[이미지 첨부] ${currentAttachment.file.name}`
          : trimmed,
      },
      ...(currentAttachment
        ? []
        : [
            {
              id: pendingAssistantId,
              role: "assistant" as const,
              message: "",
              reasoning: "",
              streamMetrics: formatStreamMetrics(liveMetricSnapshot),
              meta: `${selectedModel}`,
              isStreaming: true,
            },
          ]),
    ]);
    setDraft("");
    setAttachments([]);
    currentAttachments.forEach((attachment) => URL.revokeObjectURL(attachment.previewUrl));
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
    setIsSending(true);
    setStatus(`메시지 전송 중... · ${selectedModel}`);

    try {
      if (currentAttachment) {
        const response = await analyzeChatImage(userId, currentAttachment.file, trimmed, selectedModel);
        setTurns((current) => [
          ...current,
          {
            id: `image-${Date.now()}`,
            role: "assistant",
            message: buildImageLearningMessage(response),
            meta: "intent: image_learning",
            suggestions: response.suggested_question_types.slice(0, 3),
          },
        ]);
        setStatus(`이미지 학습 응답 완료 · ${selectedModel}`);
      } else {
        activeStreamControllerRef.current?.abort();
        const controller = new AbortController();
        activeStreamControllerRef.current = controller;
        streamMetricsTimer = window.setInterval(() => {
          liveMetricSnapshot = {
            ...liveMetricSnapshot,
            elapsed_ms: performance.now() - streamStartedAt,
          };
          setTurns((current) =>
            current.map((turn) =>
              turn.id === pendingAssistantId
                ? { ...turn, streamMetrics: formatStreamMetrics(liveMetricSnapshot) }
                : turn,
            ),
          );
        }, 500);
        const response = await streamChatMessage(userId, trimmed, {
          sessionId,
          modelName: selectedModel,
          reasoningEnabled,
          signal: controller.signal,
          onMetadata: (event) => {
            setSessionId(event.session_id);
            setStatus(`스트림 연결됨 · ${event.model_name}`);
          },
          onMetrics: (event) => {
            if (event.elapsed_ms !== undefined || event.total_tokens !== undefined) {
              liveMetricSnapshot = {
                elapsed_ms: event.elapsed_ms ?? performance.now() - streamStartedAt,
                output_tokens: event.output_tokens ?? liveMetricSnapshot.output_tokens,
                reasoning_tokens: event.reasoning_tokens ?? liveMetricSnapshot.reasoning_tokens,
                total_tokens: event.total_tokens ?? liveMetricSnapshot.total_tokens,
                tokens_per_second:
                  event.tokens_per_second ?? liveMetricSnapshot.tokens_per_second,
              };
              const metricsText = formatStreamMetrics(liveMetricSnapshot);
              setTurns((current) =>
                current.map((turn) =>
                  turn.id === pendingAssistantId
                    ? { ...turn, streamMetrics: metricsText }
                    : turn,
                ),
              );
              return;
            }
            if (event.first_chunk_ms !== undefined) {
              setStatus(`첫 토큰 수신 · ${formatElapsedSeconds(event.first_chunk_ms)} · ${selectedModel}`);
            }
          },
          onReasoningDelta: (delta) => {
            if (!delta) return;
            if (reasoningEnabled) {
              setOpenReasoningTurnIds((current) => {
                if (pendingAssistantId in current) return current;
                return { ...current, [pendingAssistantId]: true };
              });
            }
            setTurns((current) =>
              current.map((turn) =>
                turn.id === pendingAssistantId
                  ? { ...turn, reasoning: `${turn.reasoning ?? ""}${delta}` }
                  : turn,
              ),
            );
          },
          onMessageDelta: (delta) => {
            if (!delta) return;
            setTurns((current) =>
              current.map((turn) =>
                turn.id === pendingAssistantId
                  ? { ...turn, message: `${turn.message}${delta}` }
                  : turn,
              ),
            );
          },
        });

        setSessionId(response.session_id);
        setOpenReasoningTurnIds((current) => {
          if (!(pendingAssistantId in current)) return current;
          return {
            ...current,
            [response.run_id]: current[pendingAssistantId],
          };
        });
        setTurns((current) =>
          current.map((turn) =>
            turn.id === pendingAssistantId
              ? buildCompletedAssistantTurn(turn, response, trimmed)
              : turn,
          ),
        );
        activeStreamControllerRef.current = null;

        const totalElapsedMs = Number(response.diagnostics.total_elapsed_ms ?? 0);
        const responseReasoningEnabled = response.diagnostics.reasoning_enabled === true;
        setStatus(
          totalElapsedMs > 0
            ? `응답 수신 완료 · reasoning ${responseReasoningEnabled ? "on" : "off"} · ${formatElapsedSeconds(totalElapsedMs)}`
            : `응답 수신 완료 · reasoning ${responseReasoningEnabled ? "on" : "off"}`,
        );
      }
    } catch (error) {
      activeStreamControllerRef.current = null;
      if (error instanceof DOMException && error.name === "AbortError") {
        setTurns((current) => current.filter((turn) => turn.id !== pendingAssistantId));
        setStatus(`요청 취소됨 · ${selectedModelLabel}`);
        return;
      }
      const errorMessage = error instanceof Error ? error.message : "Unknown error";
      if (currentAttachment) {
        setTurns((current) => [
          ...current,
          {
            id: `error-${Date.now()}`,
            role: "assistant",
            message: `요청 처리 중 문제가 생겼어요. ${errorMessage}`,
            meta: "request.error",
          },
        ]);
      } else {
        setTurns((current) =>
          current.map((turn) =>
            turn.id === pendingAssistantId
              ? {
                  ...turn,
                  message: `요청 처리 중 문제가 생겼어요. ${errorMessage}`,
                  meta: "request.error",
                  isStreaming: false,
                }
              : turn,
          ),
        );
      }
      setStatus("연결 문제");
    } finally {
      if (streamMetricsTimer !== null) {
        window.clearInterval(streamMetricsTimer);
      }
      setIsSending(false);
    }
  }

  function buildCompletedAssistantTurn(
    turn: ChatTurn,
    response: ChatResponse,
    submittedMessage: string,
  ): ChatTurn {
    const firstChunkMs = Number(response.diagnostics.first_chunk_ms ?? 0);
    const totalElapsedMs = Number(response.diagnostics.total_elapsed_ms ?? 0);
    const diagnostics = [
      firstChunkMs > 0 ? `first ${formatElapsedSeconds(firstChunkMs)}` : "",
      totalElapsedMs > 0 ? `total ${formatElapsedSeconds(totalElapsedMs)}` : "",
    ]
      .filter(Boolean)
      .join(" · ");
    const finalMessage = response.output.message.trim();
    const streamedMessage = turn.message.trim();
    const normalizedFinalMessage = normalizeEchoCandidate(finalMessage);
    const finalLooksLikePromptEcho = isPromptEcho(finalMessage, submittedMessage);
    const streamedLooksLikePromptEcho = isPromptEcho(streamedMessage, submittedMessage);
    const looksLikeReasoningLeak =
      normalizedFinalMessage.startsWith("thinking process") ||
      normalizedFinalMessage.startsWith("1. **analyze the request:**");
    const shouldPreferStreamedMessage =
      streamedMessage.length > 0 && (
        finalMessage.length === 0 ||
        finalLooksLikePromptEcho ||
        looksLikeReasoningLeak
      ) && !streamedLooksLikePromptEcho;
    const displayMessage =
      shouldPreferStreamedMessage
        ? turn.message
        : finalLooksLikePromptEcho || streamedLooksLikePromptEcho
          ? buildEchoFallbackMessage(submittedMessage)
          : response.output.message;

    return {
      ...turn,
      id: response.run_id,
      message: displayMessage,
      reasoning: response.reasoning ?? turn.reasoning ?? "",
      diagnostics,
      streamMetrics: undefined,
      meta: `intent: ${response.output.detected_intent}`,
      suggestions: response.output.suggested_next_actions,
      isStreaming: false,
    };
  }

  function handlePickImage() {
    fileInputRef.current?.click();
  }

  function handleImageChange(event: ChangeEvent<HTMLInputElement>) {
    const nextFile = event.target.files?.[0];
    if (!nextFile) return;
    if (!nextFile.type.startsWith("image/")) {
      setStatus("이미지 파일만 업로드할 수 있어요.");
      return;
    }
    setAttachments((current) => {
      current.forEach((attachment) => URL.revokeObjectURL(attachment.previewUrl));
      return [
        {
          id: `${nextFile.name}-${nextFile.size}-${Date.now()}`,
          file: nextFile,
          previewUrl: URL.createObjectURL(nextFile),
        },
      ];
    });
    setStatus(`이미지 첨부 준비됨 · ${nextFile.name}`);
  }

  return (
    <div className="workspace-chat">
      <div className="workspace-chat__top">
        <div className="workspace-chat__eyebrow">AI 튜터</div>
        <div className="workspace-chat__title">
          오늘 무엇을
          <br />
          연습할까요?
        </div>
        <div className="workspace-chat__chips">
          {starterPrompts.map((prompt, index) => (
            <button
              key={prompt}
              type="button"
              className={`workspace-chat__chip${index === 0 ? " is-on" : ""}`}
              onClick={() => setDraft(starterDrafts[prompt])}
            >
              {prompt}
            </button>
          ))}
        </div>
        {/*중복 표기로 사용할 필요*/}
        {/* <div className="workspace-chat__runtime-row">
          <div className={`workspace-chat__runtime-badge is-${runtimeBackend}`}>
            {runtimeBadgeLabel}
          </div>
          <div className="workspace-chat__runtime-note">
            {runtimeBackend === "llama_cpp"
              ? "UI is locked to the served local model."
              : "Choose a hosted Gemini model for this session."}
          </div>
        </div>*/}
      </div>

      <div
        ref={transcriptRef}
        className="workspace-chat__transcript"
        onScroll={updateAutoScrollState}
      >
        {turns.map((turn) => (
          <div key={turn.id} className={`workspace-bubble-row is-${turn.role}`}>
            {turn.role === "assistant" ? (
              <div className="workspace-ai-avatar">
                <div className="workspace-ai-avatar__dot" />
              </div>
            ) : null}

            <div className={`workspace-bubble is-${turn.role}`}>
              {turn.role === "assistant" && turn.streamMetrics ? (
                <div className="workspace-bubble__stream-meter">
                  {turn.streamMetrics}
                </div>
              ) : null}

              <div className="workspace-bubble__text">
                {turn.message ? (
                  turn.message.split("\n").map((line, index) => (
                    <span key={`${turn.id}-${index}`}>
                      {line}
                      {index < turn.message.split("\n").length - 1 ? <br /> : null}
                    </span>
                  ))
                ) : turn.isStreaming ? (
                  <span className="workspace-bubble__streaming-text">Generating...</span>
                ) : null}
              </div>

              {reasoningEnabled && turn.role === "assistant" && turn.reasoning?.trim() ? (
                <div className="workspace-bubble__reasoning">
                  <button
                    type="button"
                    className="workspace-bubble__reasoning-toggle"
                    onClick={() => toggleReasoning(turn.id)}
                    aria-expanded={Boolean(openReasoningTurnIds[turn.id])}
                    title="Show or hide reasoning for this response"
                  >
                    <span className="workspace-bubble__reasoning-label">Reasoning</span>
                    <span className="workspace-bubble__reasoning-state">
                      {openReasoningTurnIds[turn.id] ? "Hide" : "Show"}
                    </span>
                  </button>
                  {openReasoningTurnIds[turn.id] ? (
                    <div className="workspace-bubble__reasoning-text">
                      {turn.reasoning.trim()}
                    </div>
                  ) : null}
                </div>
              ) : null}

              {turn.meta ? (
                <div className="workspace-bubble__meta">
                  <div className="workspace-bubble__meta-dot" />
                  {turn.meta}
                </div>
              ) : null}

              {turn.diagnostics ? (
                <div className="workspace-bubble__meta">
                  <div className="workspace-bubble__meta-dot" />
                  {turn.diagnostics}
                </div>
              ) : null}

              {turn.suggestions?.length ? (
                <div className="workspace-suggestion-row">
                  {turn.suggestions.map((suggestion) => (
                    <button
                      key={suggestion}
                      type="button"
                      className="workspace-suggestion"
                      onClick={() => void handleSubmit(suggestion)}
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
          </div>
        ))}

        {isSending && !turns.some((turn) => turn.isStreaming) ? (
          <div className="workspace-bubble-row is-assistant">
            <div className="workspace-ai-avatar">
              <div className="workspace-ai-avatar__dot" />
            </div>
            <div className="workspace-bubble is-assistant">
              <div className="workspace-typing">
                <span />
                <span />
                <span />
              </div>
            </div>
          </div>
        ) : null}
      </div>

      <div className="workspace-chat__statusbar">
        <div className="workspace-status-pill">
          <span className="workspace-status-pill__pulse" />
          {status}
        </div>
        <div className="workspace-session-id">sess:{sessionId?.slice(0, 6) ?? "a3f9e2"}</div>
      </div>

      <form
        className="workspace-chat__composer"
        onSubmit={(event) => {
          event.preventDefault();
          void handleSubmit(draft);
        }}
      >
        <div className="workspace-chat__composer-wrap">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            className="workspace-chat__file-input"
            onChange={handleImageChange}
          />
          {attachments.length ? (
            <div className="workspace-chat__attachment-row">
              {attachments.map((attachment) => (
                <div key={attachment.id} className="workspace-chat__attachment-chip">
                  <div className="workspace-chat__attachment-thumb">
                    <img
                      src={attachment.previewUrl}
                      alt={attachment.file.name}
                      className="workspace-chat__attachment-image"
                    />
                  </div>
                  <span className="workspace-chat__attachment-name">{attachment.file.name}</span>
                  <button
                    type="button"
                    className="workspace-chat__attachment-remove"
                    onClick={() => {
                      setAttachments((current) => {
                        const next = current.filter((item) => item.id !== attachment.id);
                        const removed = current.find((item) => item.id === attachment.id);
                        if (removed) {
                          URL.revokeObjectURL(removed.previewUrl);
                        }
                        if (next.length === 0 && fileInputRef.current) {
                          fileInputRef.current.value = "";
                        }
                        return next;
                      });
                    }}
                    aria-label="첨부 제거"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          ) : null}
          <textarea
            className="workspace-chat__textarea"
            rows={2}
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder="메시지를 입력하거나 예문에 답해보세요…"
          />

          <div className="workspace-chat__composer-footer">
            <span className="workspace-chat__hint">{helperText}</span>
            <div className="workspace-chat__actions">
              <button
                type="button"
                className={`workspace-chat__ghost${reasoningEnabled ? " is-active" : ""}`}
                aria-label={reasoningEnabled ? "Reasoning 끄기" : "Reasoning 켜기"}
                title={reasoningEnabled ? "Reasoning on" : "Reasoning off"}
                aria-pressed={reasoningEnabled}
                onClick={() => {
                  setReasoningEnabled((current) => {
                    const next = !current;
                    setStatus(`Reasoning ${next ? "켜짐" : "꺼짐"} · 다음 메시지부터 적용`);
                    return next;
                  });
                }}
              >
                <svg className="icon-sm" viewBox="0 0 24 24">
                  <path d="M9 3.5a4 4 0 00-4 4v1.2a4.5 4.5 0 00.2 8.8A4.2 4.2 0 009.4 21H15a4 4 0 004-4v-1.1a4.5 4.5 0 00-.5-8.8A4.2 4.2 0 0014.2 3.5H9z" />
                  <path d="M9 8.5h6M8.5 12h7M10 15.5h4" />
                </svg>
              </button>
              <button
                type="button"
                className="workspace-chat__ghost"
                aria-label="이미지 첨부"
                onClick={handlePickImage}
              >
                <svg className="icon-sm" viewBox="0 0 24 24">
                  <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48" />
                </svg>
              </button>
              <div className="workspace-chat__model-picker">
                <button
                  type="button"
                  className={`workspace-chat__ghost${modelPickerOpen ? " is-active" : ""}`}
                  aria-label={`모델 선택 · ${selectedModelLabel}`}
                  title={selectedModelLabel}
                  disabled={availableModelOptions.length <= 1}
                  onClick={() => setModelPickerOpen((current) => !current)}
                >
                  <svg className="icon-sm" viewBox="0 0 24 24">
                    <path d="M12 3l2.2 4.46L19 9.1l-3.5 3.41.83 4.82L12 15.3l-4.33 2.03.83-4.82L5 9.1l4.8-.64L12 3z" />
                  </svg>
                </button>
                {modelPickerOpen ? (
                  <div className="workspace-chat__model-popover">
                    {availableModelOptions.map((option) => (
                      <button
                        key={option.value}
                        type="button"
                        className={`workspace-chat__model-option${option.value === selectedModel ? " is-selected" : ""}`}
                        onClick={() => {
                          if (option.value !== selectedModel) {
                            resetConversationForModelSwitch(option.label, option.backend);
                          }
                          setSelectedModel(option.value);
                          setModelPickerOpen(false);
                          setStatus(`모델 전환 중 · ${option.label}`);
                        }}
                      >
                        {option.label}
                      </button>
                    ))}
                  </div>
                ) : null}
              </div>
              <button type="submit" className="workspace-chat__send" disabled={isSending}>
                {isSending ? "전송 중" : "전송"}
              </button>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
}
