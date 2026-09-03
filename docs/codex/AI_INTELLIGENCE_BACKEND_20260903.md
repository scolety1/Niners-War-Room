# AI Intelligence backend skeleton (sections 19–21)

Code: `src/services/ai_intelligence_backend_service.py`. Tests:
`tests/test_ai_intelligence_backend_service.py`, 24/24 passing. Not
wired into `desktop_facade.py`, any HTTP route, or any frontend page yet
(verified via grep) — this is the backend skeleton the sections asked
for, not the owner-facing surface.

No live API calls anywhere in this module. News events are appended by
an owner/operator action (`append_news_event`); this module never fetches
news on its own, so there is nothing to gate behind
`NWR_FANTASYPROS_API_KEY` or any other credential — that key stays
scoped to `fantasypros_kdst_consensus_service.py`, its existing home.

## News Scout (section 19)

`NewsEvent` schema (`event_type` ∈ INJURY/DEPTH_CHART_CHANGE/SUSPENSION/
TRADE/RETIREMENT/COACHING_CHANGE/ROLE_CHANGE/OTHER, `severity` ∈ LOW/
MEDIUM/HIGH) + `validate_news_event` (rejects a malformed event outright)
+ an append-only, per-profile JSON Lines store
(`append_news_event`/`read_news_events`), the same architecture as
`nwr_pure_experiment_service.py`'s decision receipts. Refuses a
duplicate `event_id`.

## Impact Analyst (section 20)

`generate_direct_impact_hypothesis`: a **disclosed, structural rule
table** over `(event_type, severity)` pairs — not a live model call.
Every combination not explicitly in the table degrades to
`UNCERTAIN`/`LOW` confidence with `requires_owner_review=True` rather
than guessing.

`generate_beneficiary_hypotheses`: for a genuinely negative, medium+
confidence event (injury/suspension/retirement), generates a low-
confidence `POSITIVE` hypothesis for each teammate the **caller**
supplies at the same position — this function never looks up a roster or
invents a name itself, and every result is `requires_owner_review=True`
(a structural inference, not a confirmed depth-chart fact). An uncertain
or low-severity event produces no beneficiary hypotheses at all.

## Explanation layer (section 21)

`explain_pick_recommendation`: assembles natural language strictly from
real, already-computed factors the caller supplies on
`PickExplanationInputs` — overall rank, replacement-adjusted value
(NWR's own existing VOR field), roster position count vs. max, ADP
context, and any Impact Analyst hypotheses. It never invents a clause not
backed by a field on the input — an absent factor (e.g. no ADP available)
is simply omitted, not filled in with a guess.

## What's deferred

Wiring any of this into `desktop_facade.py`/an HTTP route/the Draft Room
UI, and any live ingestion path for real news (which would require an
actual news-provider credential and API call, explicitly out of scope
per this section's "no live API calls" instruction). This is
schema-and-logic infrastructure, ready to be wired in once an owner
decides to connect a real news source.
