import { useEffect, useMemo, useState } from "react";
import {
  deletePracticeItem,
  deleteReadyPack,
  fetchPracticeItemDetail,
  fetchProblemInventory,
  fetchReadyPackDetail,
  fetchWorkerStatus,
  queueProblemGeneration,
  runHarness,
  startWorker,
  stopWorker,
} from "../../api";
import type {
  HarnessRunResponse,
  PracticeItemDetail,
  ProblemInventoryResponse,
  ReadyPackDetail,
  WorkerStatusResponse,
} from "../../types";

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

const strategyLabel: Record<string, string> = {
  llm: "LLM 생성",
  llm_repair: "LLM Repair",
  seed_fallback: "Seed Fallback",
  llm_invalid_fallback: "검증 실패 Fallback",
  llm_error_fallback: "오류 Fallback",
};

function getStrategyTone(strategy?: string | null) {
  if (strategy === "llm") {
    return "easy";
  }
  if (strategy === "llm_repair") {
    return "medium";
  }
  if (strategy === "llm_invalid_fallback" || strategy === "llm_error_fallback") {
    return "hard";
  }
  return "medium";
}

function getStrategyLabel(strategy?: string | null) {
  if (!strategy) {
    return "미기록";
  }
  return strategyLabel[strategy] ?? strategy;
}

function normalizeValidationErrorKey(error: string) {
  return error.replace(/^item_\d+_/, "");
}

