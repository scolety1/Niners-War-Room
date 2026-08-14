# Desktop Reconciliation Conflicts

Base: `11afc9463e7581d9d80e595a953ab04506d059a7` (Practical Mock).

The Dynasty bridge (`bc9d812`, `194dc96`) was replayed onto the Practical Mock
line. Git performed clean content merges; the following were the shared semantic
surfaces reviewed after the replay.

| File | Competing behavior | Chosen merged behavior | Why | Regression coverage |
| --- | --- | --- | --- | --- |
| `desktop/packages/contracts/src/index.ts` | Dynasty adds typed immediate-production and Rookie-Veteran bridge results; Redraft adds practical-profile, manual K/DST, and external-consensus payloads. | Retain every additive interface and optional field. `DynastyComparison.bridge` stays optional; Redraft contracts retain `practicalMode`, `manualAssets`, and `externalConsensus`. | The apps are distinct and their API payloads must coexist without inventing a shared valuation scale. | `desktop` typecheck; `tests/test_desktop_application_api.py`; Dynasty and Redraft frontend tests. |
| `src/application/desktop_facade.py` | Dynasty enriches player detail, comparison, and trade data with separately governed immediate-production context; Redraft imports Sleeper profiles, starts a local practical mock, exposes manual K/DST, and keeps FantasyPros optional. | Retain both mode-gated paths in one facade. Dynasty bridge calls remain in Dynasty-only flows; Sleeper/FantasyPros calls remain Redraft-only and read-only. | Preserves Rookie ↔ Veteran comparison while keeping Fantasy Gamers Practical Mock operational and preventing cross-app state or authority leakage. | `tests/test_rookie_veteran_dynasty_bridge_service.py`, `tests/test_desktop_application_api.py`, `tests/test_practical_redraft_mock_service.py`, `tests/test_sleeper_redraft_owner_service.py`, `tests/test_fantasypros_kdst_consensus_service.py`. |
| `tests/test_desktop_application_api.py` | Dynasty asserts bridge payloads and no common-score arithmetic; Redraft asserts practical profile/bootstrap payload shape. | Preserve both assertion groups and require the union payload shape. | A facade integration regression can otherwise silently remove one product surface while the other still passes. | Focused pytest run listed above. |

No textual conflict markers were produced. No model, frozen authority, or candidate
rookie score was promoted during this reconciliation.

## Replay correction

`src/services/rookie_draft_eligibility_service.py` pinned the Rookie Intelligence
V2 factual-overlay receipt to an older hash even though the checked-in factual
overlay had been updated by the validated candidate line. The receipt now pins the
checked-in `68afdb…e922` file. This only restores the fail-closed 80-player
availability gate: the overlay supplies factual identity/context, and the runtime
continues to expose 73 frozen scored players plus seven unscored manual-review
assets. The candidate score/rank file is neither loaded nor promoted.
