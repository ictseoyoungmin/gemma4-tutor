# 2026-04-22 Prioritized Workspace Follow-up Slices

## Prioritization Principle

The priorities below are ordered by:

- direct learner-facing impact
- functional completeness of the current product
- reduction of UX confusion
- mobile web usability, especially on narrow screens and touch devices

## Slice 1. Real Image Attachment Learning Flow

Priority:

- `P0`

Why this comes first:

- The UI already lets the learner pick an image, but the selected file was not actually sent to the backend.
- This creates a broken expectation at the most visible tutor interaction point.
- Fixing this closes a core product gap and improves both desktop and mobile web usage immediately.

Scope:

- Send the attached image to the backend instead of keeping it as UI-only state.
- Reuse the existing `/v1/image/analyze` backend flow.
- Preserve model selection when sending image-based tutor requests.
- Make the attachment and send actions usable on mobile screens.

Mobile web notes:

- Attachment chips must wrap cleanly instead of overflowing.
- Touch targets for attach/model/send actions should remain comfortable on narrow screens.
- The composer should keep working when the viewport width is constrained.

Status:

- `completed`

Planned deliverables:

- frontend API helper for multipart image upload
- backend support for `model_name` on image analysis requests
- tutor chat panel integration for image-learning responses
- small mobile-friendly composer/attachment refinements
- regression coverage for the image analysis API contract

Completed work:

- Added multipart image upload support in the web API layer for tutor chat.
- Extended `/v1/image/analyze` to accept `model_name` and pass it through to the image-analysis service.
- Connected tutor chat image attachments to the real backend image-learning flow.
- Rendered image-learning responses inside the existing tutor transcript with follow-up suggestions.
- Improved mobile web usability by allowing attachment wrapping and enlarging touch targets for composer actions on narrow screens.
- Added regression coverage for the image analysis route contract and verified the frontend build.

## Slice 2. Smart Transcript Auto-scroll Policy

Priority:

- `P1`

Why this is next:

- Long conversations become hard to review because the panel always jumps to the bottom.
- This is especially disruptive on mobile web where vertical space is limited.

Scope:

- Auto-scroll only when the learner is already near the bottom.
- Preserve the scroll position when the learner is reading earlier messages.
- Keep the bottom-anchored composer behavior intact.

Mobile web notes:

- Scroll lock and jumpiness are more noticeable on small screens.
- The policy should be tested with touch scrolling behavior in mind.

Status:

- `completed`

Completed work:

- Replaced unconditional transcript auto-scroll with a near-bottom policy.
- Preserved the learner's scroll position while reading older messages.
- Re-enabled bottom sticking when the learner actively sends a new message, so their own message and the next reply remain visible.
- Kept the change lightweight so it behaves consistently on both desktop and mobile web transcript scrolling.

## Slice 3. Persist Drawer Width and Collapse Preferences

Priority:

- `P1`

Why this matters:

- The drawer shell exists, but the learner loses panel preferences on refresh or revisit.
- Mobile and tablet users may frequently collapse panels, so restoring those preferences improves continuity.

Scope:

- Persist left/right drawer collapse states.
- Persist left/right drawer widths where appropriate.
- Restore preferences safely across desktop and mobile web layouts.

Mobile web notes:

- Mobile should not blindly restore oversized desktop widths.
- Restore logic should clamp width values per viewport size.

Status:

- `completed as mobile discomfort pass`

Adjusted scope:

- Instead of implementing persistence right now, this slice was narrowed to mobile-web usability fixes only.
- The drawer feature already exists, so the goal became reducing layout pressure and awkward navigation behavior on narrow screens.

Completed work:

- Changed mobile workspace layout so side drawers no longer consume the main content grid width.
- Made mobile drawers behave like overlays, keeping the center content readable.
- Collapsed both side drawers automatically when first entering a mobile-sized viewport.
- Ensured opening one mobile drawer closes the other, reducing cramped multi-panel states.
- Added a tap-to-close mobile backdrop for opened side drawers.
- Converted the top navigation tabs into a horizontal scrollable row on mobile to avoid cramped multi-line wrapping.

## Slice 4. Ready Pack Session State Refactor

Priority:

- `P2`

Why this matters:

- The current flow works, but state transitions are spread across multiple `useState` updates.
- As more UX rules are added, this increases regression risk.

Scope:

- Move Ready Pack study/result transitions into a reducer or small state machine.
- Clarify transitions for `workspace`, `study`, and `result`.
- Keep current behavior stable while reducing state-management complexity.

Mobile web notes:

- Refactoring should not break narrow-screen study and result layouts.

Status:

- `completed`

Completed work:

- Consolidated `selectedPackId`, `viewMode`, and `session` transitions into a local reducer inside `ReadyPackPanel`.
- Moved launch, answer selection, navigation, timer toggle, practice finish, exam submit, and back-to-workspace transitions into explicit actions.
- Reduced scattered ad-hoc state updates while keeping the current learner flow unchanged.
- Kept the refactor local to the Ready Pack module so the existing UI and mobile layout work remained stable.
- Verified the web build after the state refactor.

## Slice 5. Attachment Model Expansion

Priority:

- `P3`

Why this is later:

- Single-image support is enough for the current learner workflow once Slice 1 is complete.
- Multi-attachment support is useful, but not as urgent as fixing the broken current path.

Scope:

- Move attachment state from single file to array-based structure.
- Prepare the composer for future multi-image or mixed attachment support.

Mobile web notes:

- The attachment list UI must remain compact and readable on small screens.

Status:

- `completed`

Completed work:

- Moved tutor chat attachment state from a single-file shape to an array-based attachment model.
- Updated the composer attachment UI to render from the attachment list instead of a single hard-coded slot.
- Kept the current learner flow stable by preserving the existing single-image upload behavior while making the state shape expansion-ready.
- Added attachment preview URL lifecycle handling so thumbnail rendering remains clean and disposable.
- Kept the attachment presentation compact enough for narrow mobile layouts.

## Slice 1 Kickoff Note

Work starts with Slice 1 today.

Implementation target:

- make image attachment in tutor chat fully functional
- keep model choice wired through the image request
- maintain a usable touch-friendly composer on mobile web
