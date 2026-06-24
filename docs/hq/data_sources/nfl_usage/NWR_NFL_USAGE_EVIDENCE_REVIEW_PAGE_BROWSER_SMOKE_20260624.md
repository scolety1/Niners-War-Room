# NFL Usage Evidence Review Page Browser Smoke

## Verdict

GREEN.

Streamlit was launched locally on port `8502` and checked with Playwright using the system Edge channel.

## Routes Checked

- `/nfl-usage-evidence-review`: HTTP 200, page title found, review-only banner found, no visible traceback/error text
- `/drafting-mode`: HTTP 200, no visible traceback/error text
- `/rankings`: HTTP 200, no visible traceback/error text
- `/settings-data-health`: HTTP 200, no visible traceback/error text
- `/unified-universe-review`: HTTP 200, no visible traceback/error text

## Guardrails

The smoke did not load or inspect raw shared-cache payloads. The page service reads only committed summary artifacts under `docs/hq/data_sources/nfl_usage/review_artifacts/`.
