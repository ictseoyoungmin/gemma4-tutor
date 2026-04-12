import { useState } from "react";
import { sendChatMessage } from "../api";

type ChatTurn = {
  id: string;
  role: "user" | "assistant";
  message: string;
  meta?: string;
  suggestions?: string[];
};

const starterPrompts = [
  "Give me one short TOEIC Part 5 tip.",
  "Correct this sentence: I am agree with the plan.",
  "Ask me one easy English warm-up question.",
];

export function TutorChatPanel({ userId }: { userId: string }) {
  const [draft, setDraft] = useState(starterPrompts[0]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [turns, setTurns] = useState<ChatTurn[]>([
    {
      id: "intro",
      role: "assistant",
      message:
        "Start a conversation here. This panel now calls the real /v1/chat route and keeps the returned session id for follow-up messages.",
      meta: "Connected to tutor API",
    },
  ]);
  const [status, setStatus] = useState("Ready");
  const [isSending, setIsSending] = useState(false);

  async function handleSubmit(message: string) {
    const trimmed = message.trim();
    if (!trimmed || isSending) return;

    const userTurn: ChatTurn = {
      id: `user-${Date.now()}`,
      role: "user",
      message: trimmed,
    };
    setTurns((current) => [...current, userTurn]);
    setDraft("");
    setIsSending(true);
    setStatus("Sending message...");

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
      setStatus("Tutor reply received");
    } catch (error) {
      const messageText = error instanceof Error ? error.message : "Unknown error";
      setTurns((current) => [
        ...current,
        {
          id: `error-${Date.now()}`,
          role: "assistant",
          message: `Request failed. ${messageText}`,
          meta: "request error",
        },
      ]);
      setStatus(messageText);
    } finally {
      setIsSending(false);
    }
  }

  return (
    <div style={panelStyle}>
      <div style={statusRowStyle}>
        <div style={badgeStyle}>{status}</div>
        <div style={sessionStyle}>session: {sessionId ?? "new"}</div>
      </div>

      <div style={starterRowStyle}>
        {starterPrompts.map((prompt) => (
          <button
            key={prompt}
            type="button"
            onClick={() => setDraft(prompt)}
            style={promptChipStyle}
          >
            {prompt}
          </button>
        ))}
      </div>

      <div style={transcriptStyle}>
        {turns.map((turn) => (
          <div
            key={turn.id}
            style={turn.role === "user" ? userBubbleWrapStyle : assistantBubbleWrapStyle}
          >
            <div style={turn.role === "user" ? userBubbleStyle : assistantBubbleStyle}>
              <div style={bubbleRoleStyle}>{turn.role === "user" ? "You" : "Tutor"}</div>
              <div style={bubbleMessageStyle}>{turn.message}</div>
              {turn.meta ? <div style={bubbleMetaStyle}>{turn.meta}</div> : null}
              {turn.suggestions?.length ? (
                <div style={suggestionRowStyle}>
                  {turn.suggestions.map((suggestion) => (
                    <button
                      key={suggestion}
                      type="button"
                      onClick={() => setDraft(suggestion)}
                      style={suggestionChipStyle}
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
          </div>
        ))}
      </div>

      <form
        style={composerStyle}
        onSubmit={(event) => {
          event.preventDefault();
          void handleSubmit(draft);
        }}
      >
        <textarea
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Ask the tutor for guidance, correction, or a practice prompt..."
          style={textareaStyle}
          rows={4}
        />
        <div style={composerFooterStyle}>
          <div style={helperTextStyle}>
            Uses `user_id={userId}` and keeps the returned chat session for follow-up turns.
          </div>
          <button type="submit" style={sendButtonStyle} disabled={isSending}>
            {isSending ? "Sending..." : "Send to Tutor"}
          </button>
        </div>
      </form>
    </div>
  );
}

const panelStyle: React.CSSProperties = {
  display: "grid",
  gap: 14,
};

const statusRowStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  gap: 10,
  flexWrap: "wrap",
  alignItems: "center",
};

const badgeStyle: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  borderRadius: 999,
  padding: "8px 12px",
  background: "#eff6ff",
  color: "#1d4ed8",
  fontWeight: 600,
  fontSize: 13,
};

const sessionStyle: React.CSSProperties = {
  fontSize: 13,
  color: "#64748b",
};

const starterRowStyle: React.CSSProperties = {
  display: "flex",
  gap: 8,
  flexWrap: "wrap",
};

const promptChipStyle: React.CSSProperties = {
  borderRadius: 999,
  border: "1px solid #cbd5e1",
  background: "#fff",
  padding: "8px 12px",
  cursor: "pointer",
  color: "#334155",
};

const transcriptStyle: React.CSSProperties = {
  display: "grid",
  gap: 12,
  maxHeight: 460,
  overflowY: "auto",
  padding: 4,
};

const userBubbleWrapStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "flex-end",
};

const assistantBubbleWrapStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "flex-start",
};

const userBubbleStyle: React.CSSProperties = {
  maxWidth: "86%",
  borderRadius: 18,
  padding: 14,
  background: "#111827",
  color: "white",
};

const assistantBubbleStyle: React.CSSProperties = {
  maxWidth: "86%",
  borderRadius: 18,
  padding: 14,
  background: "#f8fafc",
  color: "#0f172a",
  border: "1px solid #e2e8f0",
};

const bubbleRoleStyle: React.CSSProperties = {
  fontSize: 12,
  textTransform: "uppercase",
  letterSpacing: 1,
  opacity: 0.7,
  marginBottom: 8,
};

const bubbleMessageStyle: React.CSSProperties = {
  whiteSpace: "pre-wrap",
  lineHeight: 1.6,
};

const bubbleMetaStyle: React.CSSProperties = {
  marginTop: 10,
  fontSize: 12,
  opacity: 0.75,
};

const suggestionRowStyle: React.CSSProperties = {
  display: "flex",
  gap: 8,
  flexWrap: "wrap",
  marginTop: 12,
};

const suggestionChipStyle: React.CSSProperties = {
  borderRadius: 999,
  border: "1px solid #bfdbfe",
  background: "#dbeafe",
  color: "#1d4ed8",
  padding: "6px 10px",
  cursor: "pointer",
};

const composerStyle: React.CSSProperties = {
  display: "grid",
  gap: 10,
};

const textareaStyle: React.CSSProperties = {
  width: "100%",
  borderRadius: 16,
  border: "1px solid #cbd5e1",
  padding: 14,
  resize: "vertical",
  font: "inherit",
  minHeight: 110,
};

const composerFooterStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  gap: 12,
  alignItems: "center",
  flexWrap: "wrap",
};

const helperTextStyle: React.CSSProperties = {
  fontSize: 13,
  color: "#64748b",
};

const sendButtonStyle: React.CSSProperties = {
  borderRadius: 12,
  border: "none",
  padding: "10px 14px",
  background: "#2563eb",
  color: "white",
  cursor: "pointer",
  fontWeight: 600,
};
