import { useState } from "react";
import "./workspace/workspace.css";
import { WorkspaceMain } from "./workspace/WorkspaceMain";
import { WorkspaceNav } from "./workspace/WorkspaceNav";
import { WorkspaceRightRail } from "./workspace/WorkspaceRightRail";
import { TutorChatPanel } from "./workspace/TutorChatPanel";

export function LearnerWorkspace({ userId }: { userId: string }) {
  const [activeTab, setActiveTab] = useState("학습 공간");

  return (
    <div className="workspace-shell">
      <div className="workspace-grain" />
      <WorkspaceNav userId={userId} activeTab={activeTab} onTabChange={setActiveTab} />

      <div className="workspace-body">
        <aside className="workspace-sidebar">
          <TutorChatPanel userId={userId} />
        </aside>

        <WorkspaceMain userId={userId} activeTab={activeTab} />
        <WorkspaceRightRail />
      </div>
    </div>
  );
}
