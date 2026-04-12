import { navTabs } from "./workspaceData";

export function WorkspaceNav({ userId }: { userId: string }) {
  return (
    <nav className="workspace-nav">
      <div className="workspace-nav__left">
        <div className="workspace-brand">
          <div className="workspace-brand__mark">
            <div className="workspace-brand__core" />
          </div>
          <span>StudyOS</span>
        </div>

        <div className="workspace-nav__divider" />

        <div className="workspace-tabs">
          {navTabs.map((tab, index) => (
            <button
              key={tab}
              type="button"
              className={`workspace-tab${index === 0 ? " is-active" : ""}`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      <div className="workspace-nav__right">
        <div className="workspace-streak-pill">
          <span>🔥</span>
          <span>12일 연속</span>
        </div>
        <button type="button" className="workspace-notif" aria-label="알림">
          <svg className="icon-sm" viewBox="0 0 24 24">
            <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 01-3.46 0" />
          </svg>
          <span className="workspace-notif__dot" />
        </button>
        <div className="workspace-avatar">{userId.slice(0, 2).toUpperCase()}</div>
      </div>
    </nav>
  );
}
