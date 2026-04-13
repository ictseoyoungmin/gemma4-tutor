import { useEffect, useState } from "react";
import { fetchNextToeicItem, submitToeicAnswer } from "../../api";
import type { ToeicAnswerResponse, ToeicNextResponse } from "../../types";

const difficultyLabel: Record<"easy" | "medium" | "hard", string> = {
  easy: "쉬움",
  medium: "보통",
  hard: "어려움",
};

export function PracticePanel({ userId }: { userId: string }) {
  const [practice, setPractice] = useState<ToeicNextResponse | null>(null);
  const [selectedOption, setSelectedOption] = useState("");
  const [result, setResult] = useState<ToeicAnswerResponse | null>(null);
  const [status, setStatus] = useState("문제를 불러오는 중...");
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [startedAt, setStartedAt] = useState<number | null>(null);

  useEffect(() => {
    void loadNextItem();
  }, [userId]);

  async function loadNextItem() {
    try {
      setIsLoading(true);
      setStatus("문제를 불러오는 중...");
      const next = await fetchNextToeicItem(userId);
      setPractice(next);
      setSelectedOption("");
      setResult(null);
      setStartedAt(Date.now());
      setStatus("문제 준비 완료");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "문제를 가져오지 못했습니다.");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleSubmit() {
    if (!practice || !selectedOption || isSubmitting) return;

    try {
      setIsSubmitting(true);
      setStatus("답안을 확인하는 중...");
      const elapsed = startedAt ? Date.now() - startedAt : 0;
      const response = await submitToeicAnswer(
        userId,
        practice.item.item_id,
        selectedOption,
        elapsed,
      );
      setResult(response);
      setStatus(response.correct ? "정답입니다" : "해설을 확인해보세요");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "답안을 제출하지 못했습니다.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="workspace-panel workspace-practice">
      <div className="workspace-panel__head">
        <div>
          <div className="workspace-panel__title">TOEIC Part 5 Practice</div>
          <div className="workspace-practice__subcopy">단일 문항 풀이 → 즉시 해설 → 다음 난이도 추천</div>
        </div>
        <div className="workspace-practice__meta">
          <span className={`workspace-practice__difficulty is-${practice?.recommended_difficulty ?? "medium"}`}>
            {difficultyLabel[practice?.recommended_difficulty ?? "medium"]}
          </span>
          <span className="workspace-panel__metric">{status}</span>
        </div>
      </div>

      {practice ? (
        <div className="workspace-practice__body">
          <div className="workspace-practice__prompt">{practice.item.prompt}</div>
          <div className="workspace-practice__question">{practice.item.question_text}</div>

          <div className="workspace-practice__options">
            {practice.item.options.map((option, index) => {
              const optionLabel = String.fromCharCode(65 + index);
              const isSelected = selectedOption === option;
              const isCorrect = result?.correct_option === option;
              const isWrongSelection = Boolean(result && isSelected && !result.correct);
              return (
                <button
                  key={option}
                  type="button"
                  className={[
                    "workspace-practice__option",
                    isSelected ? "is-selected" : "",
                    result && isCorrect ? "is-correct" : "",
                    isWrongSelection ? "is-wrong" : "",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                  onClick={() => setSelectedOption(option)}
                  disabled={Boolean(result)}
                >
                  <span className="workspace-practice__option-label">{optionLabel}</span>
                  <span>{option}</span>
                </button>
              );
            })}
          </div>

          <div className="workspace-practice__tags">
            <span className="workspace-practice__tag">grammar: {practice.item.grammar_tag}</span>
            {practice.item.vocab_tag ? (
              <span className="workspace-practice__tag">vocab: {practice.item.vocab_tag}</span>
            ) : null}
            <span className="workspace-practice__tag">
              recent accuracy: {Math.round(practice.recent_accuracy * 100)}%
            </span>
          </div>

          {result ? (
            <div className={`workspace-practice__result${result.correct ? " is-correct" : " is-wrong"}`}>
              <div className="workspace-practice__result-title">
                {result.correct ? "정답입니다." : `오답입니다. 정답은 ${result.correct_option}`}
              </div>
              <div className="workspace-practice__result-copy">{result.explanation}</div>
              <div className="workspace-practice__result-foot">
                <span>다음 추천 난이도: {difficultyLabel[result.recommended_difficulty]}</span>
                {result.weak_tags.length ? <span>취약 태그: {result.weak_tags.join(", ")}</span> : null}
              </div>
            </div>
          ) : null}

          <div className="workspace-practice__actions">
            <button
              type="button"
              className="workspace-practice__submit"
              onClick={() => void handleSubmit()}
              disabled={!selectedOption || isSubmitting || isLoading || Boolean(result)}
            >
              {isSubmitting ? "채점 중" : "답안 제출"}
            </button>
            <button
              type="button"
              className="workspace-practice__next"
              onClick={() => void loadNextItem()}
              disabled={isLoading || isSubmitting}
            >
              다음 문제
            </button>
          </div>
        </div>
      ) : (
        <div className="workspace-practice__empty">문제를 준비하지 못했습니다. 다시 시도해보세요.</div>
      )}
    </section>
  );
}
