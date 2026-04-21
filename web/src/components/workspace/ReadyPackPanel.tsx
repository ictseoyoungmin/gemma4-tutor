import { useEffect, useMemo, useState } from "react";
import { fetchReadyPacks, launchReadyPack, submitQuizAnswers } from "../../api";
import type { QuizItem, QuizSubmitResponse, ReadyPackLaunchResponse, ReadyQuizSummary } from "../../types";
import { StudyStageShell } from "./StudyStageShell";

type AnswerMap = Record<number, string>;
type StudyViewMode = "workspace" | "study" | "result";
type StudyMode = "practice" | "exam";

type StudySession = {
  mode: StudyMode;
  launch: ReadyPackLaunchResponse;
  answers: AnswerMap;
  currentIndex: number;
  revealedIndexes: number[];
  result: QuizSubmitResponse | null;
  startedAt: number;
  submittedAt: number | null;
  timerEnabled: boolean;
};

type ReviewEntry = {
  item: QuizItem;
  selectedAnswer: string;
  correctAnswer: string;
  isCorrect: boolean;
  feedback: string;
};

const difficultyLabel: Record<string, string> = {
  easy: "쉬움",
  medium: "보통",
  hard: "어려움",
};

const modeLabel: Record<StudyMode, string> = {
  practice: "연습 모드",
  exam: "실전 풀이",
};

const readyPackCatalog: Record<string, { itemCount: number; minutes: number; icon: "grammar" | "vocab" | "reading" | "listening" }> = {
  "Part 5 핵심 문법 40선": { itemCount: 40, minutes: 30, icon: "grammar" },
  "비즈니스 어휘 실전편": { itemCount: 60, minutes: 45, icon: "vocab" },
  "RC 고난도 모의고사": { itemCount: 100, minutes: 75, icon: "reading" },
  "전치사 집중 훈련": { itemCount: 30, minutes: 20, icon: "grammar" },
};

function getReadyPackDisplayMeta(pack: ReadyQuizSummary) {
  const preset = readyPackCatalog[pack.title];
  if (preset) return preset;
  const requestedItemCount = typeof pack.generation?.requested_item_count === "number" ? pack.generation.requested_item_count : null;
  const inferredItemCount = requestedItemCount ?? 20;
  return {
    itemCount: inferredItemCount,
    minutes: Math.max(10, Math.round(inferredItemCount * 0.75)),
    icon: pack.mode === "toeic" ? "reading" : "grammar",
  } as const;
}

function ReadyPackCardIcon({ icon }: { icon: "grammar" | "vocab" | "reading" | "listening" }) {
  if (icon === "vocab") {
    return (
      <svg className="workspace-ready-pack__card-icon-svg" viewBox="0 0 24 24">
        <path d="M5 6.5A2.5 2.5 0 0 1 7.5 4H20v15H7.5A2.5 2.5 0 0 0 5 21.5v-15Z" />
        <path d="M8 8h8" />
        <path d="M8 12h6" />
      </svg>
    );
  }
  if (icon === "reading") {
    return (
      <svg className="workspace-ready-pack__card-icon-svg" viewBox="0 0 24 24">
        <rect x="4" y="4" width="16" height="16" rx="3" />
        <path d="M8 8h8" />
        <path d="M8 12h8" />
        <path d="M8 16h5" />
      </svg>
    );
  }
  if (icon === "listening") {
    return (
      <svg className="workspace-ready-pack__card-icon-svg" viewBox="0 0 24 24">
        <path d="M12 5a7 7 0 0 1 7 7v4" />
        <path d="M5 16v-4a7 7 0 0 1 7-7" />
        <rect x="3" y="14" width="4" height="6" rx="2" />
        <rect x="17" y="14" width="4" height="6" rx="2" />
      </svg>
    );
  }
  return (
    <svg className="workspace-ready-pack__card-icon-svg" viewBox="0 0 24 24">
      <path d="M6 4h12" />
      <path d="M9 4v5" />
      <path d="M15 4v5" />
      <path d="M7 11h10l-1 8H8l-1-8Z" />
    </svg>
  );
}

function computeReviewEntries(session: StudySession): ReviewEntry[] {
  return session.launch.pack.items.map((item, index) => {
    const selectedAnswer = session.answers[index] ?? "";
    const isCorrect = selectedAnswer === item.answer;
    const feedback =
      session.result?.feedback[index] ??
      (selectedAnswer
        ? isCorrect
          ? "정답입니다."
          : "다시 확인해보세요."
        : "아직 답변하지 않았습니다.");

    return {
      item,
      selectedAnswer,
      correctAnswer: item.answer,
      isCorrect,
      feedback,
    };
  });
}

