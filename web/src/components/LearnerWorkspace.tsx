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
  const [leftWidth, setLeftWidth] = useState(320);
  const [rightWidth, setRightWidth] = useState(260);
  const [resizingSide, setResizingSide] = useState<"left" | "right" | null>(null);
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

  useEffect(() => {
    if (!resizingSide) return;

    function handlePointerMove(event: PointerEvent) {
      if (resizingSide === "left") {
        setLeftWidth(Math.max(260, Math.min(520, event.clientX)));
      } else {
        setRightWidth(Math.max(220, Math.min(420, window.innerWidth - event.clientX)));
      }
    }

    function handlePointerUp() {
      setResizingSide(null);
    }

    window.addEventListener("pointermove", handlePointerMove);
    window.addEventListener("pointerup", handlePointerUp);
    document.body.style.cursor = "col-resize";

    return () => {
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointerup", handlePointerUp);
      document.body.style.cursor = "";
    };
  }, [resizingSide]);

  return (
    <div className="workspace-shell">
      <div className="workspace-grain" />
      <WorkspaceNav userId={userId} activeTab={activeTab} onTabChange={setActiveTab} />

      <div
        className={`workspace-body${focusMode ? " is-focus-mode" : ""}${resizingSide ? " is-resizing" : ""}`}
        style={{
          gridTemplateColumns: `${leftCollapsed ? 22 : leftWidth}px minmax(0, 1fr) ${rightCollapsed ? 22 : rightWidth}px`,
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
          {!leftCollapsed ? (
            <button
              type="button"
              className="workspace-drawer__resizer workspace-drawer__resizer--left"
              aria-label="왼쪽 패널 크기 조절"
              onPointerDown={() => setResizingSide("left")}
            />
          ) : null}
          <div className="workspace-drawer__content">
            <TutorChatPanel userId={userId} />
          </div>
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
          {!rightCollapsed ? (
            <button
              type="button"
              className="workspace-drawer__resizer workspace-drawer__resizer--right"
              aria-label="오른쪽 패널 크기 조절"
              onPointerDown={() => setResizingSide("right")}
            />
          ) : null}
          <div className="workspace-drawer__content">
            <WorkspaceRightRail />
          </div>
        </aside>
      </div>
    </div>
  );
}
