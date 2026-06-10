# Current Board Credibility Review - 2026-06-10

## Executive Read

The current Rankings board is presentable, but it is not yet a fully trusted edge model. The latest age/format sanity work fixed obvious old-veteran crowding, but several remaining rows show deeper model-quality questions:

- established elite WR evidence may be underweighted when route/lifecycle/first-down receipts are missing
- short-window RB VORP can still outrank long-horizon WR profiles
- TE exception gates may still be loose for no-TE-premium
- 1QB QB cap may be too dependent on current VORP gap and too harsh on elite long-term QB profiles
- missing evidence is still doing too much work inside the single blended score

No scoring was changed in this pass. These findings should drive controlled shadow experiments, not hardcoded player moves.

## Guardrails Checked

- Market rank, league rank, ADP, public rankings, trade calculators, projections, RotoWire rankings/projections, prior draft history, and legacy active-pack scores remain blocked from private score.
- Team/roster tags are display-only.
- Legal draft pool remains pending.
- 2026 5.04 remains No Baseline / Manual late-round watchlist / No exact equivalence.
- Outcome percentages remain blank/in development.
- Decision Board remains untouched.

## Watch-Row Findings

| Player | Current rank | Score | Finding type | Read |
|---|---:|---:|---|---|
| Chase Brown | 22 | 49.1893 | formula issue / acceptable risk | Ranking is not from `[MY TEAM]`; it is driven by RB VORP and short-window three-down role. Historical replay says late-capital RB hits are real, including Chase Brown, but the current blended score needs clearer short-window upside vs dynasty floor separation. |
| CeeDee Lamb | 23 | 48.5992 | formula issue / data issue | Capped by missing route/lifecycle and partial first-down evidence. This looks like an established elite WR proof-lane gap, not a reason to use market rank. |
| Justin Jefferson | 25 | 47.7511 | formula issue / data issue | Similar to CeeDee: missing route/lifecycle/first-down receipts appear to suppress established multi-year WR evidence too much. |
| Jaylen Waddle | 33 | 41.1687 | data issue / formula candidate | Still carries RotoWire current-team/status warning and confidence cap. Historical replay specifically flags first-round WR underranks, including Jaylen Waddle, so this row should remain a WR proof-lane review case. |
| Trey McBride | 8 | 62.2578 | formula issue / human review | TE exception is receipt-backed by large private VORP, route/target, first-down, efficiency, and red-zone components. In no-TE-premium, top-10 still needs review because TE exception criteria may be too generous. |
| Puka Nacua | 1 | 83.0486 | acceptable model edge / data caveat | Rank is explainable by large private WR VORP and target/first-down evidence. Still capped by missing route/lifecycle receipts, so detail card should frame as strong private edge with source caveat. |
| Jaxon Smith-Njigba | 2 | 82.5714 | acceptable model edge / data caveat | Similar to Puka. Historical replay shows JSN as a prior underranked difference-maker, so a high rank is not automatically suspicious, but evidence/trust should be explicit. |
| Brock Bowers | 46 | 34.0184 | formula issue / data issue | TE small-gap cap suppresses him despite elite-TE exception flag. Could be right in no-premium if VORP gap is small, but young elite TE exception logic should be replay-tested. |
| Josh Allen | 19 | 50.3163 | acceptable model edge / watch | 1QB cap now keeps him relevant without top-10 dominance. Rushing age caution and capped trust are visible. |
| Patrick Mahomes | 84 | 24.1863 | formula issue / human review | One-QB small VORP gap cap may be too harsh for elite long-horizon QB profiles when current-year VORP is muted. Needs QB retained-value/horizon review. |
| Lamar Jackson | 144 | 15.0935 | formula issue / human review | Replacement-level QB cap plus rushing-age caution buries him. In 1QB this compression is expected, but the rank looks too low unless current VORP and horizon evidence justify it. |

## General Causes

### Established WR Proof Lane

