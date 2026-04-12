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
      <div style={sidebarHeaderStyle}>
        <div style={eyebrowStyle}>AI tutor</div>
        <div style={sidebarTitleStyle}>What do you want to practice today?</div>
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
      </div>

      <div style={transcriptStyle}>
        {turns.map((turn) => (
          <div
            key={turn.id}
            style={turn.role === "user" ? userBubbleWrapStyle : assistantBubbleWrapStyle}
          >
            {turn.role === "assistant" ? <div style={aiAvatarStyle}><div style={aiAvatarDotStyle} /></div> : null}
            <div style={turn.role === "user" ? userBubbleStyle : assistantBubbleStyle}>
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

      <div style={statusRowStyle}>
        <div style={badgeStyle}>
          <div style={badgeDotStyle} />
          {status}
        </div>
        <div style={sessionStyle}>session: {sessionId ?? "new"}</div>
      </div>

      <form
        style={composerStyle}
        onSubmit={(event) => {
          event.preventDefault();
          void handleSubmit(draft);
        }}
      >
        <div style={composerShellStyle}>
          <textarea
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder="Ask the tutor for guidance, correction, or a practice prompt..."
            style={textareaStyle}
            rows={3}
          />
          <div style={composerFooterStyle}>
            <button type="submit" style={sendButtonStyle} disabled={isSending}>
              {isSending ? "Sending..." : "Send to Tutor"}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}

const panelStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateRows: "auto minmax(0, 1fr) auto auto",
  minHeight: "100%",
  height: "100%",
};

const sidebarHeaderStyle: React.CSSProperties = {
  padding: "20px 20px 16px",
  borderBottom: "1px solid rgba(255,255,255,0.08)",
};

const eyebrowStyle: React.CSSProperties = {
  fontSize: 10,
  letterSpacing: 1.6,
  textTransform: "uppercase",
  color: "#ba7517",
  marginBottom: 6,
};

const sidebarTitleStyle: React.CSSProperties = {
  fontFamily: "\"Lora\", Georgia, serif",
  fontSize: 18,
  fontWeight: 400,
  color: "#f5ede0",
  lineHeight: 1.3,
  marginBottom: 14,
};

const sessionStyle: React.CSSProperties = {
  fontSize: 11,
  color: "#7d6f5e",
  fontFamily: "\"SF Mono\", \"Fira Code\", monospace",
};

const starterRowStyle: React.CSSProperties = {
  display: "flex",
  gap: 6,
  flexWrap: "wrap",
};

const promptChipStyle: React.CSSProperties = {
  borderRadius: 999,
  border: "1px solid rgba(255,255,255,0.13)",
  background: "transparent",
  padding: "5px 11px",
  cursor: "pointer",
  color: "#c4b49a",
  fontSize: 12,
};

const transcriptStyle: React.CSSProperties = {
  display: "grid",
  gap: 14,
  overflowY: "auto",
  padding: "18px 20px",
};

const userBubbleWrapStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "flex-end",
};

const assistantBubbleWrapStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "flex-end",
  gap: 8,
  justifyContent: "flex-start",
};

const aiAvatarStyle: React.CSSProperties = {
  width: 24,
  height: 24,
  borderRadius: 7,
  background: "#412402",
  border: "1px solid #854f0b",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  flexShrink: 0,
};

const aiAvatarDotStyle: React.CSSProperties = {
  width: 10,
  height: 10,
  borderRadius: 2,
  background: "#ef9f27",
};

const userBubbleStyle: React.CSSProperties = {
  maxWidth: "82%",
  borderRadius: "16px 16px 4px 16px",
  padding: "10px 14px",
  background: "#27211a",
  border: "1px solid rgba(255,255,255,0.13)",
  color: "#f5ede0",
  fontSize: 13,
};

const assistantBubbleStyle: React.CSSProperties = {
  maxWidth: "84%",
  borderRadius: "4px 16px 16px 16px",
  padding: "10px 14px",
  background: "#1f1408",
  color: "#faeeda",
  border: "1px solid #854f0b",
  fontSize: 13,
};

const bubbleMessageStyle: React.CSSProperties = {
  whiteSpace: "pre-wrap",
  lineHeight: 1.65,
};

const bubbleMetaStyle: React.CSSProperties = {
  marginTop: 8,
  fontSize: 11,
  color: "#854f0b",
  fontFamily: "\"SF Mono\", \"Fira Code\", monospace",
  opacity: 0.85,
};

const suggestionRowStyle: React.CSSProperties = {
  display: "flex",
  gap: 5,
  flexWrap: "wrap",
  marginTop: 9,
};

const suggestionChipStyle: React.CSSProperties = {
  borderRadius: 999,
  border: "1px solid #854f0b",
  background: "transparent",
  color: "#ef9f27",
  padding: "4px 9px",
  cursor: "pointer",
  fontSize: 11,
};

const statusRowStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  gap: 10,
  padding: "8px 20px",
  borderTop: "1px solid rgba(255,255,255,0.08)",
};

const badgeStyle: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: 6,
  padding: "4px 10px",
  borderRadius: 999,
  background: "#1a2710",
  border: "1px solid rgba(99,153,34,0.3)",
  color: "#8ab85a",
  fontSize: 11,
};

const badgeDotStyle: React.CSSProperties = {
  width: 6,
  height: 6,
  borderRadius: "50%",
  background: "#8ab85a",
};

const composerStyle: React.CSSProperties = {
  padding: "12px 16px",
  borderTop: "1px solid rgba(255,255,255,0.08)",
};

const textareaStyle: React.CSSProperties = {
  width: "100%",
  border: "none",
  outline: "none",
  background: "transparent",
  color: "#f5ede0",
  resize: "vertical",
  font: "inherit",
  minHeight: 76,
  lineHeight: 1.55,
};

const composerFooterStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "flex-end",
  gap: 10,
  alignItems: "center",
  marginTop: 8,
};

const sendButtonStyle: React.CSSProperties = {
  borderRadius: 9,
  border: "none",
  padding: "7px 16px",
  background: "#ba7517",
  color: "#faeeda",
  cursor: "pointer",
  fontWeight: 500,
};

const composerShellStyle: React.CSSProperties = {
  border: "1px solid rgba(255,255,255,0.13)",
  borderRadius: 16,
  padding: "10px 12px",
  background: "#1e1a15",
};
