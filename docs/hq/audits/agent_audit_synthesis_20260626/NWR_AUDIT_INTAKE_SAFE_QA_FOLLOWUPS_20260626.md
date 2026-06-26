# NWR Audit Intake Safe QA Follow-Ups - 2026-06-26

## Verdict

GREEN for safe QA follow-up scope. This update adds guardrail tests and documentation only. It does not implement Live Draft V2, model input, app decision wiring, ranking changes, or source-truth promotion.

## What was added

- `critical_service_test_mapping_20260626.csv`: maps critical services to existing focused tests and calls out one partial registry coverage waiver.
- `local_preflight_guardrail_checklist_20260626.md`: a local preflight checklist covering focused pytest, Ruff, protected artifact diff, raw/shared/local/secret scans, blocked-field scanner coverage, absolute path scan, and whitespace checks.
- `tests/test_agent_audit_followup_guardrails.py`: focused tests for the audit follow-up queue.

## Guardrail coverage added

The new tests prove:

- CFBD, NFL usage, Outcome, DynastyProcess, and proxy evidence remain review-only, display-only, or blocked as appropriate.
- True routes, true TPRR, and true YPRR remain blocked licensed-data gaps.
- Red-zone, inside-10, and inside-5 remain review-only/display-only candidates with model input disabled.
- Decision pages do not read CFBD/NFL/full-refresh evidence artifact roots.
- Missing player_id remains blocked and is not fabricated.
- Missing age remains `Not enough information` and is not treated as average or clean.
- Missing injury/status remains `Not enough information` and is not treated as healthy or low-risk.
- Missing/unsupported Outcome remains `Not enough information` and is not treated as zero or low probability.
- Critical services have mapped focused tests or explicit waivers.
- Representative services import, and representative pages compile, without executing Streamlit pages.

## Explicit non-goals

- No Live Draft V2 implementation started.
- No app decision page wiring added.
- No model input enabled.
- No model/rank/source-truth logic changed.
- No CFBD/NFL/Outcome/proxy/market data promoted.
- No raw/shared/local secret/runtime files added.

## Known validation caveat

Full-repo pytest and full-repo Ruff were already observed to have pre-existing failures outside this audit lane. This follow-up keeps validation focused on the audit guardrails and lane-touched files, while documenting the broader preflight commands so future cleanup can address legacy issues separately.
