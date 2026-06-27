# NWR Nav Page Framework + Future Tools

Date: 2026-06-26  
Branch: work/nav-page-framework-future-tools-20260626  
Base HEAD: 9e1341bcf7ba4e402204264832692944c49a9600

## Verdict

GREEN as a feature branch pending integration rehearsal and Master merge.

This lane changes app navigation/page labels and roadmap shell content only. It does not
change ranks, tiers, model logic, source-truth artifacts, runtime service behavior, or
data refresh behavior.

## Final Navigation Structure

The app now uses native Streamlit grouped navigation with the locked structure:

- Draft
  - Live Draft
  - Mock Drafts
  - Draft Analyzer
- Research
  - Dynasty Rankings
  - Player Compare
  - Trading Lab
- Future
  - Future Tools
- Admin
  - Refresh Data
  - Evidence Review
  - Settings / Data Health

Compatibility/deep routes remain registered but hidden from primary navigation:

- /drafting-mode
- /drafting-mode-root
- /cheat-sheets
- /post-draft
- /draft-analyzer
- /unified-universe-review
- /nfl-usage-evidence-review
- legacy/debug routes already present in the app

## Draft Analyzer Rename

User-facing Post-Draft Review wording was renamed to Draft Analyzer:

- Visible nav label: Draft Analyzer
- Page title: Draft Analyzer
- Existing route retained: /post-draft-mode
- New compatibility alias added: /draft-analyzer

The page still labels runtime state as local audit/display data, not official source
truth, and does not mutate ranks, tiers, latest files, or model outputs.

## Future Tools Roadmap Shell

/future-tools is roadmap-only. The top warning says:

Roadmap only. These tools are not active model outputs, projections, rankings, or
source-truth decisions yet.

Sections included:

- In-Season Tools
  - Who Should I Start?
  - Waiver Wire Rankings
  - In-Season Rankings
  - Trade Targets
  - Roster Weakness Tracker
- Future Draft Prep
  - Upcoming Rookie Class Preview
  - Draft Class Strength
  - Position Strength by Class
  - Future Pick Planning
  - Position Target Plan
- League Calendar Tools
  - Keeper Deadline Prep
  - Drop Deadline Prep
  - Trade Deadline Prep
  - Playoff Push Planner

Every row is marked Future / Not active. No fake rankings, projections, waiver
recommendations, start/sit advice, rookie class evaluations, model output, or data pull
was implemented.

## Live vs Mock Warning Strategy

Live Draft now says:

LIVE DRAFT - actions on this page write to the real local live draft runtime state.
State changes become part of the live draft event log. Use Mock Drafts for experiments.

Mock Drafts now says:

MOCK DRAFTS - practice state only. Mock state is separate from Live Draft and safe for
experimenting; deletes/resets require confirmation.

Runtime service behavior was not rewritten in this lane.

## Tier Board Demotion

Tier Board / Cheat Sheet remains secondary only:

- Not present as a primary navigation item.
- Available inside Dynasty Rankings as "Tier Board / Cheat Sheet".
- Available inside Live Draft as "Tier Board / value cliffs".
- /cheat-sheets remains as a compatibility route and now states it is a secondary
  tier-board view.

No tier assignments, Dynasty Rank, Final Board Rank, or frozen board data changed.

## Tests And Checks

Focused pytest:

```text
pytest tests/test_agent_audit_synthesis_guardrails.py tests/test_agent_audit_followup_guardrails.py tests/test_draft_day_runtime_state_service.py tests/test_post_draft_mode_service.py tests/test_draft_day_workflow_service.py tests/test_draft_day_trade_lab_service.py tests/test_evidence_status_registry.py tests/test_navigation_compression.py tests/test_drafting_mode_cockpit_page.py tests/test_mock_draft_room_service.py tests/test_future_tools_page.py tests/test_dynasty_rankings_page_v1.py tests/test_evidence_integration_review_page.py tests/test_draft_prep_page.py tests/test_birthday_demo_guardrails.py -q
```

Result: 139 passed.

Other checks:

- Ruff on touched Python files: passed.
- Python compile on touched Python files: passed.
- git diff --check: passed.

## Route Smoke

Feature preview ran on:

http://127.0.0.1:8605

HTTP route smoke returned 200 for:

- /live-draft-room
- /mock-draft
- /post-draft-mode
- /draft-analyzer
- /rankings
- /player-compare
- /trading-lab
- /future-tools
- /refresh-data
- /evidence-integration-review
- /settings-data-health
- /drafting-mode
- /cheat-sheets

Browser marker smoke confirmed:

- Navigation groups: Draft, Research, Future, Admin.
- Hidden compatibility route group did not appear.
- Live Draft warning is visible.
- Mock Draft warning is visible.
- Future Tools is roadmap-only.
- Dynasty Rankings opens with Full Dynasty Rankings and the Tier Board expander.
- Draft Analyzer alias renders the recap/audit page.

## Guardrails

Confirmed:

- Frozen board remains 66 rows.
- No protected artifact diff was detected.
- No C:\NWR_SHARED_DATA, C:\NWR_LOCAL_SECRETS, local_exports, raw cache/API/vendor/Gmail,
  secret, or API-key files are tracked.
- No latest_candidate/latest_approved changes.
- No pinned snapshot/hash changes.
- No rank, tier, model, source-truth, CFBD/NFL usage, or decision-page wiring changes.
- No data refresh was run.
- No hosted deployment work was started.

## Remaining Caveats

- This is a navigation/page-framework lane only.
- Future Tools remains a roadmap shell.
- Human review should verify that the native Streamlit grouped top navigation feels right
  under draft pressure before expanding page count.
