# Final Draft-Day Playbook - 2026-06-22

## Verdict

GREEN with known YELLOW data caveats. The Streamlit app is usable for the draft. Frozen Final Draft Board V1 remains the approved baseline, and the expanded PDF free-agent pool is a review-only draftable overlay.

## Open First

- App command: `.\scripts\start_draft_day_app.ps1`
- Primary app URL: `http://127.0.0.1:8501/live-draft-room`
- Static fallback: `C:\NWR\Niners-War-Room\docs\draft_day_exports\final_board_v1_20260622\OPEN_THIS_FIRST.html`
- Detailed pick sheet: `docs/hq/parallel_lanes/overnight_accuracy_max_20260622/FINAL_DRAFT_PICK_WINDOW_CHEAT_SHEET_20260622.md`

## Current Source Truth

- Frozen board: 66 rows, unchanged.
- Expanded draftable pool: frozen board plus PDF page-3 free agents.
- PDF page-3 free agents: 77 parsed; 63 QB/RB/WR/TE shown by default; 14 K/DST hidden by default.
- Candidate Best Available: review-only cross-asset comparison, not an approved rank replacement.
- ADP/range/current pick value: display-only price context, not model input.

## Top Options By Pick

### 1.03

- Best options: Jeremiyah Love, Zay Flowers, Chris Olave, Makai Lemon, Carnell Tate, Jameson Williams, KC Concepcion, Denzel Boston.
- Best rookie/prospect: Jeremiyah Love.
- Veteran/free-agent comparison set: Zay Flowers, Chris Olave, Jameson Williams, Tyreek Hill.
- Best value if he falls: Jeremiyah Love.

### 1.04

- Best options: Jeremiyah Love, Zay Flowers, Chris Olave, Makai Lemon, Carnell Tate, Jameson Williams, KC Concepcion, Denzel Boston.
- Best rookie/prospect: Jeremiyah Love.
- Veteran/free-agent comparison set: Zay Flowers, Chris Olave, Jameson Williams, Tyreek Hill.
- Best values if they fall: Jeremiyah Love, Drake Maye.

### 1.09

- Best options: Jeremiyah Love, Zay Flowers, Chris Olave, Makai Lemon, Carnell Tate, Jameson Williams, KC Concepcion, Denzel Boston.
- Best rookie/prospect: Jeremiyah Love.
- Veteran/free-agent comparison set: Zay Flowers, Chris Olave, Jameson Williams, Tyreek Hill.
- Best values if they fall: Jeremiyah Love, Zay Flowers, Chris Olave, Carnell Tate, Drake Maye, Rashee Rice.

### 2.04

- Best options: Jeremiyah Love, Zay Flowers, Chris Olave, Makai Lemon, Carnell Tate, Jameson Williams, KC Concepcion, Denzel Boston.
- Best rookie/prospect: Jeremiyah Love.
- Veteran/free-agent comparison set: Zay Flowers, Chris Olave, Jameson Williams, Tyreek Hill.
- Best values if they fall: Jeremiyah Love, Zay Flowers, Chris Olave, Makai Lemon, Carnell Tate, Jameson Williams.

### 2.08

- Best options: Jeremiyah Love, Zay Flowers, Chris Olave, Makai Lemon, Carnell Tate, Jameson Williams, KC Concepcion, Denzel Boston.
- Best rookie/prospect: Jeremiyah Love.
- Veteran/free-agent comparison set: Zay Flowers, Chris Olave, Jameson Williams, Tyreek Hill.
- Best values if they fall: Jeremiyah Love, Zay Flowers, Chris Olave, Makai Lemon, Carnell Tate, Jameson Williams.

## Rookie Vs Veteran Checks

- If Zay Flowers is available, compare him directly against the rookie WR/RB tier before taking a lower-confidence rookie.
- If Chris Olave is available, compare him directly against the top rookie WRs and do not bury him behind uncertainty-only prospect upside.
- If Jameson Williams is available, keep him review-visible; he should not be ignored simply because his frozen rank is lower.
- Drake Maye is discounted for 10-team 1QB, but he is not a zero-value asset.
- Tyreek Hill is now visible from the PDF free-agent pool with internal model-v4 review value, Candidate Rank 13, Low confidence, and age/receipt caveats.

## Players Not To Blindly Trust

- Any PDF-only free agent with Candidate Rank or Candidate Value shown as `Not enough information`.
- Tyreek Hill without checking age, team/status, and receipt caveats.
- Dallas Goedert, Juwan Johnson, Tua Tagovailoa, Jaylen Wright, Isaac Guerendo, Darnell Mooney, Rashod Bateman, Bryce Young, Anthony Richardson, Austin Ekeler, Marquise Brown, Cedric Tillman, Jerome Ford, Ben Sinnott, Michael Mayer, Geno Smith, Marcus Mariota, Mac Jones, and Noah Gray: draftable from PDF, but insufficient safe internal candidate value in the app layer.
- Any player with Low confidence, manual-review flags, needs-data flags, or missing Outcome support.

## How To Use The App

- Start in Live Draft Room.
- Use Candidate Best Available to find the best review-only rookie/veteran comparison.
- Keep Final Board Rank visible as the frozen approved baseline.
- Use `Show PDF free agents` to keep verified page-3 free agents in the pool.
- Keep `Show K/DST` off by default unless intentionally reviewing those positions.
- Assign picks in the Pick Selection panel; the board auto-advances to the next open pick.
- Use Undo Last or Remove Player for mistakes.

## Candidate Rank Vs Final Board Rank

- Prefer Candidate Rank when it lifts a known veteran/free-agent with internal evidence and the caveat is acceptable.
- Prefer Final Board Rank when Candidate confidence is Low, source notes say `Not enough information`, or the player is PDF-only with no internal value.
- Never treat Candidate Rank as latest_candidate, latest_approved, hidden sort, private value, or final draft advice.

## ADP Range / Current Pick Value

- ADP Range is display-only available-pool price context.
- Current Pick Value is a reach/value timing label, not model truth.
- Do not use ADP, PDF rank, market rank, or trade-calculator context as an internal value input.

## Outcome / Horizon Context

- Outcome is display-only and partial.
- Position-aware display is expected: wrong-position heads are hidden or `N/A`; same-position missing support is `Not enough information`.
- Outcome support remains limited; missing Outcome is not zero.
- Horizon bands are review-only context, not approved probabilities.

## Emergency Fallback

If Streamlit has a problem, open:

`C:\NWR\Niners-War-Room\docs\draft_day_exports\final_board_v1_20260622\OPEN_THIS_FIRST.html`

Then use:

- `docs/hq/parallel_lanes/overnight_accuracy_max_20260622/FINAL_DRAFT_PICK_WINDOW_CHEAT_SHEET_20260622.md`
- `docs/hq/parallel_lanes/overnight_accuracy_max_20260622/expanded_pool_top_candidate_best_available.csv`
- `docs/hq/parallel_lanes/overnight_accuracy_max_20260622/expanded_pool_key_free_agent_sanity.csv`

## Final Guardrails

- Frozen board was not mutated.
- Final Board Rank was not changed.
- Dynasty Rank was not overwritten.
- latest_candidate/latest_approved were not updated.
- Pinned snapshot was not mutated.
- No hosted deployment was created.
- No raw vendor CSVs, raw prediction dumps, or `C:\NWR_SHARED_DATA` files are tracked.
