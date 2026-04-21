import { useEffect, useRef, useState } from "react";
import "./workspace/workspace.css";
import { WorkspaceMain } from "./workspace/WorkspaceMain";
import { WorkspaceNav } from "./workspace/WorkspaceNav";
import { WorkspaceRightRail } from "./workspace/WorkspaceRightRail";
import { TutorChatPanel } from "./workspace/TutorChatPanel";

export function LearnerWorkspace({ userId }: { userId: string }) {
  const [activeTab, setActiveTab] = useState("학습 공간");
  const [focusMode, setFocusMode] = useState(false);
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [rightCollapsed, setRightCollapsed] = useState(false);
  const previousPanelStateRef = useRef({ left: false, right: false });

  useEffect(() => {
    if (focusMode) {
      previousPanelStateRef.current = { left: leftCollapsed, right: rightCollapsed };
      setLeftCollapsed(true);
      setRightCollapsed(true);
      return;
    }

    setLeftCollapsed(previousPanelStateRef.current.left);
    setRightCollapsed(previousPanelStateRef.current.right);
  }, [focusMode]);

  return (
    <div className="workspace-shell">
      <div className="workspace-grain" />
      <WorkspaceNav userId={userId} activeTab={activeTab} onTabChange={setActiveTab} />

      <div
        className={`workspace-body${focusMode ? " is-focus-mode" : ""}`}
        style={{
          gridTemplateColumns: `${leftCollapsed ? 22 : 320}px minmax(0, 1fr) ${rightCollapsed ? 22 : 260}px`,
        }}
      >
        <aside className={`workspace-sidebar workspace-drawer${leftCollapsed ? " is-collapsed" : ""}`}>
          <button
            type="button"
            className="workspace-drawer__toggle workspace-drawer__toggle--left"
            onClick={() => setLeftCollapsed((current) => !current)}
            aria-label={leftCollapsed ? "왼쪽 패널 열기" : "왼쪽 패널 닫기"}
          >
            {leftCollapsed ? ">>" : "<<"}
          </button>
          <TutorChatPanel userId={userId} />
        </aside>

        <WorkspaceMain userId={userId} activeTab={activeTab} onReadyPackFocusChange={setFocusMode} />
        <aside className={`workspace-rail workspace-drawer${rightCollapsed ? " is-collapsed" : ""}`}>
          <button
            type="button"
            className="workspace-drawer__toggle workspace-drawer__toggle--right"
            onClick={() => setRightCollapsed((current) => !current)}
            aria-label={rightCollapsed ? "오른쪽 패널 열기" : "오른쪽 패널 닫기"}
          >
            {rightCollapsed ? "<<" : ">>"}
          </button>
          <WorkspaceRightRail />
        </aside>
      </div>
    </div>
  );
}
