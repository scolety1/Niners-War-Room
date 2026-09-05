# NWR PRACTICE DRAFT — FINAL DATA/TEAM-SCORE RECONCILIATION

## 1. Rookies — audit and restoration

### Exact audit (from the real, installed 2026 snapshot, re-verified this pass)

- **78 original exclusions**, all for exactly one reason, confirmed per-row: `source_as_of exceeds the 30-day freshness window` (`source_as_of=2026-07-30`, 37 days stale as of today 2026-09-05). No other reason appears among the 78.
- A **separate 2 rookies** (Max Bredeson, Riley Nowakowski) are excluded further upstream — they have no row in `current.csv` at all, blocked at original data-admission time for a position conflict with the current factual registry (per the original governance receipt's own disclosed limitations). Not re-investigated tonight — this is a genuine identity/roster-conflict question, not a freshness question, and resolving it would require fresh identity work outside tonight's scope.

### Search for a newer, already-governed rookie source

Checked for any more-current, already-admitted rookie data for the Redraft V1 engine specifically. Found two later-dated candidate packets (`docs/hq/model/nwr_rookie_review_candidate_v1_20260814/`, `nwr_rookie_intelligence_v2_20260814/`) — **these belong to a different, parallel research track** ("model_v4" dynasty/rookie-review scoring, evidenced by their own `MODEL_V4_2026_ROOKIE_REVIEW_CANDIDATE.csv` filename), producing rank/score outputs in a different shape than the Redraft engine's required stat-line projection format (`passing_yards`, `rushing_tds`, etc.), and carrying no `NWR_DATA_GOVERNANCE.json`-style admission receipt for the Redraft engine's `REDRAFT_2026_PROJECTIONS` contract scope. Using them would require new engineering (mapping a rookie score into a stat-line projection) and a new governance admission — real work, not a drop-in refresh, and out of scope for tonight (per "do not fabricate missing projections"). **Conclusion: no existing, already-governed, current rookie source for the Redraft V1 engine exists to refresh from.**

### What was restored, and how

The runtime architecture does **not** absolutely require exclusion — it already has a real pathway for exactly this situation: manual assets (`_asset_pool()` in `redraft_draft_room_v1_service.py`), the same mechanism K/DST already use, always with `replacement_adjusted_value=None` / `confidence="NOT MODELED"` (the architecture has no way to carry a real value through this pathway — it is visibility-only by design). This is the closest existing, honest equivalent to "DATA_LIMITED."

The existing `import_udk_unmodeled_skill_assets()` facade helper was **not** used — it specifically requires `identity_status=UNMATCHED` rows (players NWR has no player_id for at all), which mischaracterizes this case: these 78 rookies **do** have real, known NWR player_ids already present in the governed CSV; they are freshness-blocked, not identity-unmatched. Using that helper would have misrepresented the reason. Instead, used the same underlying, real `write_manual_assets_file()`/`merge_manual_assets()` primitives directly, with identity (player_id, name, position, team) read straight from the real governed CSV row for each of the 78 — **nothing fabricated** — and an explicit, honest `authority` label disclosing exactly why: *"MANUAL — DATA_LIMITED: real 2026 rookie identity, currently excluded from governed ranking (source_as_of 2026-07-30 exceeds the 30-day freshness window). Visible for draftability only; NOT MODELED — no NWR score/value assigned."*

Applied **only** to the practice profile ("2026 KHA High Stakes League — PRACTICE 20260905"); the real KHA profile and its TEST sibling were not touched.

### Result

| | Count |
|---|---:|
| Original exclusions | 78 (+2 separate position-conflict exclusions, unrelated) |
| Restored to visibility | 78 |
| Still fully invisible | 2 (position-conflict, pre-existing, not addressed tonight) |
| Restored WITH a real NWR score | 0 |

**Player Score / market / Cost of Waiting inputs, checked precisely, not assumed**: restored rookies correctly show `NOT MODELED` for Player Score (honest — no current governed projection exists) and correctly contribute `0.0` to any roster-value calculation if drafted (same treatment as K/DST, verified via `RosterPlayer`'s `None`-value handling). **Real market context is present for at least some of them** — spot-checked Jeremiyah Love (RB), who carries a real `overallAdp: 34.2` from the owner's own previously-pasted Consensus ADP snapshot, confirming market/ADP data is scientifically present and usable independent of the stale internal projection, exactly where supported.

## 2. The "4-team F4" claim — independently verified, and corrected

**Verified from the actual code, not the prose, per instruction.** `scripts/build_team_score_calibration_corpus_v1.py:79` and every downstream F4 script: `team_count = min(4, max(2, len(player_ids) // 6))`, passed directly into `LeagueProfile(team_count=team_count, ...)` (`_profile_for_season`, confirmed by direct code read). This value is the real `LeagueProfile.team_count` used to build every simulated comparable-league population, every replacement-value calculation, and every draft-slot sample throughout the entire Team Score research program (Recovery V1, Root-Cause Decomposition, Finalization/F4, the 2016 holdout, and the 2024 holdout).

**The specific confusion the owner asked me to check for — "4 draft slots sampled" vs. "4-team league" — is NOT what happened.** `for draft_slot in range(1, team_count + 1)` samples every slot of the simulated league, and `team_count` in that range **is** the same 4 used as the league size — there were exactly 4 draft slots because the simulated league itself had exactly 4 teams. No slot/league-size mixup exists.

**What I actually found is a different, more significant issue, and I'm not going to soften it**: checking `len(player_ids) // 6` directly against the real per-season player counts (84–184 players across the 9 development seasons) shows it evaluates to **14–30** every season — the `min(4, ...)` cap is what forces the result down to 4, not data scarcity. The dataset could easily have supported simulating an 8-, 10-, 12-, or even ~20-team league. **No documented rationale for choosing 4 exists anywhere in the research history** (checked every script that defines this formula, and every report that mentions `team_count`) — it appears to be an arbitrary constant, first introduced in `run_historical_calibration_readiness_v1.py` during early research tooling, and copy-pasted forward, unquestioned, into every subsequent Team Score script tonight, including my own new ones. My own prior reports' characterization of this as "this dataset's real, verified historical league format" was **overstated** — it is not a property of the historical data; it is an unexplained parameter choice of the analysis pipeline. This report corrects that characterization.

**Historical league configuration actually used, for the record**: `_HISTORICAL_ROSTER = RosterSettings(qb=1, rb=1, wr=1, te=1, flex=1, superflex=0, k=0, dst=0, bench_size=1)` (6 total roster slots), scoring format derived per-row from each season's own `scoring_format` field (Non-PPR/Half-PPR/PPR — not fixed), `team_count=4` (arbitrary, as established above), all 4 draft slots sampled every season.

**Whether replacement/market transforms depend on team_count — verified directly in code, mechanically confirmed yes for most of F4's features**:
- `_required_position_counts(profile)` (`redraft_engine_v1_service.py:1004-1012`) is literally `profile.team_count * profile.roster.<position>` — replacement level, and therefore `replacement_adjusted_value` (the input to `optimal_lineup` and `all_roster_sum`), is directly, mechanically team_count-dependent. At team_count=16, the replacement baseline sits at a materially deeper roster spot than at team_count=4 — the same player pool produces **different values** at different league sizes.
- `nwr_rank_sum` is indirectly team_count-dependent (it's the sort order of the team_count-dependent value above).
- `market_adp_percentile_sum` is **not** team_count-dependent — it's a real-market, within-season ADP percentile, computed independent of any simulated league's size. This is F4's most portable component.
- The oracle target itself (`realized_optimal_lineup_value` percentile) is also computed against a team_count-dependent simulated comparable-league population, so even the validation's own target scale is tied to team_count=4.

**Portability across 8/10/12/16-team leagues, as requested**: `optimal_lineup`, `all_roster_sum`, and (indirectly) `nwr_rank_sum` are **not** portable without a fresh recalibration at the target league size (their numeric scale and the model's fitted means/stdevs/weights were derived entirely from team_count=4 data). `market_adp_percentile_sum` is the one component with a real claim to portability across league sizes, since it never depended on the simulated league at all. This **reinforces, on stronger and more precise mechanical grounds, the decision already made not to wire F4 into KHA's 16-team league** — not because 4-vs-16 was a labeling mixup, but because the actual replacement-value arithmetic underneath most of F4's features genuinely does not transfer.

**Per instruction, F4 is not being wired into KHA as a result of this finding.** The overnight readiness report's characterization is corrected here rather than edited in place, to preserve the original record; a pointer has been added there.

## 3. Today's practice draft — re-verified after both fixes

Full re-run on the real installation, real (now-approved) data, real manual-asset restoration in place:

| Check | Result |
|---|---|
| Fresh start | ✅ 8 auto-advanced picks (owner slot 9) |
| Rookies visible in pool | ✅ 78 manual assets present; health `"Ready — 2 blocked players visible"` (only the pre-existing position-conflict pair) |
| Recommendations generate | ✅ 8 candidates, 2.44s (FAST preset, one-time simulation warm-up; well within a draft clock) |
| Team Score implementation actually in use | ✅ `team-score-v2` — confirmed live, unchanged, per the standing decision |
| Owner pick recorded | ✅ (Jonathan Taylor) |
| Cost of Waiting present | ✅ (3.1) |
| Undo | ✅ 23→22 |
| Reset | ✅ clean 8-pick state, ready for tomorrow |
| **Real KHA board untouched** | ✅ **157 picks before, 157 after — byte-identical, confirmed a second time** |

### Exact current-data timestamp

```
source_sha256: e483caaedc236140bcdfeccdd759bf8726a4b231bbaf3e9fdc461873d3921c25 (unchanged all night)
player_rows: 530  |  blocked_rows: 78 (visible-but-unscored, see above)  |  season: 2026
approval: admission_scope=NWR_PRACTICE_DRAFT, approved_by="Spencer Colety (owner, explicit
  in-session practice-draft authorization, 2026-09-05)", valid_until=2026-09-05 (today only)
component source_as_of: veterans 2026-08-08, rookies 2026-07-30 (disclosed, unchanged)
```

## Verdict

**`YELLOW_PRACTICE_DRAFT_READY_ROOKIE_LIMITATION_REMAINS`**

Not GREEN_FULL_POOL: the 78 rookies are now genuinely visible and draftable (a real improvement from last check), but they carry **no NWR Player Score, Team Score contribution, or Cost of Waiting figure** — correctly and honestly, since no current governed projection exists for them and none was fabricated. That is a real, disclosed limitation for a "full pool," not a cosmetic one. Everything else — the governance approval, the live mechanics, Team Score's implementation, and the real KHA board's integrity — is verified clean.

No production code modified. No push. No merge. No deployment.
