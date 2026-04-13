import { useMemo, useState } from "react";
import { sendChatMessage } from "../../api";
import { starterPrompts } from "./workspaceData";

type ChatTurn = {
  id: string;
  role: "user" | "assistant";
  message: string;
  meta?: string;
  suggestions?: string[];
};

const starterDrafts: Record<string, string> = {
  "TOEIC Part 5": "TOEIC Part 5 팁 하나 짧게 알려줘.",
  "문장 교정": "이 문장 교정해줘: I am agree with the plan.",
  워밍업: "가벼운 영어 워밍업 질문 하나 해줘.",
  어휘: "비즈니스 영어 어휘 3개만 알려줘.",
};

const initialTurns: ChatTurn[] = [
  {
    id: "intro-1",
    role: "assistant",
    message: "안녕하세요! TOEIC Part 5, 문장 교정, 워밍업 중 어떤 것부터 시작할까요?",
    meta: "intent: chat",
    suggestions: ["Part 5 풀기", "문장 교정"],
  },
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

export function TutorChatPanel({ userId }: { userId: string }) {
  const [draft, setDraft] = useState(starterDrafts["TOEIC Part 5"]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [turns, setTurns] = useState<ChatTurn[]>(initialTurns);
  const [status, setStatus] = useState("연결됨");
  const [isSending, setIsSending] = useState(false);

  const helperText = useMemo(() => {
    if (isSending) return "튜터가 다음 학습 흐름을 준비하고 있어요.";
    if (sessionId) return "현재 세션이 이어지고 있어요.";
    return "메시지를 입력하거나 예문에 답해보세요…";
  }, [isSending, sessionId]);

  async function handleSubmit(message: string) {
    const trimmed = message.trim();
    if (!trimmed || isSending) return;

    setTurns((current) => [
      ...current,
      {
        id: `user-${Date.now()}`,
        role: "user",
        message: trimmed,
      },
    ]);
    setDraft("");
    setIsSending(true);
    setStatus("메시지 전송 중...");

    try {
      const response = await sendChatMessage(userId, trimmed, sessionId);
      setSessionId(response.session_id);
      setTurns((current) => [
        ...current,
        {
          id: response.run_id,
          role: "assistant",
          message: response.output.message,
          meta: `intent: ${response.output.detected_intent}`,
          suggestions: response.output.suggested_next_actions,
        },
      ]);
      setStatus("응답 수신 완료");
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Unknown error";
      setTurns((current) => [
        ...current,
        {
          id: `error-${Date.now()}`,
          role: "assistant",
          message: `요청 처리 중 문제가 생겼어요. ${errorMessage}`,
          meta: "request.error",
        },
      ]);
      setStatus("연결 문제");
    } finally {
      setIsSending(false);
    }
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
      </div>

      <div className="workspace-chat__transcript">
        {turns.map((turn) => (
          <div key={turn.id} className={`workspace-bubble-row is-${turn.role}`}>
            {turn.role === "assistant" ? (
              <div className="workspace-ai-avatar">
                <div className="workspace-ai-avatar__dot" />
              </div>
            ) : null}

            <div className={`workspace-bubble is-${turn.role}`}>
              <div className="workspace-bubble__text">
                {turn.message.split("\n").map((line, index) => (
                  <span key={`${turn.id}-${index}`}>
                    {line}
                    {index < turn.message.split("\n").length - 1 ? <br /> : null}
                  </span>
                ))}
              </div>

              {turn.meta ? (
                <div className="workspace-bubble__meta">
                  <div className="workspace-bubble__meta-dot" />
                  {turn.meta}
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

        {isSending ? (
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
                className="workspace-chat__ghost"
                aria-label="학습 진단"
                onClick={() => setDraft("학습 진단부터 시작해줘.")}
              >
                <svg className="icon-sm" viewBox="0 0 24 24">
                  <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48" />
                </svg>
              </button>
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
