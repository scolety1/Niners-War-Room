# NFL Usage Evidence Review Page

## Verdict

GREEN. The optional review page was added because live validation is GREEN and the page reads only committed summary artifacts.

## Route

`/nfl-usage-evidence-review`

The route is hidden from the main navigation and intended for review/debug inspection only.

## Data Loaded

Only small CSV artifacts under:

`docs/hq/data_sources/nfl_usage/review_artifacts/`

The page does not load raw play-by-play, snap counts, NGS, FTN, PFR, participation, or shared-cache payloads.

## Guardrails

- App/model integration: no
- Decision-page integration: no
- Model input: no
- Rankings/Drafting Mode/Player Compare/Trading Lab/Post-Draft feed: no
