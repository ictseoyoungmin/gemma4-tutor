# 2026-04-21 UI Study Workspace Slice Plan

## Background

The current workspace UI has gradually connected some features, but it still lacks a complete learner flow where a user selects a problem set, enters the solving screen, submits answers, and reviews the results.

Reference:

- [.reference/ui_practice/learner_workspace_v3.html](/home/ubuntu/gemma_tutor_edge/.reference/ui_practice/learner_workspace_v3.html)

The goal of this UI task is to carry over the core structure of the reference above, while adapting it into the current React-based workspace with more mature behavior.

## Product Requirements

Key requirements to implement:

- When the user clicks `Solve Problem` on a problem card, the UI should transition from the workspace list view to the actual solving view.
- In exam-solving mode, the user should complete all questions first, then submit once and see the grading result.
- On the result screen, the user should be able to access the correct answer, the user's choice, and the explanation for each item.
- The recommended-time timer should support an on/off toggle.[^timer-policy]
- The tutor chat panel should use a drawer structure that opens and closes with `>` / `<` buttons.
- The tutor chat panel should support horizontal resizing with the mouse.
- Even when chat messages accumulate, the input box should remain fixed at the bottom, and only the conversation content should scroll upward.
- The model selection UI should be redesigned as a compact icon-drawer pattern near the composer.
- The clip button next to the send button should be connected to a real image upload event.
- The right-side status panel should also be openable and closable as a drawer.

## Design Direction

Actively reflect the following elements from the reference:

- the screen transition structure between `workspace` and `study`
- the combination of top study bar + progress bar + question stage
- drawer buttons for the left and right panels
- a bottom-anchored chat composer structure

Additional improvements:

- Do not force short-form practice and full exam solving into the same component; separate the session state.
- Make the result screen a dedicated reviewable state rather than a simple alert/summary.[^result-phase]
- Preserve the left/right panel collapse states and widths as user-controlled UI state.[^ui-pref-state]

## Current Gaps

Current shortcomings:

- The dedicated transition into a solving screen after problem selection is weak.
- The in-progress solving state and post-submission result state are not clearly separated.
- The layout between the chat composer and accumulated messages is not stable.
- The model selection UI takes up too much space.
- The tutor panel and the right status panel do not yet provide a complete drawer UX.
- The upload button is not connected to a real file-selection event.

## Proposed Slice Plan

### Slice 1. Study session routing and view state

Status:

- `completed`

Scope:

- Create a study-session state when the user clicks `Solve Problem` on a problem card.
- Transition from the workspace list view to the study view.
- Support `back` behavior to return to the list view.

Implementation detail:

- Add `viewMode: "workspace" | "study" | "result"` to `WorkspaceMain.tsx` or to the upper-level workspace state component.[^viewmode-split]
- Store the selected ready-pack detail and the current solving-session state in separate store/state.
- Convert the reference's `#workspace` / `#study` switching structure into React component state.

Acceptance:

- After clicking a problem card, the actual solving screen opens.
- When the user navigates back, the original list/selection state is preserved.

Completed work:

- Added `workspace | study | result` view state to the Ready Pack solving flow.
- Reworked the Ready Pack launcher so the list view and the solving screen are visually separated.
- Preserved selected-pack highlighting when returning from the solving screen to the list.

### Slice 2. Practice vs exam solving flow

Status:

- `completed`

Scope:

- Separate practice flow and exam flow.
- In exam flow, allow submission only after all questions are completed.
- Manage question navigation state, unanswered state, and submission eligibility state.

Implementation detail:

- Add `answersByItemId`, `currentIndex`, `isSubmitted`, and `mode` to the session state.[^session-reducer]
- In exam mode, allow only question navigation and do not reveal the correct answer immediately.
- Hide explanations/correct answers before submission.

Acceptance:

- The user can solve all questions and submit at the end.
- Before submission, correct answers and explanations are not visible.

Completed work:

- Added explicit `practice` and `exam` start actions per Ready Pack.
- Added per-session answer state, current question index, and question navigation state.
- Enforced one-shot submission only after all answers are filled in exam mode.
- Kept explanations and correct answers hidden before submission in exam mode.
- Added immediate reveal behavior for practice mode after a choice is selected.

### Slice 3. Result and review screen

Status:

- `completed`

Scope:

- After submission, show score summary, correct/incorrect counts, and the result relative to recommended time.
- Allow access to the correct answer, the user's choice, and the explanation for each item.
- Allow per-item navigation in review mode.

Implementation detail:

- Add either a dedicated `result` view or a `submitted` stage inside `study`.[^result-phase]
- Show `correct / incorrect / unanswered` status in the question list.
- Reuse either a detailed review panel or the same question-stage UI.

Acceptance:

- After submission, the total score and per-question results are visible.
- For each question, the user can review the correct answer and explanation.

Completed work:

- Added a dedicated result/review screen with summary cards for score, correct, incorrect, and unanswered counts.
- Added per-question review navigation with `correct / wrong / unanswered` visual state.
- Exposed the user's selected answer, the correct answer, explanation, and feedback for each question.
- Reused the study question stage as a review surface after submission.

### Slice 4. Recommended timer with on/off toggle

Status:

- `pending`

Scope:

- Show a recommended-time timer.
- Provide a timer on/off switch.
- Keep recommended-time information available even when the timer is off.

Implementation detail:

- Add a timer toggle to the study bar.
- Keep `timerEnabled`, `startedAt`, and `elapsedMs` in session state.[^timer-policy]
- When off, stop live ticking and show either a static display or hide it.

Acceptance:

- The user can turn the timer on and off.
- The solving state remains intact even when the timer is turned off.

### Slice 5. Tutor drawer shell

Status:

- `pending`

Scope:

- Convert the left tutor chat panel into a drawer.
- Open/close it with `>` / `<` buttons.
- Keep a handle visible so it can be reopened even when collapsed.

Implementation detail:

- Port the reference's `.panel.left` and `.drawer-btn.left-btn` structure into the current React/CSS codebase.
- Preserve collapse state in local state or in persisted workspace state.

Acceptance:

- The tutor panel collapses and reopens smoothly.[^testable-acceptance]

### Slice 6. Tutor drawer resize

Status:

- `pending`

Scope:

- Allow the user to resize the tutor panel horizontally with the mouse.

Implementation detail:

- Add a resizer handle.
- Control width state through pointer-event-based dragging.
- Apply minimum/maximum width limits.[^resize-order]

Acceptance:

- The user can adjust the tutor panel width left and right.
- The panel does not become too narrow or too wide.

### Slice 7. Chat transcript scrolling and anchored composer

Status:

- `pending`

Scope:

- Make only the message list scroll.
- Keep the input box fixed at the bottom.
- When new messages accumulate, the conversation stacks upward without pushing the input box away.

Implementation detail:

- Split the layout into `header / transcript / composer`.
- Apply `overflow-y: auto` only to the transcript region.
- Add an automatic scroll-to-bottom policy for new messages.[^autoscroll-policy]

Acceptance:

- Even in long conversations, the input box stays in place.
- As messages accumulate, only the transcript scrolls upward.

### Slice 8. Compact model picker near composer actions

Status:

- `pending`

Scope:

- Replace the existing model selector with a space-efficient icon-button drawer.
- Add a model icon button next to the clip button and send button.
- Show a model list drawer/popover when clicked.

Implementation detail:

- Rearrange the composer action row.
- Group the model button, clip button, and send button together.
- Show the selected model as an icon, short label, or tooltip.

Acceptance:

- On the default screen, the model selector occupies almost no space.
- When clicked, the model list opens and can be selected.

### Slice 9. Image upload action from clip button

Status:

- `pending`

Scope:

- Connect the clip button to a real file-upload input.
- Establish a base flow where an image can be attached together with a chat input.

Implementation detail:

- Connect a hidden file input.
- Define allowed formats and preview policy.
- Start with single-image upload first.[^attachments-array]

Acceptance:

- Clicking the clip button opens the file picker.
- The selected image is reflected as an attached item.

### Slice 10. Right status drawer

Status:

- `pending`

Scope:

- Make the right status panel openable and closable as a drawer.
- Improve visibility and usability of learning stats/state.

Implementation detail:

- Apply the reference's `.panel.right` and `.drawer-btn.right-btn` pattern.
- Preserve collapse state.

Acceptance:

- The right status panel can be collapsed and reopened.

### Slice 11. Visual polish and responsive pass

Status:

- `pending`

Scope:

- Refine the full study UI to match the reference tone.
- Verify drawer, resizer, and question-stage layouts under narrow widths.
- Check keyboard accessibility and focus states.

Implementation detail:

- Refine spacing, bar, progress, question card, and result card styles.
- Define fallback rules for mobile/narrow desktop widths.

Acceptance:

- The main flow is stable on desktop, and the layout does not break at narrower widths.

## State Model Draft

Core state draft required before implementation:

- `workspaceViewMode`
- `selectedPackId`
- `studySession`
- `studySession.currentIndex`
- `studySession.answersByItemId`
- `studySession.startedAt`
- `studySession.elapsedMs`
- `studySession.timerEnabled`
- `studySession.submittedAt`
- `studySession.resultSummary`
- `leftDrawerOpen`
- `leftDrawerWidth`
- `rightDrawerOpen`
- `modelPickerOpen`
- `chatAttachment`[^attachments-array]

## Suggested Execution Order

Recommended implementation order:

1. Slice 1
2. Slice 2
3. Slice 3
4. Slice 4
5. Slice 5
6. Slice 7
7. Slice 8
8. Slice 9
9. Slice 10
10. Slice 6
11. Slice 11

Reason for this order:

- First, the actual study flow must be completed so the UI becomes functionally meaningful.
- Next, improving the chat drawer and status panels reduces implementation conflicts.
- Resize behavior is safer to add after the drawer structure becomes stable.[^resize-order]

## Notes

- The exam result screen should not be just a simple score card; it should include an entry point into review mode.
- The timer is a guidance tool rather than a strict constraint, so on/off support is required.
- For the chat drawer, actual usability depends not only on open/close behavior, but especially on transcript scrolling and a fixed composer.
- The model picker should be much more compact than the current version, and an icon-button-based pattern is appropriate.

---

[^timer-policy]: Agent note: before implementation, decide whether the toggle hides only the live display or also pauses elapsed-time measurement. For exam/history consistency, continuing measurement while hiding the display is often safer than stopping time itself.

[^result-phase]: Agent note: avoid leaving this ambiguous. A robust structure is often `workspace | study` at the top level, with a study-session phase such as `solving | submitted | reviewing` inside the session state. That usually reduces transition bugs.

[^ui-pref-state]: Agent note: panel open/close state and panel width are better treated as UI preference state rather than core study-session state. This keeps domain state and layout state from getting mixed together.

[^viewmode-split]: Agent note: `viewMode: "workspace" | "study" | "result"` is workable, but may later overlap with study-internal phases. If the current code already has room for nested state, prefer separating top-level route/view state from session phase state.

[^session-reducer]: Agent note: the solving flow, submission flow, and review flow are tightly coupled. A reducer or small state-machine shape for `studySession` will likely be more stable than scattered `useState` updates across multiple components.

[^testable-acceptance]: Agent note: acceptance criteria should ideally be testable in DOM/UI terms. For example: collapsed state shows reopen handle, toggle button reopens panel, and previous width is restored after reopening.

[^resize-order]: Agent note: resize can remain later in execution order, but the panel layout should still be designed early enough that adding drag-resize does not require reworking the drawer shell structure.

[^autoscroll-policy]: Agent note: define the autoscroll rule explicitly. A common policy is: autoscroll only when the user is already near the bottom; otherwise preserve the user's scroll position while new messages arrive.

[^attachments-array]: Agent note: even if v1 supports only a single image, consider representing attachments as a list/array in state from the start. That avoids unnecessary refactoring when multi-attachment support is introduced later.