CeeDee Lamb, Justin Jefferson, and Jaylen Waddle suggest the model lacks a source-safe proof lane for established multi-year WRs when proprietary route/lifecycle fields are absent. Missing data should cap trust, but it should not erase multi-year elite production if private evidence is otherwise strong.

Candidate shadow test:

- Add an established WR proof component using admitted multi-year production, first-down/yardage evidence, target/role evidence where available, age, and trust.
- Keep market/league ranks display-only.
- Do not hardcode WR names.

### RB Short-Window vs Dynasty Horizon

Chase Brown above CeeDee Lamb is not tag bias. It is a model-shape issue: RB VORP and short-window role can outrank longer-horizon WR evidence in a single blended score.

Candidate shadow test:

- Split RB upside from floor/safety.
- Add dynasty horizon caution for RBs whose value is short-window or role-fragile.
- Preserve late RB hit upside from historical replay.

### TE No-Premium Exception Gate

Trey McBride at #8 is explainable from private components, but still aggressive for no-TE-premium. Brock Bowers at #46 may be too compressed if the model is undercounting young elite TE horizon.

Candidate shadow test:

- Replay TE exception gates against historical TE outcomes.
- Require strong private receipts for top-board TE exceptions.
- Make older/status-risk TEs pay sharper caution.
- Keep no-TE-premium cap active.

### QB 1QB Cap

Josh Allen at #19 looks plausible. Mahomes at #84 and Lamar at #144 are the real concerns. The cap may be too dependent on current VORP/replacement gap and not enough on elite retained-value/horizon.

Candidate shadow test:

- Add an elite QB floor/horizon review lane for 1QB.
- Keep top-10 dominance blocked unless private evidence is overwhelming.
- Ensure elite QBs do not collapse below obvious replacement/depth rows without a clear explanation.

### Missing Evidence Policy

Several trustworthy players have warnings like missing route/target/snap evidence, missing lifecycle/role-shape evidence, or partial first-down confidence cap. The model needs to distinguish:

- evidence unavailable because source is missing
- evidence missing because player lacks the trait
- evidence stale or identity-conflicted

Candidate shadow test:

- Missing evidence should reduce confidence/trust.
- Missing evidence should not automatically crush established multi-year proof.
- Source conflicts should remain quarantined.

## What Not To Do

- Do not tune to consensus or public ranks.
- Do not hardcode Chase, CeeDee, Jefferson, Waddle, Trey, Puka, JSN, Mahomes, or Lamar.
- Do not use market rank or league rank as score inputs.
- Do not let `[MY TEAM]` or keeper status affect private score.
- Do not promote Decision Board from this review.

## Immediate Formula Recommendations

Recommended next work is shadow-only:

1. Established WR proof/floor lane.
2. RB short-window value vs dynasty horizon split.
3. TE no-premium exception replay.
4. 1QB elite QB floor/horizon review.
5. Missing-evidence policy audit.

Production formula work should wait until the model edge harness is expanded beyond rookie replay into current-player/veteran outcomes.

## Birthday Demo Classification

| Player | Classification |
|---|---|
| Chase Brown | defer until after birthday / formula candidate |
| CeeDee Lamb | formula issue / data issue |
| Justin Jefferson | formula issue / data issue |
| Jaylen Waddle | data issue / formula candidate |
| Trey McBride | human-review issue / TE formula candidate |
| Puka Nacua | acceptable model edge with source caveat |
| Jaxon Smith-Njigba | acceptable model edge with source caveat |
| Brock Bowers | formula issue / TE evidence review |
| Josh Allen | acceptable model edge / QB watch |
| Patrick Mahomes | formula issue |
| Lamar Jackson | formula issue |

## Next Research Questions

1. Can exact league-scoring outcomes be rebuilt from raw stats instead of generic fantasy totals?
2. Which private fields best predict retained dynasty value after years 2-3?
3. Can established WR proof be made source-safe without market contamination?
4. Can RB role/VORP be split into upside and horizon fragility?
5. Can TE/QB exception gates be validated in replay rather than judged by eyeballing current ranks?
