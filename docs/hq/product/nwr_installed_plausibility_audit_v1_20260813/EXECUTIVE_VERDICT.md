# NWR installed desktop plausibility / calibration audit V1

Audit date: 2026-08-13  
Installed candidate: `codex/nwr-desktop-installed-agent-fixes-20260813` at `a21a5197629713ba74a6d4b8df65e10de4b562ff`  
Tree: `f0b4f47820f2e316bec30f4b71d071009793c948`  
Verdict: **YELLOW_NWR_INSTALLED_RESULTS_HAVE_QUESTIONABLE_OUTLIERS**

## Overall answer

**MOSTLY.** NWR's installed Dynasty and Redraft outputs are generally coherent, directionally monotone, format-aware, and within a defensible fantasy-football possibility space. The audit found no arithmetic inversion, probability-bound failure, outcome-window nesting failure, or evidence that the installed system is reading the wrong canonical ranking/rookie/outcome files. It did find several current rankings that are large independent calls, decision-language coarseness in the Trade Analyzer, a range-label clarity risk, a stale/optional market-context divergence, and one intermittent packaged-sidecar launch warning. Those are reasons for owner scrutiny, not proof that the core model is broken.

No model, projection, rank, trade rule, authority file, or owner workspace was changed.

## Dynasty rankings

The top board is recognizably plausible but intentionally non-consensus. Puka Nacua at #1 is an aggressive but defensible call: contemporary public 1QB lists place him around #4-8. The strongest questionable cluster is not the top overall player; it is the relative treatment of elite young tight ends and several young cornerstone players. NWR has Kyle Pitts #17, Brock Bowers #45, and Ashton Jeanty #46, while contemporary public lists generally place Bowers and Jeanty in roughly the top 5-23. Courtland Sutton at #29 is also a major pro-veteran call versus public dynasty neighborhoods around #100-145.

Classification: **plausible board with several YELLOW outliers**, especially Bowers/Jeanty, Sutton, and the extreme tail treatment of some 1QB quarterbacks.

## Trade Analyzer

The original deal — give Luther Burden, Chris Bell, and a 2027 first; receive George Kittle, Chuba Hubbard, Brock Purdy, and a 2028 second — returned `COUNTER`, preferred the current/outgoing side, and carried `MEDIUM` confidence. That is broadly aligned with independent 10-team 1QB reasoning: the younger receiver plus earlier first retains stronger long-horizon and flexibility value, while Purdy's positional scarcity is limited and the incoming side carries age/role risk.

Perturbations moved the internal dimensions in the correct direction. Removing Purdy worsened the incoming package to `REJECT`; upgrading Kittle to Puka strongly improved incoming production/upside dimensions; changing balanced to contending helped the veteran-heavy incoming side. The top-line ordinal recommendation is coarse: the Puka upgrade remained `COUNTER` and an obviously poor Puka-for-Gabe-Davis-plus-second package only reached `LEAN_REJECT`. This is a **decision-language coarseness watch**, not a proven valuation inversion.

## Player Compare

The five compare pairs were internally consistent with the ranking board and time horizon. Puka/Chase, Taylor/Achane, Tetairoa McMillan/Davante Adams, Sutton/Carnell Tate, and Josh Allen/Purdy all produced explainable short-, medium-, and long-horizon differences. The system correctly refused to force a common production-scale lean when rookie evidence was not comparable.

The main presentation caveat is that `Floor`, `Expected`, and `Ceiling` contain different signal types (downside probability, research neighborhood, ceiling probability). They are not three numbers on one ordered scale, even though the labels invite that reading.

## Rookie Review

