# Prompt: NFLVerse Player Context Human Identity Decision Review

Use this prompt when opening the next Data Hygiene / Identity Review lane.

```text
You are Codex working in Niners War Room Data Hygiene.

Task:
Run the NFLVerse Player Context Human Identity Decision Review lane.

This lane reviews the pending identity decision sheet created during the NFLVerse
display upgrade wave. It may prepare a human-review workflow and record explicit
human decisions if they are provided. It must not infer human approval.

Base:
Fetch origin first.
Use current `origin/work/hq-parallel-control`.

Required minimum HQ HEAD:
`30cff63884c8d8696c248ce10776f446063de2ce`

Branch/worktree:
Branch: `work/nflverse-player-context-human-identity-review-20260630`
Worktree: `C:\NWR\Niners-War-Room-nflverse-player-context-human-identity-review-20260630`

Inputs:
- `docs/hq/data_sources/nflverse_player_context_identity_approval_v1_20260630/identity_human_decision_sheet.csv`
- `docs/hq/data_sources/nflverse_player_context_identity_approval_v1_20260630/identity_approval_summary.md`
- `docs/hq/data_sources/nflverse_player_context_identity_hardening_v1_20260630/`
- `docs/hq/data_sources/nflverse_player_context_display_20260630/`
- `docs/hq/data_sources/nflverse_display_upgrade_closeout_20260630/`

Known current identity facts:
- 54 identity-review rows.
- 43 rows are recommended review-only approvals, but still not approved.
- 4 rows require human review.
- 7 rows are recommended keep-blocked.
- `approved_by_human=false` for all rows.
- No approved identity overlay exists yet.

Goal:
Prepare and, only if explicit human decisions are present, validate a review-only
identity decision packet.

Allowed:
- Read tracked repo artifacts.
- Produce docs/CSV under:
  `docs/hq/data_sources/nflverse_player_context_human_identity_review_20260630/`
- Validate decision sheet schema and conservative flags.
- Create an apply plan for a later overlay lane.
- If the user provides explicit human decisions in this lane, record them in a new
  review packet.

Not allowed:
- Do not set `approved_by_human=true` by inference.
- Do not treat recommended approvals as approved joins.
- Do not rebuild the player context artifact.
- Do not expose context for identity-review rows in app surfaces.
- Do not promote identities to source truth, model input, training, rank logic,
  hidden sort, trade value, pick value, or recommendations.
- Do not touch app pages.
- Do not touch Rankings, Player Compare, Trading Lab, Development Lab, Draft Room,
  Injury / Availability UI, Outcome probabilities, source truth, model logic, ranks,
  tiers, latest pointers, frozen board, runtime JSON, raw/shared/local/secrets.

Required outputs:
1. `artifact_manifest.md`
2. `human_identity_review_summary.md`
3. `human_identity_decision_review.csv`
4. `identity_apply_overlay_readiness.md`
5. `identity_review_guardrail_report.md`
6. `next_lane_prompt_if_approved.md`

Decision rules:
- `human_decision=PENDING` means no approval.
- `human_decision=APPROVE_REVIEW_ONLY` may be accepted only if paired with
  `approved_by_human=true` and explicit human evidence in the packet.
- `REJECT_WRONG_IDENTITY`, `KEEP_BLOCKED`, and `NEEDS_MORE_INFO` remain blocked.
- Model/training/source-truth/rank/hidden-sort/trade/pick flags must remain false.

Checks:
- CSV schema validation.
- Confirm no `approved_by_human=true` unless explicit human decision evidence exists.
- Confirm all model/training/source-truth/rank/hidden-sort/trade/pick flags remain false.
- Confirm no app/model/rank/source-truth/protected paths changed.
- `git diff --check`.
- Forbidden tracked path scan.
- Protected path scan.

Commit and push if docs/CSV checks pass.

Final verdict options:
- `YELLOW_HUMAN_IDENTITY_REVIEW_PENDING`
- `GREEN_HUMAN_REVIEW_DECISIONS_RECORDED`
- `YELLOW_NO_HUMAN_APPROVAL_EVIDENCE`
- `RED_GUARDRAIL_FAILURE`

Expected likely result:
`YELLOW_HUMAN_IDENTITY_REVIEW_PENDING`

Final report:
- verdict
- branch/worktree
- base HQ HEAD
- final HEAD
- pushed yes/no
- decision counts
- whether any rows were explicitly approved by a human
- whether an apply-overlay lane is ready
- files changed
- checks run
- guardrail confirmation
- recommended next lane
```
