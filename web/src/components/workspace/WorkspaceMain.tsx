import {
  heroStats,
  heroTags,
  practiceModules,
  queueItems,
  readyPacks,
  skillProgress,
} from "./workspaceData";

function PackIcon() {
  return (
    <svg className="icon-pack" viewBox="0 0 24 24">
      <path d="M4 19.5A2.5 2.5 0 016.5 17H20" />
      <path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z" />
    </svg>
  );
}

function ModuleIcon({ variant }: { variant: string }) {
  if (variant === "primary") {
    return (
      <svg className="icon-img" viewBox="0 0 24 24">
        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
      </svg>
    );
  }

  if (variant === "green") {
    return (
      <svg className="icon-img icon-img--green" viewBox="0 0 24 24">
        <circle cx="12" cy="12" r="10" />
        <line x1="12" y1="8" x2="12" y2="16" />
        <line x1="8" y1="12" x2="16" y2="12" />
      </svg>
    );
  }

  return (
    <svg className="icon-img icon-img--slate" viewBox="0 0 24 24">
      <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" />
      <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
    </svg>
  );
}

function MediaImagePlaceholder() {
  return (
    <>
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" className="workspace-media__icon">
        <rect x="3" y="3" width="18" height="18" rx="2" />
        <circle cx="8.5" cy="8.5" r="1.5" />
        <polyline points="21 15 16 10 5 21" />
      </svg>
      <div className="workspace-media__drop-text">이미지 드롭 또는 클릭</div>
    </>
  );
}

function MediaAudioPlaceholder() {
  return (
    <>
      <div className="workspace-wave" aria-hidden="true">
        <span />
        <span />
        <span />
        <span />
        <span />
        <span />
        <span />
      </div>
      <div className="workspace-media__drop-text">오디오 세션 준비 중</div>
    </>
  );
}

export function WorkspaceMain() {
  return (
    <main className="workspace-main">
      <section className="workspace-hero workspace-fade-in">
        <div className="workspace-hero__tags">
          {heroTags.map((tag) => (
            <div key={tag} className="workspace-hero__tag">
              {tag}
            </div>
          ))}
        </div>

        <div className="workspace-hero__eyebrow">Learner Workspace</div>
        <h2 className="workspace-hero__title">
          집중 <em>학습 플로우</em>
        </h2>
        <p className="workspace-hero__copy">
          튜터 채팅, 문제 풀기, 설명 확인까지 한 화면에서 끊김 없이 이어지는 학습 경험.
        </p>

        <div className="workspace-hero__stats">
          {heroStats.map((item) => (
            <div key={item.label} className="workspace-hero-stat">
              <div className={`workspace-hero-stat__value${item.accent ? " is-accent" : ""}`}>{item.value}</div>
              <div>
                <div className="workspace-hero-stat__label">{item.label}</div>
                <div className="workspace-hero-stat__delta">{item.delta}</div>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="workspace-progress-row workspace-fade-in">
        <article className="workspace-panel">
          <div className="workspace-panel__head">
            <div className="workspace-panel__title">스킬 현황</div>
            <div className="workspace-panel__metric">이번 주 기준</div>
          </div>

          <div className="workspace-skill-list">
            {skillProgress.map((item) => (
              <div key={item.name} className="workspace-skill">
                <div className="workspace-skill__row">
                  <div className="workspace-skill__name">{item.name}</div>
                  <div className="workspace-skill__score">{item.score}</div>
                </div>
                <div className="workspace-skill__bar">
                  <div className={`workspace-skill__fill is-${item.tone}`} style={{ width: item.width }} />
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="workspace-panel">
          <div className="workspace-panel__head">
            <div className="workspace-panel__title">Ready Pack</div>
            <div className="workspace-panel__metric">5개 준비됨</div>
          </div>

          <div className="workspace-pack-list">
            {readyPacks.map((pack) => (
              <button key={pack.name} type="button" className="workspace-pack">
                <div className="workspace-pack__icon">
                  <PackIcon />
                </div>
                <div className="workspace-pack__body">
                  <div className="workspace-pack__name">{pack.name}</div>
                  <div className="workspace-pack__meta">{pack.meta}</div>
                </div>
                <div className={`workspace-pack__badge is-${pack.difficulty}`}>
                  {pack.difficulty === "easy" ? "쉬움" : pack.difficulty === "med" ? "보통" : "어려움"}
                </div>
              </button>
            ))}
          </div>
        </article>
      </section>

      <section className="workspace-fade-in">
        <div className="workspace-section-head">
          <div className="workspace-section-head__label">연습 모듈</div>
          <button type="button" className="workspace-section-head__action">
            전체 →
          </button>
        </div>

        <div className="workspace-modules">
          {practiceModules.map((module) => (
            <button key={module.title} type="button" className={`workspace-module is-${module.variant}`}>
              {module.badge ? <div className="workspace-module__badge">{module.badge}</div> : null}
              <div className={`workspace-module__icon is-${module.variant}`}>
                <ModuleIcon variant={module.variant} />
              </div>
              <div className="workspace-module__title">{module.title}</div>
              <div className="workspace-module__desc">{module.description}</div>
              <div className="workspace-module__arrow">↗</div>
            </button>
          ))}
        </div>
      </section>

      <section className="workspace-fade-in">
        <div className="workspace-section-head">
          <div className="workspace-section-head__label">개발 예정 모듈</div>
        </div>

        <div className="workspace-queue">
          {queueItems.map((item, index) => (
            <div key={item} className="workspace-queue__item">
              <div className="workspace-queue__num">{String(index + 1).padStart(2, "0")}</div>
              <div className="workspace-queue__text">{item}</div>
              <div className="workspace-queue__tag">예정</div>
            </div>
          ))}
        </div>
      </section>

      <section className="workspace-fade-in">
        <div className="workspace-section-head">
          <div className="workspace-section-head__label">멀티미디어 학습</div>
        </div>

        <div className="workspace-media-grid">
          <article className="workspace-media-card">
            <div className="workspace-media__title">이미지 기반 학습</div>
            <div className="workspace-media__copy">이미지 업로드 → 어휘 추출 → 멀티모달 분석 → 이미지 기반 퀴즈 생성.</div>
            <div className="workspace-media__drop">
              <MediaImagePlaceholder />
            </div>
            <div className="workspace-coming">Coming soon</div>
          </article>

          <article className="workspace-media-card">
            <div className="workspace-media__title">오디오 연습</div>
            <div className="workspace-media__copy">STT · TTS 재생 · 쉐도잉 연습 · 발음 채점 기능 제공 예정.</div>
            <div className="workspace-media__drop">
              <MediaAudioPlaceholder />
            </div>
            <div className="workspace-coming">Coming soon</div>
          </article>
        </div>
      </section>
    </main>
  );
}