Jeremiyah Love (#1, NFL pick 3), Carnell Tate (#8, NFL pick 4), and KC Concepcion (#14, NFL pick 24) are in plausible neighborhoods and their confidence caps truthfully expose missing recruiting/combine normalization. De'Zhaun Stribling remains visibly blocked. Contemporary NFL evidence says San Francisco selected him at pick 33, so the block is a current-information/identity-governance blind spot; importantly, NWR fails closed rather than fabricating a score.

## Market gaps

The installed app's July 17 snapshot was explicitly 27 days stale and display-only. The sign convention was correct in all sampled rows: positive gaps meant NWR higher and negative gaps meant market higher. Major installed calls included Joe Mixon #97 versus market #316.8 (+220), Calvin Austin #100 versus #310 (+210), Darius Slayton #89 versus #296 (+208), and Sutton #29 versus #99 (+71).

The disposable facade did not resolve exactly the same optional market artifact as the installed package (for example, it showed Joe Mixon at 342 rather than 316.8). Canonical board/rookie/outcome resources matched byte-for-byte, so this is isolated to optional stale market context. Installed UI values are authoritative in this report.

## Outcomes

All sampled probabilities were within 0-100 and all threshold/window nesting checks passed. Repeated probability patterns exist across players in the same position/tier families. They look like coarse calibration buckets, not arithmetic duplication or leakage. Treat exact-looking probabilities as calibrated bands rather than bespoke player forecasts.

## Redraft

The installed Standard profile rendered 608 ranked players and matched the isolated backend result. All four built-in profiles produced sensible scoring and positional shifts. Superflex increased QB opportunity cost without contaminating Dynasty ranks. PPR and half-PPR moved high-catch receivers in the expected direction. Projection evidence is uniformly labeled low where appropriate.

## Courtland Sutton

Sutton is aggressive, but not out of realm. Installed results were #52/WR12 Standard, #46/WR13 half-PPR, #41/WR14 PPR, and #49/WR14 Superflex PPR. His projection — 124 targets, 74 catches, 1,017 yards, seven touchdowns — is a plausible high-volume veteran line rather than an impossible efficiency assumption. Contemporary public sources range from WR24-30 and about overall 52-57, making NWR materially higher at WR12-14 but close in overall draft cost for shallow formats. Dynasty #29 is the more aggressive disagreement.

## Opportunity versus efficiency

NWR does not simply rank target volume. Sutton and Wan'Dale Robinson receive meaningful volume credit, but a low-efficiency Jerry Jeudy projection is not promoted to the top board, while lower-volume/high-efficiency Alec Pierce remains prominent. The system appears to blend prior production, opportunity, efficiency, age, and role evidence. The main watch is that role persistence can dominate when current depth-chart or injury context is missing.

## Largest defensible disagreements

- Puka Nacua #1: defensible independent ceiling/production call.
- Older productive veterans (Jonathan Taylor #4, Christian McCaffrey #18, Sutton #29, Davante Adams #47): an explicit win-now/production lean despite lifecycle risk.
- 1QB quarterback economics: Purdy #185 is not a claim that he is a poor NFL quarterback; it is a shallow-league replacement-value call.
- Efficiency/talent profiles such as Alec Pierce #27, Jameson Williams #26, Michael Wilson #34, and Parker Washington #44: NWR is willing to elevate per-route/explosive evidence ahead of generic market rank.

## Potential actual defects

No RED model defect was proven. Four YELLOW implementation/product risks remain:

1. Trade top-line language can be too sticky/coarse relative to large package changes.
2. Floor/Expected/Ceiling labels imply a shared ordered scale when the values are different signal families.
3. Installed and isolated runs can resolve different optional stale market artifacts.
4. One installed Dynasty launch logged an Application Control block for an extracted NumPy DLL before a contained retry reached ready state.

## What the owner should scrutinize first

1. Bowers #45 and Jeanty #46: determine whether the evidence chain intentionally supports the extreme discount.
2. Sutton #29 Dynasty: verify role sustainability and age/lifecycle assumptions, not just projection volume.
3. Quarterbacks below #140 in 10-team 1QB: interpret through replacement economics, then manually adjust for an owner's actual league behavior.
4. Any trade where the individual dimensions move strongly but the top-line label does not.
5. Any large market gap when the snapshot is stale or current team/route/status evidence is unavailable.

## Independent contemporary references

- PFF 2026 PPR big board: https://www.pff.com/news/fantasy-football-rankings-2026-post-free-agency-top-300-ppr-big-board
- ESPN 2026 PPR cheat sheet: https://g.espncdn.com/s/ffldraftkit/26/NFL26_CS_PPR300.pdf?adddata=2026CS_PPR300
- RotoBaller 2026 1QB dynasty ranks: https://www.rotoballer.com/fantasy-football-dynasty-1qb-rankings-post-nfl-draft-june-2026/1882143
- BR Fantasy 2026 dynasty ranks: https://www.brfantasyfootball.com/rankings/dynasty
- Hawk Dynasty 2026 ranks: https://hawkdynasty.com/dynasty-rankings/
- NFL 2026 draft reports: https://www.nfl.com/news/2026-nfl-draft-49ers--wr-de-zhaun-stribling-no-33-overall-pick

## Owner trust guide

Usually trust NWR strongly for league-specific replacement economics, transparent evidence gaps, direction-of-trade changes, and separating rookie review evidence from veteran production evidence. Double-check large veteran/role-persistence calls, elite young-TE discounts, extreme young-player discounts, and coarse trade labels. Trust current external context more when injuries, depth charts, team changes, rookie identity, or market data post-date NWR's evidence snapshot.

**YELLOW_NWR_INSTALLED_RESULTS_HAVE_QUESTIONABLE_OUTLIERS**
