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

- `completed`

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

Completed work:

- Added a recommended-time indicator to the study bar.
- Added a visible timer on/off toggle in the focused solving UI.
- Kept study progress intact while allowing the visible timer to pause.

### Slice 5. Tutor drawer shell

Status:

- `completed`

Scope:

- Convert the left tutor chat panel into a drawer.
- Open/close it with `>` / `<` buttons.
- Keep a handle visible so it can be reopened even when collapsed.

Implementation detail:

- Port the reference's `.panel.left` and `.drawer-btn.left-btn` structure into the current React/CSS codebase.
- Preserve collapse state in local state or in persisted workspace state.

Acceptance:

- The tutor panel collapses and reopens smoothly.[^testable-acceptance]

Completed work:

- Added drawer-style open/close behavior for the left tutor panel.
- Added top-positioned handles that remain visible in collapsed state.
- Auto-collapsed the side panels when entering focused solving mode.

### Slice 6. Tutor drawer resize

Status:

- `completed`

Scope:

- Allow the user to resize the tutor panel horizontally with the mouse.

Implementation detail:

- Add a resizer handle.
- Control width state through pointer-event-based dragging.
- Apply minimum/maximum width limits.[^resize-order]

Acceptance:

- The user can adjust the tutor panel width left and right.
- The panel does not become too narrow or too wide.

Completed work:

- Added pointer-driven horizontal resize for both side panels.
- Added visible vertical resize handles and resize cursor feedback.
- Reduced drag heaviness by disabling transitions during active resizing.

### Slice 7. Chat transcript scrolling and anchored composer

Status:

- `completed`

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

Completed work:

- Changed the tutor panel so the transcript is the only scrolling region.
- Kept the status bar and composer anchored at the bottom.
- Added automatic scroll-to-bottom behavior for accumulated chat messages.

### Slice 8. Compact model picker near composer actions

Status:

- `completed`

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

Completed work:

- Removed the large model selector row from the tutor header.
- Added a compact model icon button next to the composer actions.
- Added an inline popover-style model picker near the send flow.

### Slice 9. Image upload action from clip button

Status:

- `completed`

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

Completed work:

- Connected the clip button to a hidden image file input.
- Added single-image attachment state in the chat composer.
- Added an attachment chip with remove action and helper-text feedback.

### Slice 10. Right status drawer

Status:

- `completed`

Scope:

- Make the right status panel openable and closable as a drawer.
- Improve visibility and usability of learning stats/state.

Implementation detail:

- Apply the reference's `.panel.right` and `.drawer-btn.right-btn` pattern.
- Preserve collapse state.

Acceptance:

- The right status panel can be collapsed and reopened.

Completed work:

- Added drawer-style open/close behavior for the right status panel.
- Added a persistent top handle so it can be reopened after collapse.
- Applied the same focused-study auto-collapse behavior used by the tutor drawer.

### Slice 11. Visual polish and responsive pass

Status:

- `completed`

Scope:

- Refine the full study UI to match the reference tone.
- Verify drawer, resizer, and question-stage layouts under narrow widths.
- Check keyboard accessibility and focus states.

Implementation detail:

- Refine spacing, bar, progress, question card, and result card styles.
- Define fallback rules for mobile/narrow desktop widths.

Acceptance:

- The main flow is stable on desktop, and the layout does not break at narrower widths.

Completed work:

- Added keyboard-visible focus outlines for interactive controls across the workspace shell.
- Added responsive layout adjustments for the study screen, result summary, timer bar, and chat composer under narrower widths.
- Reduced narrow-width breakage by collapsing key grid layouts into single-column fallbacks.
- Applied additional visual polish to the focused study card and popover surfaces.

### Slice 12. Shared study-stage transition shell

Status:

- `completed`

Scope:

- Reuse the same focused study-stage structure for both `TOEIC Part 5 Practice` and `Ready Pack 실행`.
- Reduce differences in stage transition behavior between the two launcher buttons.

Implementation detail:

- Extract a shared study-shell component for the top study bar, progress handling, and centered question stage.
- Move both practice and ready-pack flows onto the shared shell.
- Apply focused side-panel collapse consistently when either study module is active.

Acceptance:

- Both launcher buttons enter a visually consistent focused study stage.
- Shared transition scaffolding is reused instead of duplicating separate stage layouts.

Completed work:

- Added a shared `StudyStageShell` component for the common focused study layout.
- Moved `ReadyPack` study/result screens onto the shared shell.
- Moved `TOEIC Part 5 Practice` onto the same focused shell and focus-mode behavior.
- Made both module entries clear surrounding workspace context in a more consistent way.

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
