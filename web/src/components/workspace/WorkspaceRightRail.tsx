import { achievements, attendance } from "./workspaceData";

const dayLabels = ["월", "화", "수", "목", "금", "토", "일"];

export function WorkspaceRightRail() {
  return (
    <div className="workspace-rail__inner">
      <div className="workspace-rail__head">
        <div className="workspace-rail__eyebrow">학습 현황</div>
        <div>
          <div className="workspace-rail__subhead">4월 출석</div>
          <div className="workspace-calendar">
            {dayLabels.map((label) => (
              <div key={label} className="workspace-calendar__label">
                {label}
              </div>
            ))}

            {attendance.map((item) => (
              <div key={`${item.day}-${item.value}`} className={`workspace-calendar__day is-${item.state}`}>
                {item.value}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="workspace-rail__body">
        <section>
          <div className="workspace-rail__subhead">업적</div>
          <div className="workspace-achievement-list">
            {achievements.map((achievement) => (
              <div key={achievement.title} className="workspace-achievement">
                <div className={`workspace-achievement__icon${achievement.unlocked ? " is-unlocked" : " is-locked"}`}>
                  {achievement.icon}
                </div>
                <div>
                  <div className="workspace-achievement__title">{achievement.title}</div>
                  <div className="workspace-achievement__desc">{achievement.description}</div>
                </div>
                {achievement.unlocked ? <div className="workspace-achievement__badge">달성</div> : null}
              </div>
            ))}
          </div>
        </section>

        <section className="workspace-consistency">
          <div className="workspace-rail__subhead">Consistency</div>
          <div className="workspace-consistency__value">12일</div>
          <div className="workspace-consistency__copy">
            지금 페이스를 유지하면 이번 주 목표 세션을 무난하게 채울 수 있어요.
          </div>
        </section>
      </div>
    </div>
  );
}
