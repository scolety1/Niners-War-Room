# Mock Draft Input Snapshot Contract - 2026-06-16

## Source
- PDF source: `C:\Users\smcol\Downloads\LVE Rosters 061326.pdf`.
- Local extracted snapshot root: `local_exports/mock_draft_simulator/input_snapshots/lve_rosters_061326/`.
- Snapshot files remain local-only under ignored `local_exports/` and must not be committed.

## Allowed Use
- Review-only mock draft preparation.
- Build in-memory simulator pick rows from 2026 extracted pick ownership.
- Build in-memory availability rows from declared top-five drops and extracted free-agent rows.
- Preserve duplicate declared drops, including Brock Purdy x2, until Tim resolves intent.

## Blocked Use
- Production rankings or sorting.
- Rookie HQ files, rookie formulas, rookie board order, rookie warnings, or rookie exports.
- Outcome probabilities or coarse bands.
- Model artifact promotion.
- App/Streamlit wiring.
- Treating PDF `overall_rank`, ADP, market, or search rank as NWR private quality/value.

## Review Rules
- 2026 pick labels with real slots, such as `1.03`, `1.04`, `2.04`, `2.08`, and `5.04`, may become simulator pick rows.
- Future placeholder pick labels such as `1.00` for 2027/2028 are review-required and not simulator-ready until a contract is defined.
- Snapshot-derived available rows must keep `stats_model_value=0.0` unless a separate admitted NWR private value source is explicitly joined later.
- Snapshot ranks may be displayed as source rank context and used for review ordering only; they are not NWR quality.
