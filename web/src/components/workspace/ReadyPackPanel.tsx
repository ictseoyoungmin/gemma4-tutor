import { useEffect, useState } from "react";
import { fetchReadyPacks, launchReadyPack, submitQuizAnswers } from "../../api";
import type { QuizSubmitResponse, ReadyPackLaunchResponse, ReadyQuizSummary } from "../../types";

type AnswerMap = Record<number, string>;

const difficultyLabel: Record<string, string> = {
  easy: "쉬움",
  medium: "보통",
  hard: "어려움",
};

export function ReadyPackPanel({ userId }: { userId: string }) {
  const [packs, setPacks] = useState<ReadyQuizSummary[]>([]);
  const [activePack, setActivePack] = useState<ReadyPackLaunchResponse | null>(null);
  const [answers, setAnswers] = useState<AnswerMap>({});
  const [result, setResult] = useState<QuizSubmitResponse | null>(null);
  const [status, setStatus] = useState("Ready Pack 불러오는 중...");
  const [isLoading, setIsLoading] = useState(true);
  const [isLaunching, setIsLaunching] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    void loadReadyPacks();
  }, [userId]);

  async function loadReadyPacks() {
    try {
      setIsLoading(true);
      const nextPacks = await fetchReadyPacks(userId);
      setPacks(nextPacks);
      setStatus(nextPacks.length ? "Ready Pack 준비됨" : "준비된 Ready Pack이 아직 없습니다");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Ready Pack을 가져오지 못했습니다.");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleLaunch(readyPackId: string) {
    try {
      setIsLaunching(true);
      setStatus("Ready Pack을 시작하는 중...");
      const launched = await launchReadyPack(userId, readyPackId);
      setActivePack(launched);
      setAnswers({});
      setResult(null);
      setStatus("Ready Pack 실행 중");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Ready Pack 실행에 실패했습니다.");
    } finally {
      setIsLaunching(false);
    }
  }

  async function handleSubmit() {
    if (!activePack || isSubmitting) return;

    try {
      setIsSubmitting(true);
      const orderedAnswers = activePack.pack.items.map((item, index) => answers[index] ?? "");
      const submitted = await submitQuizAnswers(userId, activePack.quiz_id, orderedAnswers);
      setResult(submitted);
      setStatus(`채점 완료 · ${submitted.correct}/${submitted.total}`);
      void loadReadyPacks();
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "채점에 실패했습니다.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="workspace-panel workspace-ready-pack">
      <div className="workspace-panel__head">
        <div>
          <div className="workspace-panel__title">Ready Pack Launcher</div>
          <div className="workspace-ready-pack__subcopy">대기 중인 팩을 선택해 바로 집중 학습으로 전환합니다.</div>
        </div>
        <div className="workspace-ready-pack__head-meta">
          <span className="workspace-panel__metric">{status}</span>
          <button type="button" className="workspace-ready-pack__refresh" onClick={() => void loadReadyPacks()}>
            새로고침
          </button>
        </div>
      </div>

      <div className="workspace-ready-pack__layout">
        <div className="workspace-ready-pack__list">
          {packs.length ? (
            packs.map((pack) => (
              <button
                key={pack.ready_pack_id}
                type="button"
                className={`workspace-pack${activePack?.ready_pack_id === pack.ready_pack_id ? " is-active" : ""}`}
                onClick={() => void handleLaunch(pack.ready_pack_id)}
                disabled={isLaunching}
              >
                <div className="workspace-pack__body">
                  <div className="workspace-pack__name">{pack.title}</div>
                  <div className="workspace-pack__meta">{pack.mode} · {new Date(pack.created_at).toLocaleDateString()}</div>
                </div>
                <div className={`workspace-pack__badge is-${pack.difficulty}`}>
                  {difficultyLabel[pack.difficulty] ?? pack.difficulty}
                </div>
              </button>
            ))
          ) : (
            <div className="workspace-ready-pack__empty">
              {isLoading ? "불러오는 중..." : "아직 준비된 Ready Pack이 없습니다. 대시보드에서 prebuild job을 실행해보세요."}
            </div>
          )}
        </div>

        <div className="workspace-ready-pack__workspace">
          {activePack ? (
            <>
              <div className="workspace-ready-pack__title-row">
                <div>
                  <div className="workspace-ready-pack__title">{activePack.pack.title}</div>
                  <div className="workspace-ready-pack__meta-line">
                    {activePack.pack.mode} · {difficultyLabel[activePack.pack.difficulty]} · {activePack.pack.items.length}문항
                  </div>
                </div>
                <div className="workspace-session-id">quiz:{activePack.quiz_id.slice(0, 6)}</div>
              </div>

              <div className="workspace-ready-pack__items">
                {activePack.pack.items.map((item, index) => (
                  <div key={`${activePack.quiz_id}-${index}`} className="workspace-ready-pack__item">
                    <div className="workspace-ready-pack__question">
                      Q{index + 1}. {item.prompt}
                    </div>
                    {item.choices.length ? (
                      <div className="workspace-ready-pack__choices">
                        {item.choices.map((choice) => (
                          <button
                            key={choice}
                            type="button"
                            className={`workspace-ready-pack__choice${answers[index] === choice ? " is-selected" : ""}`}
                            onClick={() => setAnswers((current) => ({ ...current, [index]: choice }))}
                            disabled={Boolean(result)}
                          >
                            {choice}
                          </button>
                        ))}
                      </div>
                    ) : (
                      <textarea
                        className="workspace-ready-pack__textarea"
                        value={answers[index] ?? ""}
                        onChange={(event) =>
                          setAnswers((current) => ({ ...current, [index]: event.target.value }))
                        }
                        placeholder="답안을 입력하세요"
                        disabled={Boolean(result)}
                      />
                    )}
                    {result ? <div className="workspace-ready-pack__feedback">{result.feedback[index]}</div> : null}
                  </div>
                ))}
              </div>

              <div className="workspace-ready-pack__footer">
                <button
                  type="button"
                  className="workspace-practice__submit"
                  onClick={() => void handleSubmit()}
                  disabled={isSubmitting || Boolean(result)}
                >
                  {isSubmitting ? "채점 중" : "Ready Pack 제출"}
                </button>
                {result ? (
                  <div className="workspace-ready-pack__score">
                    점수 {Math.round(result.score * 100)}% · {result.correct}/{result.total}
                  </div>
                ) : null}
              </div>
            </>
          ) : (
            <div className="workspace-ready-pack__empty">
              왼쪽 목록에서 Ready Pack을 선택하면 이 영역에서 바로 문제를 풀 수 있습니다.
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
