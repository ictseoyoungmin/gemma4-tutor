from __future__ import annotations

from collections import Counter

from .schemas import ToeicPracticeItem


TOEIC_ITEMS: list[ToeicPracticeItem] = [
    ToeicPracticeItem(
        item_id="toeic-p5-001",
        part_type="part5",
        difficulty_level="easy",
        question_text="The marketing team will ___ the final brochure before noon.",
        prompt="Choose the best word to complete the sentence.",
        options=["review", "reviews", "reviewed", "reviewing"],
        correct_option="review",
        explanation="After 'will', the base form of the verb is required.",
        grammar_tag="modal_base_form",
        vocab_tag="marketing",
    ),
    ToeicPracticeItem(
        item_id="toeic-p5-002",
        part_type="part5",
        difficulty_level="easy",
        question_text="Ms. Perez is responsible ___ preparing the weekly sales summary.",
        prompt="Choose the best word to complete the sentence.",
        options=["for", "to", "with", "about"],
        correct_option="for",
        explanation="The expression is 'be responsible for' plus a noun or gerund.",
        grammar_tag="preposition_collocation",
        vocab_tag="sales",
    ),
    ToeicPracticeItem(
        item_id="toeic-p5-003",
        part_type="part5",
        difficulty_level="medium",
        question_text="All visitors must present a photo ID upon ___ at the main lobby.",
        prompt="Choose the best word to complete the sentence.",
        options=["arrive", "arrived", "arrival", "arriving"],
        correct_option="arrival",
        explanation="After the preposition 'upon', a noun fits the sentence best here.",
        grammar_tag="noun_form",
        vocab_tag="security",
    ),
    ToeicPracticeItem(
        item_id="toeic-p5-004",
        part_type="part5",
        difficulty_level="medium",
        question_text="The report was delayed because several figures were recorded ___.",
        prompt="Choose the best word to complete the sentence.",
        options=["incorrect", "incorrectly", "incorrectness", "more incorrect"],
        correct_option="incorrectly",
        explanation="The verb 'recorded' is modified by an adverb, so 'incorrectly' is correct.",
        grammar_tag="adverb_form",
        vocab_tag="reporting",
    ),
    ToeicPracticeItem(
        item_id="toeic-p5-005",
        part_type="part5",
        difficulty_level="hard",
        question_text="No sooner ___ the contract signed than the legal team archived the draft versions.",
        prompt="Choose the best word to complete the sentence.",
        options=["had", "has", "was", "did"],
        correct_option="had",
        explanation="The inversion pattern is 'No sooner had + subject + past participle'.",
        grammar_tag="inversion",
        vocab_tag="legal",
    ),
    ToeicPracticeItem(
        item_id="toeic-p5-006",
        part_type="part5",
        difficulty_level="hard",
        question_text="Applicants will be considered for the role provided that all references ___ by Friday.",
        prompt="Choose the best word to complete the sentence.",
        options=["submit", "are submitted", "submitted", "will submit"],
        correct_option="are submitted",
        explanation="The references receive the action, so a passive form is needed.",
        grammar_tag="passive_voice",
        vocab_tag="hiring",
    ),
]


def calculate_recent_accuracy(attempts: list[dict[str, object]]) -> float:
    if not attempts:
        return 0.0
    correct_count = sum(1 for attempt in attempts if attempt["correct"])
    return correct_count / len(attempts)


def infer_recommended_difficulty(attempts: list[dict[str, object]]) -> str:
    accuracy = calculate_recent_accuracy(attempts[:5])
    if not attempts:
        return "medium"
    if len(attempts) == 1:
        return "easy" if accuracy < 1.0 else "medium"
    if accuracy >= 0.8:
        return "hard"
    if accuracy <= 0.5:
        return "easy"
    return "medium"


def derive_weak_tags(attempts: list[dict[str, object]], limit: int = 3) -> list[str]:
    counter: Counter[str] = Counter()
    for attempt in attempts:
        if attempt["correct"]:
            continue
        counter.update([attempt["grammar_tag"]])
        vocab_tag = attempt.get("vocab_tag")
        if vocab_tag:
            counter.update([str(vocab_tag)])
    return [tag for tag, _count in counter.most_common(limit)]


def select_next_item(
    *,
    attempts: list[dict[str, object]],
    part_type: str,
) -> tuple[ToeicPracticeItem, str, list[str], float]:
    weak_tags = derive_weak_tags(attempts)
    recommended_difficulty = infer_recommended_difficulty(attempts)
    recent_accuracy = calculate_recent_accuracy(attempts[:5])
    recent_item_ids = {str(attempt["item_id"]) for attempt in attempts[:3]}

    candidates = [
        item for item in TOEIC_ITEMS if item.part_type == part_type and item.difficulty_level == recommended_difficulty
    ]
    if weak_tags:
        weak_match = [
            item
            for item in candidates
            if item.grammar_tag in weak_tags or (item.vocab_tag is not None and item.vocab_tag in weak_tags)
        ]
        if weak_match:
            candidates = weak_match
    unseen_candidates = [item for item in candidates if item.item_id not in recent_item_ids]
    selected_pool = unseen_candidates or candidates or [item for item in TOEIC_ITEMS if item.part_type == part_type]
    return selected_pool[0], recommended_difficulty, weak_tags, recent_accuracy


def get_item_by_id(item_id: str) -> ToeicPracticeItem | None:
    for item in TOEIC_ITEMS:
        if item.item_id == item_id:
            return item
    return None
