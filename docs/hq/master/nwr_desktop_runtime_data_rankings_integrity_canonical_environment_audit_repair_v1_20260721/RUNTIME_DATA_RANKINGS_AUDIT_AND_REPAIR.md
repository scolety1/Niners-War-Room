# NWR desktop runtime, data, and rankings audit and repair

## Verdict

The installed Niners War Room desktop path is repaired and independently validated against canonical HQ `cdc77f32507ef7e451b872b9a7c28275af6c4725` (tree `d5df1e865b010b58b49be70b8b3ba91308159ef6`). The live remote `origin/work/hq-parallel-control` resolved to the same commit before repair work began.

The failure was not a ranking-formula defect. It was a combination of launcher-path, ignored-runtime-data, and Windows process-lineage defects:

1. The installed Desktop and Start Menu launch shortcuts directly invoked `pythonw.exe scripts/nwr_desktop.py start`. Launcher logs recorded three real `[WinError 6] The handle is invalid` start failures. The direct path could leave an active server with `RECOVERY_REQUIRED` ownership evidence.
2. The stable checkout had no repository-local active data pack, approved 240-row full dynasty board, or Outcome V1 display artifact. The application therefore fell back to bundled/sample or unavailable states on surfaces whose accepted data is intentionally ignored by Git.
3. Windows descendant discovery trusted parent PID alone. A pre-existing process whose stale parent PID had been reused by the launcher could be captured as owned, and a later reused descendant PID was treated as a blocking identity conflict. The installed shortcut could start healthily but fail Stop with `RECOVERY_REQUIRED` after the original processes were already gone.

No ranking formula, score, tier, source-admission rule, player identity, recommendation, outcome meaning, or model semantic was changed.

## Installed runtime repair

Both installed launch shortcuts now resolve to:

```text
Target: C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe
Arguments: -NoProfile -ExecutionPolicy Bypass -File "C:\NWR\Niners-War-Room-V1\scripts\NWR Desktop Commands.ps1" -Command start
Working directory: C:\NWR\Niners-War-Room-V1
```

The installer migrates only exact legacy-owned `pythonw.exe` shortcuts and retains rollback behavior. The uninstaller recognizes both the current PowerShell form and the exact legacy form. Same-named foreign shortcuts remain fail-closed.

Process capture now requires each Windows child identity to have a creation time at or after its verified parent and to retain the observed parent relationship. A PID occupied by a different full identity is recorded as reused/unrelated and is never targeted. Top-level listener changes and unverified live browser registrations remain blocking conflicts.

## Canonical local data restored

Only artifacts with exact existing application contracts and independently corroborated recovery copies were restored. No review-only draft-pool preview manifest was promoted.

| Artifact | Rows | SHA-256 | Runtime role |
| --- | ---: | --- | --- |
| `local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv` | 240 | `263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4` | Approved full dynasty rankings |
| `local_exports/outcome_probability/numeric_outcome_display_v1.csv` | 240 | `1fb63fec25f7893ed09004830c7eb4e5ed32c6622c08876849fb61a2e4826cb0` | Outcome V1 display context |
| Active pack `dim_players.csv` | 240 | `9c3d86491a52f8ec51d90a62f81a80beb31877dfbbd6d896b807c70a630673ef` | Player dimension |
| Active pack `fact_rosters.csv` | 240 | `7700ddb92817eac06ab04e3ab8899d109017cfb025fd4621a4e7c870113ccdaa` | Roster facts |
| Active pack `fact_official_rankings.csv` | 240 | `5982539472cbb172f54ce5280b44a00911b1dad8842ffa58e9074406131ecae6` | Official-rank context |
| Active pack `fact_future_picks.csv` | 50 | `e6f8de25c60b08928a066d400aa21832d26acc553972f1903868c81fcaed1ff9` | Future-pick facts |
| Active pack `fact_pick_values.csv` | 50 | `e7478e46e8b2097668682fff70c057098b560692a04f0287d4f56ce73e03f70f` | Pick-value facts |
| Active pack `model_outputs.csv` | 240 | `cf846c1fcd3bd541cbae1c5cf935136de73a05c5253c2a6ed58c0f213198e7a2` | Legacy active-pack review scores |
| Active pack `metadata_sources.csv` | 7 | `953f2957d93f0677ab71652bfd6b46e574f8952ab452a33a98b7ffba8a75c87a` | Source metadata |

The tracked Outcome V2 artifact remains exact at 240 rows and SHA-256 `63569e3758ab20e74eef30c1723afc72c80b5f6174f66d9a4015c24f0f44723e`. The tracked NFLVerse player-context artifact remains 294 rows; neither was modified.

## Rendered surface agreement

The real installed runtime was launched on `127.0.0.1:8520` and inspected through rendered Streamlit pages.

| Surface | Rendered evidence | Agreement |
| --- | --- | --- |
| Dynasty Rankings | 240 full dynasty rows; first five are Puka Nacua, Jaxon Smith-Njigba, Bijan Robinson, Jonathan Taylor, Jahmyr Gibbs | Exact approved board |
| Settings / Data Health | HQ `cdc77f...`; Full Dynasty Rankings `240`, `GREEN`; frozen board `66`, `GREEN` | Exact application and board state |
| Legacy Dynasty Rankings | Active pack `lve_sleeper_20260505_pdf_ranks`; `0 errors/0 warnings`; 232 active rows; Puka Nacua rank 1 | Exact active pack and approved private board context |
| Draft Cockpit | 66 frozen rows plus 77 verified PDF free agents; 143 draftable rows | Intended frozen-plus-overlay universe |
| Player Compare | Frozen 66-row checkpoint plus verified PDF overlay; Jeremiyah Love and Makai Lemon selected by default | Intended comparison universe |
| Trading Lab | 66 frozen-board rows, 54 pick-context rows, 294 NFLVerse context rows | Intended manual/display-only context |
| War Board | Active pack is ready and review-only; optional Model v4 shadow preview remains explicitly unavailable | Truthful fail-closed optional preview; active ranks unchanged |

The full dynasty board, frozen draft checkpoint, active legacy pack, and overlay draft pool are intentionally different semantic surfaces. Agreement means each consumer resolves its canonical accepted source and labels that source honestly; it does not mean forcing all surfaces into one ranking order.

## Known non-blocking review states

- The approved 240-row full dynasty board contains zero rookie/prospect rows. Data Health correctly reports this as the existing yellow caveat.
- The latest Refresh Data receipt is missing, and the historical actual-draft/trade imports remain absent. The dashboard reports these as review states and does not infer freshness.
- The optional `local_exports/model_v4/review_only_latest` shadow-preview family was not restored because no exact current admitted artifact set was proven. Hidden review surfaces report it unavailable and do not substitute or mutate active ranks.

## Scope proof

- No security scan was run.
- No other repository was modified.
- Ignored runtime data was restored only inside `C:\NWR\Niners-War-Room-V1`.
- Tracked implementation changes are limited to launcher ownership logic, shortcut install/uninstall logic, directly related tests, and this evidence packet.
