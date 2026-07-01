# Next Parallel Lanes

Verdict: `YELLOW_NEXT_LANES_DEFINED_NOT_RUN`

This packet defines the next safe work split. It does not run these lanes.

## 1. Point-in-Time Snapshot Feasibility Lane

Purpose:

Determine whether NFLVerse roster, weekly roster, injury, practice, schedule, depth chart, snap, last active, draft, combine, identity, and availability fields can be reconstructed with prediction-time snapshots.

Required outputs:

- source snapshot manifest;
- feature-window matrix;
- prediction-anchor contract;
- identity-safe row counts;
- leakage diagnostics;
- blocked-field table;
- no experiment/model/training/source-truth approval report.

## 2. NFLVerse Player Stats Sidecar Build/Overlap Lane

Purpose:

Build a reproducible historical `player_stats` sidecar and compare overlap against Outcome V2 and Rookie Outcome label artifacts.

Required outputs:

- sidecar build manifest;
- schema manifest;
- identity overlap report;
- position/season coverage;
- unmatched existing labels;
- unmatched NFLVerse rows;
- mismatch taxonomy;
- no label-truth or training-truth promotion.

## 3. Rookie Pre-Draft Feature Coverage Lane

Purpose:

Separate pre-draft, post-draft, and review-only rookie feature families. Positive `draft_picks` evidence may support drafted-only review admission, but not experiments or Gate G.

Required outputs:

- pre-draft vs post-draft feature matrix;
- combine coverage audit;
- draft-pick admission audit;
- UDFA and CFBD blocker update;
- Gate E/F/G status;
- no active rookie probability report.

## 4. Availability Missingness Deep-Dive Lane

Purpose:

Define whether any availability denominator field can move beyond display/review context without health inference, missed-game inference, or leakage.

Required outputs:

- rostered-game denominator definition;
- active/inactive hierarchy;
- bye/cancellation handling;
- missingness and censoring audit;
- games-missed blocker report;
- no health-score/no-medical-projection report.
