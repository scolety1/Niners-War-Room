# Future 2026 Outcome Evaluation Operational Addendum

This addendum supplements but does not rewrite the canonical contract. It is fixed before outcome ingestion.

## Outcome admission and timing

- Permitted outcome source: only a separately HQ-admitted, season-complete 2026 fantasy-outcome artifact with immutable source receipt, source date, schema, and SHA-256. No live leaderboard, partial-season feed, manual estimate, or current ranking is permitted.
- Evaluation authorization requires written HQ confirmation that the 2026 regular season and the controlling scoring inputs are complete. No interim evaluation is authorized.
- Target label: final 2026 position finish derived from fantasy points under `config/nwr_scoring_rules_nwr_1qb_nonppr_fd_v1.json`; higher fantasy points are better and lower position finish is better.
- Supported controlled positions: QB, RB, WR, TE. The eight preserved K rows remain current-board coverage records but are unsupported and excluded with an explicit reason.

## Identity, eligibility and missing outcomes

- Join only through an admitted exact identity crosswalk keyed by source identity plus position and target season. Normalized names and exact-name review bridges are prohibited as controlling joins.
- Eligible evaluation rows require a frozen valid score, supported position, admitted identity, and admitted final outcome.
- Missing, changed-eligibility, retirement, no-appearance, position-conflict, and unresolved-identity rows remain in coverage reporting with distinct reasons; none may be silently excluded or assigned a manufactured outcome.

## Verification before joining outcomes

1. Check out controlling commit `e4693f49fa44dba6e75b488d6a560a88ea715b8d` or verify the canonical packet against it.
2. Verify preregistration hash `1b8cfac3807613c453588a60b24b6303e8bcaac35d03639c1927ec8d81735e28`.
3. Verify baseline-freeze hash `b3270d9782cf53de745e966c318dd61aa7f482db17da7c4ceb51ef8baa8e1179` and all manifest/player-record hashes.
4. Confirm the challenger freeze remains absent and the comparator list is unchanged.
5. Freeze and hash the admitted outcome and identity-crosswalk inputs before calculation.

## Evaluation outputs

Create a separately versioned outcome-evaluation packet containing input/hash registry, identity/eligibility ledger, full-coverage scoreboard, pairwise shared-row scoreboards, position metrics, equal-position headline, secondary pooled metric, top-K review, severe-miss review, missingness/exclusion ledger, current-board caveat, interpretation limits, validation results, and manifest.

Use the canonical top-K and severe-miss definitions already named in the contract. Report current board separately. Results inform human review only and do not automatically authorize production changes.