export function ReadyPackPanel({
  userId,
  onFocusModeChange,
}: {
  userId: string;
  onFocusModeChange?: (focused: boolean) => void;
}) {
  const [packs, setPacks] = useState<ReadyQuizSummary[]>([]);
  const [selectedPackId, setSelectedPackId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<StudyViewMode>("workspace");
  const [session, setSession] = useState<StudySession | null>(null);
  const [status, setStatus] = useState("Ready Pack 불러오는 중...");
  const [isLoading, setIsLoading] = useState(true);
  const [isLaunching, setIsLaunching] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [nowMs, setNowMs] = useState(Date.now());

  useEffect(() => {
    void loadReadyPacks();
  }, [userId]);

  useEffect(() => {
    onFocusModeChange?.(true);
    return () => onFocusModeChange?.(false);
  }, [onFocusModeChange]);

  useEffect(() => {
    if (viewMode !== "study" || !session?.timerEnabled) return;
    const intervalId = window.setInterval(() => {
      setNowMs(Date.now());
    }, 1000);
    return () => window.clearInterval(intervalId);
  }, [session?.timerEnabled, viewMode]);

  const reviewEntries = useMemo(() => (session ? computeReviewEntries(session) : []), [session]);
  const currentItem = session?.launch.pack.items[session.currentIndex] ?? null;
  const currentReviewEntry = reviewEntries[session?.currentIndex ?? 0] ?? null;
  const answeredCount = session ? Object.values(session.answers).filter(Boolean).length : 0;
  const totalCount = session?.launch.pack.items.length ?? 0;
  const canSubmitExam = Boolean(session && session.mode === "exam" && answeredCount === totalCount && !session.result);
  const practiceRevealActive =
    Boolean(session && session.mode === "practice" && session.revealedIndexes.includes(session.currentIndex));
  const resultSummary = useMemo(() => {
    if (!session) return null;
    const correct = reviewEntries.filter((entry) => entry.isCorrect).length;
    const unanswered = reviewEntries.filter((entry) => !entry.selectedAnswer).length;
    return {
      total: reviewEntries.length,
      correct,
      incorrect: reviewEntries.length - correct - unanswered,
      unanswered,
      scorePercent: reviewEntries.length ? Math.round((correct / reviewEntries.length) * 100) : 0,
    };
  }, [reviewEntries, session]);

  async function loadReadyPacks() {
    try {
      setIsLoading(true);
      const nextPacks = await fetchReadyPacks(userId);
      setPacks(nextPacks);
      setSelectedPackId((current) => current ?? nextPacks[0]?.ready_pack_id ?? null);
      setStatus(nextPacks.length ? "Ready Pack 준비됨" : "준비된 Ready Pack이 아직 없습니다");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Ready Pack을 가져오지 못했습니다.");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleLaunch(readyPackId: string, mode: StudyMode) {
    try {
      setIsLaunching(true);
      setStatus(mode === "exam" ? "실전 문제풀이 세션을 여는 중..." : "연습 세션을 여는 중...");
      setSelectedPackId(readyPackId);
      const launched = await launchReadyPack(userId, readyPackId);
      setSession({
        mode,
        launch: launched,
        answers: {},
        currentIndex: 0,
        revealedIndexes: [],
        result: null,
        startedAt: Date.now(),
        submittedAt: null,
        timerEnabled: true,
      });
      setViewMode("study");
      setStatus(`${modeLabel[mode]} 시작`);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Ready Pack 실행에 실패했습니다.");
    } finally {
      setIsLaunching(false);
    }
  }

  function handleSelectAnswer(choice: string) {
    setSession((current) => {
      if (!current || current.result) return current;
      const nextAnswers = { ...current.answers, [current.currentIndex]: choice };
      const nextRevealedIndexes =
        current.mode === "practice" && !current.revealedIndexes.includes(current.currentIndex)
          ? [...current.revealedIndexes, current.currentIndex]
          : current.revealedIndexes;
      return {
        ...current,
        answers: nextAnswers,
        revealedIndexes: nextRevealedIndexes,
      };
    });
  }

  function handleNavigate(index: number) {
    setSession((current) => (current ? { ...current, currentIndex: index } : current));
  }

  function handleBackToWorkspace() {
    setViewMode("workspace");
    setStatus("Ready Pack 목록으로 돌아왔습니다.");
  }

  function toggleTimer() {
    setSession((current) => (current ? { ...current, timerEnabled: !current.timerEnabled } : current));
  }

  async function handleSubmitExam() {
    if (!session || session.mode !== "exam" || isSubmitting || !canSubmitExam) return;

    try {
      setIsSubmitting(true);
      const orderedAnswers = session.launch.pack.items.map((_, index) => session.answers[index] ?? "");
      const submitted = await submitQuizAnswers(userId, session.launch.quiz_id, orderedAnswers);
      setSession((current) =>
        current
          ? {
              ...current,
              result: submitted,
              submittedAt: Date.now(),
            }
          : current,
      );
      setViewMode("result");
      setStatus(`채점 완료 · ${submitted.correct}/${submitted.total}`);
      void loadReadyPacks();
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "채점에 실패했습니다.");
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleFinishPractice() {
    if (!session) return;
    setSession((current) =>
      current
        ? {
            ...current,
            submittedAt: Date.now(),
          }
        : current,
    );
    setViewMode("result");
    setStatus("연습 결과를 확인하세요.");
  }

  function renderPackList() {
    if (!packs.length) {
      return (
        <div className="workspace-ready-pack__empty">
          {isLoading ? "불러오는 중..." : "아직 준비된 Ready Pack이 없습니다. 대시보드에서 prebuild job을 실행해보세요."}
        </div>
      );
    }

    return packs.map((pack) => (
      <article key={pack.ready_pack_id} className={`workspace-pack workspace-pack--launcher${selectedPackId === pack.ready_pack_id ? " is-active" : ""}`}>
        <div className="workspace-ready-pack__card-top">
          <div className="workspace-ready-pack__card-icon">
            <ReadyPackCardIcon icon={getReadyPackDisplayMeta(pack).icon} />
          </div>
          <div className={`workspace-pack__badge is-${pack.difficulty}`}>
            {difficultyLabel[pack.difficulty] ?? pack.difficulty}
          </div>
        </div>
        <button
          type="button"
          className="workspace-pack__body workspace-pack__body--selectable"
          onClick={() => setSelectedPackId(pack.ready_pack_id)}
        >
          <div className="workspace-pack__name">{pack.title}</div>
          <div className="workspace-ready-pack__card-stats">
            <span>{getReadyPackDisplayMeta(pack).itemCount}문항</span>
            <span>·</span>
            <span>{getReadyPackDisplayMeta(pack).minutes}분</span>
          </div>
          <div className="workspace-pack__meta">
            {pack.mode.toUpperCase()} · {new Date(pack.created_at).toLocaleDateString()}
          </div>
        </button>
        <div className="workspace-ready-pack__launcher-row">
          <div className="workspace-ready-pack__launcher-actions">
            <button
              type="button"
              className="workspace-ready-pack__ghost-btn"
              onClick={() => void handleLaunch(pack.ready_pack_id, "practice")}
              disabled={isLaunching}
            >
              연습
            </button>
            <button
              type="button"
              className="workspace-ready-pack__launch-btn"
              onClick={() => void handleLaunch(pack.ready_pack_id, "exam")}
              disabled={isLaunching}
            >
              문제 풀기
            </button>
          </div>
        </div>
      </article>
    ));
  }

  function renderWorkspaceView() {
    return (
      <div className="workspace-ready-pack__launcher-grid">
        {renderPackList()}
      </div>
    );
  }

  function renderChoiceButtons(item: QuizItem) {
    if (!session) return null;

    if (item.choices.length) {
      return (
        <div className="workspace-ready-pack__choices workspace-ready-pack__choices--stacked">
          {item.choices.map((choice, choiceIndex) => {
            const isSelected = session.answers[session.currentIndex] === choice;
            const reviewTone =
              viewMode === "result"
                ? choice === item.answer
                  ? " is-correct"
                  : isSelected
                    ? " is-wrong"
                    : ""
                : "";
            return (
              <button
                key={choice}
                type="button"
                className={`workspace-ready-pack__choice workspace-ready-pack__choice--block${isSelected ? " is-selected" : ""}${reviewTone}`}
                onClick={() => handleSelectAnswer(choice)}
                disabled={Boolean(session.result) || viewMode === "result"}
              >
                <span className="workspace-ready-pack__choice-index">{String.fromCharCode(65 + choiceIndex)}</span>
                <span>{choice}</span>
              </button>
            );
          })}
        </div>
      );
    }

    return (
      <textarea
        className="workspace-ready-pack__textarea"
        value={session.answers[session.currentIndex] ?? ""}
        onChange={(event) => handleSelectAnswer(event.target.value)}
        placeholder="답안을 입력하세요"
        disabled={Boolean(session.result) || viewMode === "result"}
      />
    );
  }

  function renderStudyStage() {
    if (!session || !currentItem || !currentReviewEntry) return null;

    const isFirst = session.currentIndex === 0;
    const isLast = session.currentIndex === session.launch.pack.items.length - 1;
    const elapsedMs = Math.max(0, nowMs - session.startedAt);
    const elapsedMinutes = Math.floor(elapsedMs / 60000);
    const elapsedSeconds = Math.floor((elapsedMs % 60000) / 1000);
    const recommendedMinutes = Math.max(1, Math.round(session.launch.pack.items.length * (session.mode === "exam" ? 0.75 : 0.5)));

    return (
      <StudyStageShell
        modeLabel={modeLabel[session.mode]}
        onBack={handleBackToWorkspace}
        counter={
          <>
            <strong>{session.currentIndex + 1}</strong> / {session.launch.pack.items.length}
          </>
        }
        progress={((session.currentIndex + 1) / session.launch.pack.items.length) * 100}
        timer={
          <>
            <button
              type="button"
              className={`workspace-ready-pack__timer-toggle${session.timerEnabled ? " is-on" : ""}`}
              onClick={toggleTimer}
            >
              Timer {session.timerEnabled ? "ON" : "OFF"}
            </button>
            <div className="workspace-ready-pack__timer-display">
              권장 {recommendedMinutes}분 · {session.timerEnabled ? `${String(elapsedMinutes).padStart(2, "0")}:${String(elapsedSeconds).padStart(2, "0")}` : "paused"}
            </div>
          </>
        }
      >
          <div key={`${session.launch.quiz_id}-${session.currentIndex}-${viewMode}`} className="workspace-ready-pack__question-card workspace-ready-pack__question-card--focus">
            <div className="workspace-ready-pack__question-type">
              {session.launch.pack.mode} · {difficultyLabel[session.launch.pack.difficulty]}
            </div>
            <div className="workspace-ready-pack__question">{currentItem.prompt}</div>
            {renderChoiceButtons(currentItem)}

            {session.mode === "practice" && practiceRevealActive ? (
              <div className="workspace-ready-pack__review-card">
                <div className={`workspace-ready-pack__review-status${currentReviewEntry.isCorrect ? " is-correct" : " is-wrong"}`}>
                  {currentReviewEntry.isCorrect ? "정답" : "오답"}
                </div>
                <div className="workspace-ready-pack__feedback">
                  내 답: {currentReviewEntry.selectedAnswer || "미응답"}
                </div>
                <div className="workspace-ready-pack__feedback">정답: {currentReviewEntry.correctAnswer}</div>
                <div className="workspace-ready-pack__feedback">{currentItem.explanation}</div>
              </div>
            ) : null}

            {session.mode === "exam" ? (
              <div className="workspace-ready-pack__meta-line">
                {answeredCount}/{totalCount} 문항 응답 완료 · 모든 문항에 답해야 제출할 수 있습니다.
              </div>
            ) : null}

            <div className="workspace-ready-pack__pager">
              <button
                type="button"
                className="workspace-ready-pack__pager-btn"
                onClick={() => handleNavigate(session.currentIndex - 1)}
                disabled={isFirst}
                aria-label="이전 문제"
              >
                ←
              </button>
              <div className="workspace-ready-pack__pager-dots">
                {session.launch.pack.items.map((_, index) => {
                  const isAnswered = Boolean(session.answers[index]);
                  return (
                    <button
                      key={`${session.launch.quiz_id}-dot-${index}`}
                      type="button"
                      className={`workspace-ready-pack__pager-dot${session.currentIndex === index ? " is-current" : ""}${isAnswered ? " is-done" : ""}`}
                      onClick={() => handleNavigate(index)}
                      aria-label={`${index + 1}번 문제 이동`}
                    />
                  );
                })}
              </div>
              {session.mode === "practice" && answeredCount === totalCount ? (
                <button type="button" className="workspace-practice__submit" onClick={handleFinishPractice}>
                  결과 보기
                </button>
              ) : session.mode === "exam" && isLast ? (
                <button
                  type="button"
                  className="workspace-practice__submit"
                  onClick={() => void handleSubmitExam()}
                  disabled={!canSubmitExam || isSubmitting}
                >
                  {isSubmitting ? "채점 중" : "최종 제출"}
                </button>
              ) : (
                <button
                  type="button"
                  className="workspace-ready-pack__pager-btn workspace-ready-pack__pager-btn--next"
                  onClick={() => handleNavigate(session.currentIndex + 1)}
                  disabled={isLast}
                  aria-label="다음 문제"
                >
                  →
                </button>
              )}
            </div>
          </div>
      </StudyStageShell>
    );
  }

  function renderResultView() {
    if (!session || !resultSummary || !currentReviewEntry) return null;

    return (
      <div className="workspace-ready-pack__result-shell">
        <div className="workspace-ready-pack__result-summary">
          <article className="workspace-ready-pack__result-stat">
            <div className="workspace-ready-pack__result-value">{resultSummary.scorePercent}%</div>
            <div className="workspace-ready-pack__result-label">총점</div>
          </article>
          <article className="workspace-ready-pack__result-stat">
            <div className="workspace-ready-pack__result-value">{resultSummary.correct}</div>
            <div className="workspace-ready-pack__result-label">정답</div>
          </article>
          <article className="workspace-ready-pack__result-stat">
            <div className="workspace-ready-pack__result-value">{resultSummary.incorrect}</div>
            <div className="workspace-ready-pack__result-label">오답</div>
          </article>
          <article className="workspace-ready-pack__result-stat">
            <div className="workspace-ready-pack__result-value">{resultSummary.unanswered}</div>
            <div className="workspace-ready-pack__result-label">미응답</div>
          </article>
        </div>

        <StudyStageShell
          modeLabel="결과 리뷰"
          onBack={handleBackToWorkspace}
          counter={`${session.currentIndex + 1} / ${session.launch.pack.items.length}`}
        >
          <div key={`${session.launch.quiz_id}-result-${session.currentIndex}`} className="workspace-ready-pack__question-card workspace-ready-pack__question-card--focus">
            <div className="workspace-ready-pack__question-type">Review</div>
            <div className="workspace-ready-pack__question">{currentReviewEntry.item.prompt}</div>
            {renderChoiceButtons(currentReviewEntry.item)}
            <div className="workspace-ready-pack__review-card">
              <div className={`workspace-ready-pack__review-status${currentReviewEntry.isCorrect ? " is-correct" : " is-wrong"}`}>
                {currentReviewEntry.isCorrect ? "정답입니다" : currentReviewEntry.selectedAnswer ? "오답입니다" : "미응답"}
              </div>
              <div className="workspace-ready-pack__feedback">
                내 답: {currentReviewEntry.selectedAnswer || "선택하지 않음"}
              </div>
              <div className="workspace-ready-pack__feedback">정답: {currentReviewEntry.correctAnswer}</div>
              <div className="workspace-ready-pack__feedback">{currentReviewEntry.item.explanation}</div>
              <div className="workspace-ready-pack__feedback">{currentReviewEntry.feedback}</div>
            </div>
            <div className="workspace-ready-pack__pager">
              <button
                type="button"
                className="workspace-ready-pack__pager-btn"
                onClick={() => handleNavigate(session.currentIndex - 1)}
                disabled={session.currentIndex === 0}
                aria-label="이전 리뷰"
              >
                ←
              </button>
              <div className="workspace-ready-pack__pager-dots">
                {reviewEntries.map((entry, index) => {
                  const tone = !entry.selectedAnswer ? " is-unanswered" : entry.isCorrect ? " is-correct" : " is-wrong";
                  return (
                    <button
                      key={`${session.launch.quiz_id}-review-dot-${index}`}
                      type="button"
                      className={`workspace-ready-pack__pager-dot${session.currentIndex === index ? " is-current" : ""}${tone}`}
                      onClick={() => handleNavigate(index)}
                      aria-label={`${index + 1}번 리뷰 이동`}
                    />
                  );
                })}
              </div>
              <button
                type="button"
                className="workspace-ready-pack__pager-btn workspace-ready-pack__pager-btn--next"
                onClick={() => handleNavigate(session.currentIndex + 1)}
                disabled={session.currentIndex === session.launch.pack.items.length - 1}
                aria-label="다음 리뷰"
              >
                →
              </button>
            </div>
          </div>
        </StudyStageShell>
      </div>
    );
  }

  return (
    <section className="workspace-panel workspace-ready-pack">
      <div className="workspace-panel__head">
        <div className="workspace-ready-pack__head-meta">
          <span className="workspace-panel__metric">{status}</span>
          <button type="button" className="workspace-ready-pack__refresh" onClick={() => void loadReadyPacks()}>
            새로고침
          </button>
        </div>
      </div>

      {viewMode === "workspace" ? renderWorkspaceView() : null}
      {viewMode === "study" ? renderStudyStage() : null}
      {viewMode === "result" ? renderResultView() : null}
    </section>
  );
}
