import "./workspace/workspace.css";
import { WorkspaceMain } from "./workspace/WorkspaceMain";
import { WorkspaceNav } from "./workspace/WorkspaceNav";
import { WorkspaceRightRail } from "./workspace/WorkspaceRightRail";
import { TutorChatPanel } from "./workspace/TutorChatPanel";

export function LearnerWorkspace({ userId }: { userId: string }) {
  return (
    <div className="workspace-shell">
      <div className="workspace-grain" />
      <WorkspaceNav userId={userId} />

      <div className="workspace-body">
        <aside className="workspace-sidebar">
          <TutorChatPanel userId={userId} />
        </aside>

        <WorkspaceMain />
        <WorkspaceRightRail />
      </div>
    </div>
  );
}