function summarizeValidationErrors(errors: string[]) {
  const counts = new Map<string, number>();
  for (const error of errors) {
    const key = normalizeValidationErrorKey(error);
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  return Array.from(counts.entries())
    .map(([key, count]) => ({ key, count }))
    .sort((left, right) => right.count - left.count || left.key.localeCompare(right.key));
}

export function ProblemTab({ userId }: { userId: string }) {
  const [inventory, setInventory] = useState<ProblemInventoryResponse | null>(null);
  const [workerStatus, setWorkerStatus] = useState<WorkerStatusResponse | null>(null);
  const [harnessResult, setHarnessResult] = useState<HarnessRunResponse | null>(null);
  const [selectedReadyPack, setSelectedReadyPack] = useState<ReadyPackDetail | null>(null);
  const [selectedPracticeItem, setSelectedPracticeItem] = useState<PracticeItemDetail | null>(null);
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
  const queueStatusCounts = useMemo(() => {
    const initial = { queued: 0, running: 0, done: 0, failed: 0 };
    for (const job of inventory?.active_jobs ?? []) {
      if (job.status in initial) {
        initial[job.status as keyof typeof initial] += 1;
      }
    }
    return initial;
  }, [inventory]);
  const queueTotal = queueStatusCounts.queued + queueStatusCounts.running;
  const runningRatio = queueTotal > 0 ? (queueStatusCounts.running / queueTotal) * 100 : 0;
  const queuedRatio = queueTotal > 0 ? (queueStatusCounts.queued / queueTotal) * 100 : 0;
  const failedHarnessCases = harnessResult?.results.filter((result) => !result.passed) ?? [];
  const generationStrategyCounts = useMemo(() => {
    const countsByStrategy: Record<string, number> = {};
    for (const pack of inventory?.ready_packs ?? []) {
      const strategy = pack.generation?.strategy ?? "unknown";
      countsByStrategy[strategy] = (countsByStrategy[strategy] ?? 0) + 1;
    }
    return countsByStrategy;
  }, [inventory]);
  const fallbackReadyPackCount = useMemo(
    () =>
      (inventory?.ready_packs ?? []).filter((pack) => {
        const strategy = pack.generation?.strategy;
        return strategy != null && strategy !== "llm";
      }).length,
    [inventory],
  );
  const selectedReadyPackFailures = selectedReadyPack?.generation?.validation_errors ?? [];
  const selectedReadyPackHarnessPassed = selectedReadyPack?.generation?.harness?.passed;
  const selectedReadyPackFailureSummary = useMemo(
    () => summarizeValidationErrors(selectedReadyPackFailures),
    [selectedReadyPackFailures],
  );
  const failedCandidatePreview = selectedReadyPack?.generation?.candidate_preview;
  const repairCandidatePreview = selectedReadyPack?.generation?.repair_candidate_preview;
  const selectedReadyPackRepairAttempted = selectedReadyPack?.generation?.repair_attempted;
  const selectedReadyPackRepairSuccessCount = selectedReadyPack?.generation?.repair_success_count ?? 0;
  const selectedReadyPackChunkCount = selectedReadyPack?.generation?.chunk_count;
  const selectedReadyPackRequestedItemCount = selectedReadyPack?.generation?.requested_item_count;
  const selectedReadyPackFailedChunkIndex = selectedReadyPack?.generation?.failed_chunk_index;
  const selectedReadyPackFailedChunkSize = selectedReadyPack?.generation?.failed_chunk_size;

  useEffect(() => {
    void loadAll();
  }, [userId, readyPackPage, practiceItemPage]);

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      void loadAll();
    }, 3000);
    return () => window.clearInterval(intervalId);
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

  async function handleRunHarness() {
    try {
      setStatus("하네스를 실행하는 중...");
      const result = await runHarness("asgi");
      setHarnessResult(result);
      setStatus(`하네스 완료 · ${result.passed}/${result.total} passed`);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "하네스 실행에 실패했습니다.");
    }
  }

  async function handleSelectReadyPack(readyPackId: string) {
    try {
      const detail = await fetchReadyPackDetail(userId, readyPackId);
      setSelectedReadyPack(detail);
      setSelectedPracticeItem(null);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Ready Pack 미리보기를 가져오지 못했습니다.");
    }
  }

  async function handleSelectPracticeItem(itemId: string) {
    try {
      const detail = await fetchPracticeItemDetail(userId, itemId);
      setSelectedPracticeItem(detail);
      setSelectedReadyPack(null);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Practice item 미리보기를 가져오지 못했습니다.");
    }
  }

  async function handleDeleteReadyPack(readyPackId: string) {
    try {
      await deleteReadyPack(userId, readyPackId);
      if (selectedReadyPack?.ready_pack_id === readyPackId) {
        setSelectedReadyPack(null);
      }
      await loadAll();
      setStatus("Ready Pack을 삭제했습니다.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Ready Pack 삭제에 실패했습니다.");
    }
  }

  async function handleDeletePracticeItem(itemId: string) {
    try {
      await deletePracticeItem(userId, itemId);
      if (selectedPracticeItem?.item.item_id === itemId) {
        setSelectedPracticeItem(null);
      }
      await loadAll();
      setStatus("Practice 문제를 삭제했습니다.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Practice 문제 삭제에 실패했습니다.");
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
            <button type="button" className="workspace-practice__next" onClick={() => void handleRunHarness()}>
              Harness Run
            </button>
          </div>

          <div className="workspace-problem-chip-row">
            {Object.entries(inventory?.stats.practice_items_by_part ?? {}).map(([part, count]) => (
              <div key={part} className="workspace-practice__tag">
                {part.toUpperCase()} Practice {count}
              </div>
            ))}
            {Object.entries(generationStrategyCounts).map(([strategy, count]) => (
              <div key={strategy} className="workspace-practice__tag">
                {getStrategyLabel(strategy)} {count}
              </div>
            ))}
          </div>

          <div className="workspace-queue-visual">
            <div className="workspace-queue-visual__item">
              <div className="workspace-queue-visual__row">
                <span>Queue</span>
                <span>{queueTotal}</span>
              </div>
              <div className="workspace-queue-visual__bar is-stacked">
                <div
                  className="workspace-queue-visual__fill is-running"
                  style={{ width: `${runningRatio}%` }}
                />
                <div
                  className="workspace-queue-visual__fill is-queued"
                  style={{ width: `${queuedRatio}%` }}
                />
              </div>
              <div className="workspace-queue-visual__legend">
                <span className="workspace-queue-legend is-running">Running {queueStatusCounts.running}</span>
                <span className="workspace-queue-legend is-queued">Queued {queueStatusCounts.queued}</span>
              </div>
            </div>

            <div className="workspace-queue-visual__item">
              <div className="workspace-queue-visual__row">
                <span>Fallback Packs</span>
                <span>{fallbackReadyPackCount}</span>
              </div>
              <div className="workspace-queue-visual__bar">
                <div
                  className="workspace-queue-visual__fill is-failed"
                  style={{
                    width: `${Math.min(
                      inventory?.stats.total_ready_packs
                        ? (fallbackReadyPackCount / inventory.stats.total_ready_packs) * 100
                        : 0,
                      100,
                    )}%`,
                  }}
                />
              </div>
              <div className="workspace-queue-visual__legend">
                <span className="workspace-queue-legend is-queued">Worker Failed Jobs {queueStatusCounts.failed}</span>
              </div>
            </div>
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

          {harnessResult ? (
            <div className="workspace-problem-item-list">
              {harnessResult.results.map((result) => (
                <div key={result.case_id} className="workspace-problem-item">
                  <div className="workspace-problem-item__top">
                    <div className="workspace-pack__name">{result.case_id}</div>
                    <div className={`workspace-pack__badge ${result.passed ? "is-easy" : "is-hard"}`}>
                      {result.passed ? "pass" : "fail"}
                    </div>
                  </div>
                  <div className="workspace-pack__meta">
                    {result.status_code} · {Math.round(result.elapsed_ms)}ms
                  </div>
                </div>
              ))}
            </div>
          ) : null}

          {failedHarnessCases.length ? (
            <div className="workspace-problem-failure-list">
              {failedHarnessCases.map((result) => (
                <div key={`${result.case_id}-detail`} className="workspace-problem-failure">
                  <div className="workspace-problem-failure__title">{result.case_id} 실패</div>
                  <div className="workspace-problem-failure__copy">{result.body_preview || "응답 본문 미리보기가 없습니다."}</div>
                </div>
              ))}
            </div>
          ) : null}
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
              <div
                key={pack.ready_pack_id}
                className={`workspace-pack${selectedReadyPack?.ready_pack_id === pack.ready_pack_id ? " is-active" : ""}`}
              >
                <div className="workspace-pack__body">
                  <button
                    type="button"
                    className="workspace-problem-link"
                    onClick={() => void handleSelectReadyPack(pack.ready_pack_id)}
                  >
                    <div className="workspace-pack__name">{pack.title}</div>
                  </button>
                  <div className="workspace-pack__meta">
                    {pack.mode.toUpperCase()} · {new Date(pack.created_at).toLocaleDateString()}
                  </div>
                  <div className="workspace-pack__meta">
                    {getStrategyLabel(pack.generation?.strategy)} · validation {pack.generation?.validation_errors.length ?? 0}
                  </div>
                </div>
                <div className="workspace-problem-row-actions">
                  <div className={`workspace-pack__badge is-${getStrategyTone(pack.generation?.strategy)}`}>
                    {getStrategyLabel(pack.generation?.strategy)}
                  </div>
                  <div className={`workspace-pack__badge is-${pack.difficulty}`}>
                    {difficultyLabel[pack.difficulty] ?? pack.difficulty}
                  </div>
                  <button
                    type="button"
                    className="workspace-problem-delete"
                    onClick={() => void handleDeleteReadyPack(pack.ready_pack_id)}
                  >
                    삭제
                  </button>
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
                  <button
                    type="button"
                    className="workspace-problem-link"
                    onClick={() => void handleSelectPracticeItem(item.item_id)}
                  >
                    <div className="workspace-pack__name">{item.part_type.toUpperCase()} · {item.prompt}</div>
                  </button>
                  <div className="workspace-problem-row-actions">
                    <div className={`workspace-pack__badge is-${item.difficulty_level}`}>
                      {difficultyLabel[item.difficulty_level] ?? item.difficulty_level}
                    </div>
                    <button
                      type="button"
                      className="workspace-problem-delete"
                      onClick={() => void handleDeletePracticeItem(item.item_id)}
                    >
                      삭제
                    </button>
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

      {(selectedReadyPack || selectedPracticeItem) ? (
        <article className="workspace-panel workspace-problem-preview">
          <div className="workspace-panel__head">
            <div>
              <div className="workspace-panel__title">문제 미리보기</div>
              <div className="workspace-problem-tab__copy">
                문제 탭에서 선택한 생성 결과를 바로 확인할 수 있습니다.
              </div>
            </div>
          </div>

          {selectedReadyPack ? (
            <div className="workspace-problem-preview__body">
              <div className="workspace-ready-pack__title-row">
                <div>
                  <div className="workspace-ready-pack__title">{selectedReadyPack.pack.title}</div>
                  <div className="workspace-ready-pack__meta-line">
                    {selectedReadyPack.pack.mode} · {difficultyLabel[selectedReadyPack.pack.difficulty] ?? selectedReadyPack.pack.difficulty} · {selectedReadyPack.pack.items.length}문항
                  </div>
                  <div className="workspace-ready-pack__meta-line">
                    {getStrategyLabel(selectedReadyPack.generation?.strategy)} · validation {selectedReadyPackFailures.length} · harness{" "}
                    {selectedReadyPackHarnessPassed === true ? "pass" : selectedReadyPackHarnessPassed === false ? "fail" : "-"}
                  </div>
                  <div className="workspace-ready-pack__meta-line">
                    chunk {selectedReadyPackChunkCount ?? "-"} · requested {selectedReadyPackRequestedItemCount ?? selectedReadyPack.pack.items.length}문항 · repair{" "}
                    {selectedReadyPackRepairAttempted ? `attempted (${selectedReadyPackRepairSuccessCount} success)` : "not used"}
                  </div>
                </div>
              </div>
              {selectedReadyPack.generation ? (
                <div className="workspace-problem-failure-list">
                  <div className="workspace-problem-failure">
                    <div className="workspace-problem-failure__title">Generation Metadata</div>
                    <div className="workspace-problem-failure__copy">
                      strategy: {selectedReadyPack.generation.strategy}
                      {selectedReadyPack.generation.error ? ` · error: ${selectedReadyPack.generation.error}` : ""}
                      {selectedReadyPackFailedChunkIndex ? ` · failed chunk: ${selectedReadyPackFailedChunkIndex}` : ""}
                      {selectedReadyPackFailedChunkSize ? ` · failed chunk size: ${selectedReadyPackFailedChunkSize}` : ""}
                    </div>
                  </div>
                  {selectedReadyPackFailureSummary.map((entry) => (
                    <div key={entry.key} className="workspace-problem-failure">
                      <div className="workspace-problem-failure__title">validation summary</div>
                      <div className="workspace-problem-failure__copy">
                        {entry.key}: {entry.count}
                      </div>
                    </div>
                  ))}
                  {selectedReadyPackFailures.slice(0, 3).map((failure) => (
                    <div key={failure} className="workspace-problem-failure">
                      <div className="workspace-problem-failure__title">validation failure</div>
                      <div className="workspace-problem-failure__copy">{failure}</div>
                    </div>
                  ))}
                </div>
              ) : null}
              {failedCandidatePreview ? (
                <div className="workspace-ready-pack__items">
                  <div className="workspace-ready-pack__title-row">
                    <div>
                      <div className="workspace-ready-pack__title">Failed LLM Attempt</div>
                      <div className="workspace-ready-pack__meta-line">
                        {failedCandidatePreview.mode} · {difficultyLabel[failedCandidatePreview.difficulty] ?? failedCandidatePreview.difficulty} · preview {failedCandidatePreview.items.length}/{failedCandidatePreview.item_count}문항
                      </div>
                    </div>
                  </div>
                  {failedCandidatePreview.items.map((item, index) => (
                    <div key={`candidate-preview-${index}`} className="workspace-ready-pack__item">
                      <div className="workspace-ready-pack__question">Q{index + 1}. {item.prompt}</div>
                      {item.choices.length ? (
                        <div className="workspace-ready-pack__choices">
                          {item.choices.map((choice) => (
                            <div key={`${index}-${choice}`} className="workspace-ready-pack__choice">
                              {choice}
                            </div>
                          ))}
                        </div>
                      ) : null}
                      <div className="workspace-ready-pack__feedback">answer: {item.answer}</div>
                      <div className="workspace-ready-pack__feedback">{item.explanation}</div>
                    </div>
                  ))}
                </div>
              ) : null}
              {repairCandidatePreview ? (
                <div className="workspace-ready-pack__items">
                  <div className="workspace-ready-pack__title-row">
                    <div>
                      <div className="workspace-ready-pack__title">Repair Attempt</div>
                      <div className="workspace-ready-pack__meta-line">
                        {repairCandidatePreview.mode} · {difficultyLabel[repairCandidatePreview.difficulty] ?? repairCandidatePreview.difficulty} · preview {repairCandidatePreview.items.length}/{repairCandidatePreview.item_count}문항
                      </div>
                    </div>
                  </div>
                  {repairCandidatePreview.items.map((item, index) => (
                    <div key={`repair-preview-${index}`} className="workspace-ready-pack__item">
                      <div className="workspace-ready-pack__question">Q{index + 1}. {item.prompt}</div>
                      {item.choices.length ? (
                        <div className="workspace-ready-pack__choices">
                          {item.choices.map((choice) => (
                            <div key={`${index}-repair-${choice}`} className="workspace-ready-pack__choice">
                              {choice}
                            </div>
                          ))}
                        </div>
                      ) : null}
                      <div className="workspace-ready-pack__feedback">answer: {item.answer}</div>
                      <div className="workspace-ready-pack__feedback">{item.explanation}</div>
                    </div>
                  ))}
                </div>
              ) : null}
              <div className="workspace-ready-pack__items">
                <div className="workspace-ready-pack__title-row">
                  <div>
                    <div className="workspace-ready-pack__title">
                      {selectedReadyPack.generation?.strategy === "llm" || selectedReadyPack.generation?.strategy === "llm_repair"
                        ? "Saved Final Pack"
                        : "Saved Fallback Pack"}
                    </div>
                    <div className="workspace-ready-pack__meta-line">
                      UI에 저장된 최종 Ready Pack 미리보기입니다.
                    </div>
                  </div>
                </div>
                {selectedReadyPack.pack.items.slice(0, 5).map((item, index) => (
                  <div key={`${selectedReadyPack.ready_pack_id}-${index}`} className="workspace-ready-pack__item">
                    <div className="workspace-ready-pack__question">Q{index + 1}. {item.prompt}</div>
                    {item.choices.length ? (
                      <div className="workspace-ready-pack__choices">
                        {item.choices.map((choice) => (
                          <div key={choice} className="workspace-ready-pack__choice">
                            {choice}
                          </div>
                        ))}
                      </div>
                    ) : null}
                    <div className="workspace-ready-pack__feedback">{item.explanation}</div>
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          {selectedPracticeItem ? (
            <div className="workspace-problem-preview__body">
              <div className="workspace-ready-pack__title-row">
                <div>
                  <div className="workspace-ready-pack__title">{selectedPracticeItem.item.part_type.toUpperCase()} Practice</div>
                  <div className="workspace-ready-pack__meta-line">
                    {difficultyLabel[selectedPracticeItem.item.difficulty_level] ?? selectedPracticeItem.item.difficulty_level} · {selectedPracticeItem.source}
                  </div>
                </div>
              </div>
              <div className="workspace-ready-pack__item">
                <div className="workspace-practice__prompt">{selectedPracticeItem.item.prompt}</div>
                <div className="workspace-practice__question">{selectedPracticeItem.item.question_text}</div>
                <div className="workspace-practice__options">
                  {selectedPracticeItem.item.options.map((option, index) => (
                    <div key={option} className={`workspace-practice__option${selectedPracticeItem.item.correct_option === option ? " is-correct" : ""}`}>
                      <span className="workspace-practice__option-label">{String.fromCharCode(65 + index)}</span>
                      <span>{option}</span>
                    </div>
                  ))}
                </div>
                <div className="workspace-practice__result is-correct">
                  <div className="workspace-practice__result-title">정답: {selectedPracticeItem.item.correct_option}</div>
                  <div className="workspace-practice__result-copy">{selectedPracticeItem.item.explanation}</div>
                </div>
              </div>
            </div>
          ) : null}
        </article>
      ) : null}
    </section>
  );
}
