import { useEffect, useMemo, useState } from "react";
import {
  fetchProblemInventory,
  fetchWorkerStatus,
  queueProblemGeneration,
  startWorker,
  stopWorker,
} from "../../api";
import type { ProblemInventoryResponse, WorkerStatusResponse } from "../../types";

const partLabels = [
  { key: "part1", label: "Part 1" },
  { key: "part2", label: "Part 2" },
  { key: "part3", label: "Part 3" },
  { key: "part4", label: "Part 4" },
  { key: "part5", label: "Part 5" },
  { key: "part6", label: "Part 6" },
  { key: "part7", label: "Part 7" },
] as const;

const difficultyLabel: Record<string, string> = {
  easy: "쉬움",
  medium: "보통",
  hard: "어려움",
};

export function ProblemTab({ userId }: { userId: string }) {
  const [inventory, setInventory] = useState<ProblemInventoryResponse | null>(null);
  const [workerStatus, setWorkerStatus] = useState<WorkerStatusResponse | null>(null);
  const [status, setStatus] = useState("문제 인벤토리를 불러오는 중...");
  const [readyPackPage, setReadyPackPage] = useState(1);
  const [practiceItemPage, setPracticeItemPage] = useState(1);
  const [counts, setCounts] = useState<Record<string, number>>({
    part1: 0,
    part2: 3,
    part3: 0,
    part4: 0,
    part5: 4,
    part6: 0,
    part7: 0,
  });

  const totalRequested = useMemo(
    () => Object.values(counts).reduce((sum, value) => sum + value, 0),
    [counts],
  );

  useEffect(() => {
    void loadAll();
  }, [userId, readyPackPage, practiceItemPage]);

  async function loadAll() {
    try {
      const [nextInventory, nextWorkerStatus] = await Promise.all([
        fetchProblemInventory(userId, readyPackPage, practiceItemPage, 5),
        fetchWorkerStatus(),
      ]);
      setInventory(nextInventory);
      setWorkerStatus(nextWorkerStatus);
      setStatus("문제 인벤토리 준비 완료");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "문제 정보를 가져오지 못했습니다.");
    }
  }

  async function handleStartWorker() {
    const result = await startWorker(1);
    setWorkerStatus(result);
    setStatus("워커가 실행되었습니다.");
  }

  async function handleStopWorker() {
    const result = await stopWorker();
    setWorkerStatus(result);
    setStatus("워커가 중지되었습니다.");
  }

  async function handleGenerate() {
    try {
      setStatus("문제 생성 작업을 큐에 추가하는 중...");
      await queueProblemGeneration(userId, counts);
      await loadAll();
      setStatus(`${totalRequested}개 Pack 생성 작업을 큐에 추가했습니다.`);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "문제 생성 요청에 실패했습니다.");
    }
  }

  return (
    <section className="workspace-problem-tab workspace-fade-in">
      <div className="workspace-problem-grid">
        <article className="workspace-panel">
          <div className="workspace-panel__head">
            <div>
              <div className="workspace-panel__title">문제 생성 제어</div>
              <div className="workspace-problem-tab__copy">
                파트별 Pack 수를 설정하면 워커가 백그라운드에서 Practice 문제와 Ready Pack을 생성합니다.
              </div>
            </div>
            <div className="workspace-panel__metric">{totalRequested}개 요청</div>
          </div>

          <div className="workspace-problem-controls">
            {partLabels.map((part) => (
              <div key={part.key} className="workspace-problem-control">
                <div className="workspace-problem-control__row">
                  <span>{part.label}</span>
                  <span>{counts[part.key]}</span>
                </div>
                <input
                  type="range"
                  min={0}
                  max={8}
                  value={counts[part.key]}
                  onChange={(event) =>
                    setCounts((current) => ({ ...current, [part.key]: Number(event.target.value) }))
                  }
                />
                <input
                  type="number"
                  min={0}
                  max={20}
                  value={counts[part.key]}
                  onChange={(event) =>
                    setCounts((current) => ({ ...current, [part.key]: Number(event.target.value) || 0 }))
                  }
                  className="workspace-problem-control__input"
                />
              </div>
            ))}
          </div>

          <div className="workspace-problem-tab__actions">
            <button type="button" className="workspace-practice__submit" onClick={() => void handleGenerate()}>
              문제 생성
            </button>
            <button type="button" className="workspace-practice__next" onClick={() => void loadAll()}>
              새로고침
            </button>
          </div>
        </article>

        <article className="workspace-panel">
          <div className="workspace-panel__head">
            <div>
              <div className="workspace-panel__title">워커 상태</div>
              <div className="workspace-problem-tab__copy">{status}</div>
            </div>
            <div className={`workspace-problem-status is-${workerStatus?.state ?? "stopped"}`}>
              {workerStatus?.state ?? "unknown"}
            </div>
          </div>

          <div className="workspace-problem-tab__stats">
            <div className="workspace-problem-stat">
              <div className="workspace-problem-stat__label">PID</div>
              <div className="workspace-problem-stat__value">{workerStatus?.pid ?? "-"}</div>
            </div>
            <div className="workspace-problem-stat">
              <div className="workspace-problem-stat__label">Poll</div>
              <div className="workspace-problem-stat__value">{workerStatus?.poll_interval ?? "-"}</div>
            </div>
            <div className="workspace-problem-stat">
              <div className="workspace-problem-stat__label">Exit</div>
              <div className="workspace-problem-stat__value">{workerStatus?.last_exit_code ?? "-"}</div>
            </div>
          </div>

          <div className="workspace-problem-tab__actions">
            <button type="button" className="workspace-practice__submit" onClick={() => void handleStartWorker()}>
              Worker On
            </button>
            <button type="button" className="workspace-practice__next" onClick={() => void handleStopWorker()}>
              Worker Off
            </button>
          </div>

          <div className="workspace-problem-chip-row">
            {Object.entries(inventory?.stats.practice_items_by_part ?? {}).map(([part, count]) => (
              <div key={part} className="workspace-practice__tag">
                {part.toUpperCase()} Practice {count}
              </div>
            ))}
          </div>

          <div className="workspace-problem-item-list">
            {(inventory?.active_jobs ?? []).slice(0, 4).map((job) => (
              <div key={job.job_id} className="workspace-problem-item">
                <div className="workspace-problem-item__top">
                  <div className="workspace-pack__name">{job.job_type}</div>
                  <div className="workspace-pack__badge is-medium">{job.status}</div>
                </div>
                <div className="workspace-pack__meta">job:{job.job_id.slice(0, 8)}</div>
              </div>
            ))}
          </div>
        </article>
      </div>

      <div className="workspace-problem-grid">
        <article className="workspace-panel">
          <div className="workspace-panel__head">
            <div>
              <div className="workspace-panel__title">Ready Pack</div>
              <div className="workspace-problem-tab__copy">
                {inventory?.stats.total_ready_packs ?? 0}개 준비됨
              </div>
            </div>
            <div className="workspace-panel__metric">page {readyPackPage}</div>
          </div>

          <div className="workspace-pack-list">
            {inventory?.ready_packs.map((pack) => (
              <div key={pack.ready_pack_id} className="workspace-pack">
                <div className="workspace-pack__body">
                  <div className="workspace-pack__name">{pack.title}</div>
                  <div className="workspace-pack__meta">
                    {pack.mode.toUpperCase()} · {new Date(pack.created_at).toLocaleDateString()}
                  </div>
                </div>
                <div className={`workspace-pack__badge is-${pack.difficulty}`}>
                  {difficultyLabel[pack.difficulty] ?? pack.difficulty}
                </div>
              </div>
            ))}
          </div>

          <div className="workspace-problem-tab__actions">
            <button
              type="button"
              className="workspace-practice__next"
              disabled={readyPackPage <= 1}
              onClick={() => setReadyPackPage((current) => Math.max(1, current - 1))}
            >
              이전
            </button>
            <button
              type="button"
              className="workspace-practice__next"
              onClick={() => setReadyPackPage((current) => current + 1)}
            >
              다음
            </button>
          </div>
        </article>

        <article className="workspace-panel">
          <div className="workspace-panel__head">
            <div>
              <div className="workspace-panel__title">Practice 문제 Bank</div>
              <div className="workspace-problem-tab__copy">
                {inventory?.stats.total_practice_items ?? 0}문항 저장됨
              </div>
            </div>
            <div className="workspace-panel__metric">page {practiceItemPage}</div>
          </div>

          <div className="workspace-problem-item-list">
            {inventory?.practice_items.map((item) => (
              <div key={item.item_id} className="workspace-problem-item">
                <div className="workspace-problem-item__top">
                  <div className="workspace-pack__name">{item.part_type.toUpperCase()} · {item.prompt}</div>
                  <div className={`workspace-pack__badge is-${item.difficulty_level}`}>
                    {difficultyLabel[item.difficulty_level] ?? item.difficulty_level}
                  </div>
                </div>
                <div className="workspace-pack__meta">
                  {item.grammar_tag} · {item.vocab_tag ?? "general"} · {item.source}
                </div>
              </div>
            ))}
          </div>

          <div className="workspace-problem-tab__actions">
            <button
              type="button"
              className="workspace-practice__next"
              disabled={practiceItemPage <= 1}
              onClick={() => setPracticeItemPage((current) => Math.max(1, current - 1))}
            >
              이전
            </button>
            <button
              type="button"
              className="workspace-practice__next"
              onClick={() => setPracticeItemPage((current) => current + 1)}
            >
              다음
            </button>
          </div>
        </article>
      </div>
    </section>
  );
}
