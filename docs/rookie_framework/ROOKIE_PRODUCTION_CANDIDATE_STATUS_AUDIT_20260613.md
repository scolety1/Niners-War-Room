# Rookie Production Candidate Status Audit - 2026-06-13

## 1. Executive Verdict

Verdict: GREEN.

`rankable_with_warning` is behaving correctly as a candidate/export-only middle status. It separates rows that can be ordered with visible caveats from rows that are clean `ready`, rows that need human review first, rows that are blocked, and rows that are unavailable.

Production implementation remains blocked. The new status semantics make the candidate export more useful for review and proposal work, but they do not approve production ranking replacement, app display, private-score changes, probabilities, bands, outcome columns, or veteran outcome-head usage.

The next safe movement is proposal/readiness work only, not implementation.

## 2. Status Counts Review

Current production-candidate export counts:

- `ready`: `0`
- `rankable_with_warning`: `42`
- `manual_review_required`: `7`
- `blocked`: `43`
- `unavailable`: `119`

These counts make sense.

- `ready=0` is expected because no row is clean enough to lose all warnings, gaps, source caveats, and manual-review context.
- `rankable_with_warning=42` is useful because it captures players with role/path context that can be ordered only while warnings remain visible.
- `manual_review_required=7` correctly isolates rows with human decisions required before production ranking movement, including premium injury/manual-review cases and TE exception reviews.
- `blocked=43` preserves hard-capped or capped-review rows.
- `unavailable=119` keeps low-source, needs-data, roster-declaration, and insufficient-evidence rows out of production movement.

## 3. `ready` Semantics Audit

GREEN.

`ready` remains strict. There are `0` clean ready rows, which confirms the patch did not promote warning-heavy players into a clean status.

No warning/manual-review/source-gap players were incorrectly promoted to `ready`. Rows with manual flags, remaining gaps, quarantined source terms, low source confidence, injury review, hard caps, source conflicts, or needs-data status remain outside `ready`.

## 4. `rankable_with_warning` Audit

GREEN.

Rows marked `rankable_with_warning` are orderable only with visible warnings. The audit found:

- `42` rows marked `rankable_with_warning`.
- `0` `rankable_with_warning` rows missing `manual_warnings`.
- `0` `rankable_with_warning` rows missing source-safety notes that say they are rankable only with visible warnings.

Warning preservation:

- Manual flags remain visible in `manual_warnings`.
- Injury flags remain visible or are escalated to `manual_review_required`.
- Source caveats remain visible, including quarantined source terms.
- Remaining gaps remain visible.
- Secondary charting remains soft-flag context.
- Scouting prose remains manual-review context.
- No row uses `rankable_with_warning` to hide warnings or appear clean.

## 5. Premium Pick Audit

### 1.03

GREEN.

`1.03` remains empty. The candidate export has `0` rows with `pick_zone=1.03`.

Production can safely represent `1.03` as `trade_down_review`, `hold`, `manual_review_required`, or `no_player_cleared` if a future approved artifact needs to display the slot. It should not force a player into `1.03`.

### 1.04

The `1.04` premium export has:

- `7` `rankable_with_warning`
- `2` `manual_review_required`
- `1` `unavailable`
- `0` `ready`
- `0` `blocked`

`1.04` candidates now marked `rankable_with_warning`:

- Jeremiyah Love: warnings include explosive rate, pass protection, RB survival gaps, soft flags, and quarantined source context.
- Chris Bell: warnings include route/manufactured-touch manual review, source-limited context, quarantined ranking terms, and remaining target-earning gaps.
- Makai Lemon: warnings include route/separation/press/YAC manual review and remaining WR target-earning gaps.
- Denzel Boston: warnings include route/separation/first-down/contested/red-zone manual review, quarantined projection/ranking context, and remaining WR gaps.
- KC Concepcion: warnings include route/separation/press/manufactured-touch manual review and target-rate gaps.
- Germie Bernard: warnings include route/separation/manufactured-touch manual review and target-rate gaps.
- Zachariah Branch: warnings include route/separation/manufactured-touch manual review and role/special-teams translation risk.

Premium candidates not rankable yet:

- Jordyn Tyson: `manual_review_required` because premium injury review and role/target questions remain.
- Kaelon Black: `manual_review_required` because short-yardage and injury-history review remain.
- Ted Hurst: `unavailable` because low source confidence and broad premium WR proof gaps remain.

No premium candidate is clean `ready`, and none is approved for production implementation.

## 6. Round 2 / 5.04 Audit

### Round 2

Round 2 export status:

- `3` `rankable_with_warning`
- `2` `manual_review_required`
- `4` `unavailable`
- `0` `ready`
- `0` `blocked`

Round 2 candidates marked `rankable_with_warning`:

- J'Mari Taylor
- Adam Randall
- Emmett Johnson

These rows remain warning-visible and are not clean. Warnings include RB survival gaps, soft flags, pass protection, explosive rate, receiving/first-down/goal-line gaps, and source-safety context.

Round 2 candidates marked `manual_review_required`:

- Jamal Haynes
- Jamarion Miller

Both carry injury/manual-review concerns that must be answered before production ranking movement.

Round 2 unavailable rows:

- Mike Washington
- Savion Red
- Dean Connors
- Nicholas Singleton

These remain unavailable because of low source confidence, needs-data status, inherited tags, or broad RB survival gaps.

### 5.04

The split `5.04` candidate export has:

- `32` `rankable_with_warning`
- `3` `manual_review_required`
- `84` `unavailable`
- `0` `ready`
- `0` `blocked`

High-signal `5.04` rankable-with-warning examples include:

- Skyler Bell
- Demond Claiborne
- Kaytron Allen
- Seth McGowan

TE exception rows such as Eli Stowers and Sam Roush are correctly held in `manual_review_required`, not promoted to clean or warning-rankable status.

No generic `SOURCE_LIMITED_REVIEW` row was elevated to `rankable_with_warning`. No plain `TE_REPLACEABLE` row was elevated to `rankable_with_warning`. Generic low-upside profiles remain unavailable or blocked.

## 7. Source-Safety Audit

GREEN.

The candidate export and builder preserve source-safety guardrails:

- Market/rank/projection terms are not used as private inputs.
- Quarantined warning terms stay warnings only.
- No legacy `private_score` input is used.
- No rookie probabilities are created.
- No probability bands are created.
- No app-readable output is created.
- No veteran outcome-head usage exists.
- Secondary charting remains soft-flag context.
- Scouting prose remains manual-review context.

Strict mode still rejects prohibited private input columns.

## 8. Implementation Safety

GREEN.

Confirmed:

- No production ranking files changed.
- No app or Streamlit files changed.
- No private-score files changed.
- No formula files changed.
- No probability or band files were created.
- No outcome-column files changed.
- No veteran files changed.
- `data/` remains untracked and uncommitted.
- `local_exports/` remain uncommitted.
- Every candidate row remains `production_candidate_only=yes`.
- Every candidate row remains `app_read_allowed=no`.
- Every candidate row remains `probabilities_created=no`.

## 9. Recommended Next Step

Recommendation: create a candidate implementation-readiness proposal.

That proposal should remain rookie-only and gated. It should not implement production promotion. It should define what HQ would need to approve before any implementation prompt, how `rankable_with_warning` would be displayed, how `manual_review_required` rows are held, and why production/app work remains blocked until explicit human approval.

Do not begin production implementation from this audit.
