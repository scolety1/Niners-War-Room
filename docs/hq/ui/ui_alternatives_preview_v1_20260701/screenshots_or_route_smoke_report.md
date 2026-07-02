# Screenshots Or Route Smoke Report

No screenshot binaries are tracked in this packet. The preview route itself includes rendered side-by-side sections for A/B/C, which avoids adding image artifacts to the repo.

## HTTP Route Smoke

Temporary server:

- Command: `python -m streamlit run app/main.py --server.headless true --server.port 8571 --server.address 127.0.0.1 --browser.gatherUsageStats false`
- Runtime: Codex bundled Python with project Streamlit dependency installed outside the repo.

Routes checked:

| Route | Status |
| --- | --- |
| `/ui-alternatives-preview` | PASS, HTTP 200 |
| `/rankings` | PASS, HTTP 200 |
| `/player-compare` | PASS, HTTP 200 |
| `/trading-lab` | PASS, HTTP 200 |
| `/development-lab` | PASS, HTTP 200 |
| `/settings-data-health` | PASS, HTTP 200 |
| `/draft-cockpit` | PASS, HTTP 200 |

## Streamlit AppTest Render Smoke

Pages checked with `streamlit.testing.v1.AppTest`:

| Page | Exceptions |
| --- | ---: |
| Preview | 0 |
| Rankings | 0 |
| Player Compare | 0 |
| Trading Lab | 0 |
| Development Lab | 0 |
| Settings / Data Health | 0 |

Result: PASS.
