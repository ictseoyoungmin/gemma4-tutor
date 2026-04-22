import type { ReactNode } from "react";

export function StudyStageShell({
  modeLabel,
  counter,
  timer,
  progress,
  onBack,
  children,
  footer,
}: {
  modeLabel: string;
  counter?: ReactNode;
  timer?: ReactNode;
  progress?: number;
  onBack: () => void;
  children: ReactNode;
  footer?: ReactNode;
}) {
  return (
    <div className="workspace-ready-pack__study-shell">
      <div className="workspace-ready-pack__study-bar">
        <button
          type="button"
          className="workspace-ready-pack__back-btn workspace-ready-pack__back-btn--icon"
          onClick={onBack}
          aria-label="뒤로 가기"
          title="뒤로 가기"
        >
          ←
        </button>
        <div className="workspace-ready-pack__study-pill">{modeLabel}</div>
        <div className="workspace-ready-pack__study-spacer" />
        {counter ? <div className="workspace-ready-pack__study-counter">{counter}</div> : null}
        {timer ? <div className="workspace-ready-pack__timer-group">{timer}</div> : null}
      </div>

      {typeof progress === "number" ? (
        <div className="workspace-ready-pack__study-progress">
          <div
            className="workspace-ready-pack__study-progress-fill"
            style={{ width: `${Math.max(0, Math.min(100, progress))}%` }}
          />
        </div>
      ) : null}

      <div className="workspace-ready-pack__focus-stage">
        {children}
      </div>

      {footer}
    </div>
  );
}
