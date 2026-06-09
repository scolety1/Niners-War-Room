# Rookie Draft Pick Trade Provenance Audit

Date: 2026-05-25

## Verdict

The 2026 NFL draft-pick trade history is useful, but it should not directly change
private player value yet.

Use it for:

- draft-capital provenance
- landing-spot explanation
- audit checks against final draft order
- context on whether a team used an original pick, veteran-trade pick, trade-up pick,
  or trade-down pick

Do not use it for:

- direct talent scoring
- automatic rookie ranking boosts
- market or ADP replacement
- final rookie pick recommendations

## Why This Matters

The model now admits factual draft capital from
`local_exports/model_v4/draft_capital/latest/rookie_draft_capital_2026.csv`.
That file correctly gives each rookie a round and overall pick. The trade-history
list adds a different question:

> Did the NFL team spend its own pick, a previously acquired pick, a trade-up pick,
> or a trade-down pick on the player?

That can explain landing spot and team behavior, but it is noisier than draft
capital itself. A pick may have been acquired months earlier for a veteran trade,
not because the drafting team targeted the eventual rookie. A draft-day trade-up
is more meaningful than a pick that moved through several unrelated veteran deals.

## Key Fantasy-Relevant Findings From User-Provided Trade Notes

| Player | Pick | Team | Trade-context reading | Formula lane |
|---|---:|---|---|---|
| Jeremiyah Love | 3 | ARI | No user-provided trade note found for pick 3; treat as clean premium capital. | draft_capital evidence only |
| Carnell Tate | 4 | TEN | No user-provided trade note found for pick 4; treat as clean premium capital. | draft_capital evidence only |
| Jordyn Tyson | 8 | NO | No user-provided trade note found for pick 8; treat as clean premium capital. | draft_capital evidence only |
| Kenyon Sadiq | 16 | NYJ | Pick came from Colts in Sauce Gardner trade; strong NFL draft capital, but trade was veteran-driven rather than clear Sadiq-specific trade-up. | context-only provenance |
| Makai Lemon | 20 | PHI | Pick moved GB to DAL in Micah Parsons trade, then DAL to PHI on draft night. Draft-day movement makes this useful landing/context evidence, but still not standalone talent. | context-only provenance |
| KC Concepcion | 24 | CLE | Pick came from Jaguars/Browns Travis Hunter trade. High draft capital is real; pick path is context only. | context-only provenance |
| Omar Cooper | 30 | NYJ | Pick moved MIA to SF in Jaylen Waddle deal, then SF traded down to NYJ at 30/33. This is important for explaining why NYJ landed Cooper and SF landed Stribling. | context-only provenance |
| Jadarian Price | 32 | SEA | No user-provided trade note found for pick 32; treat as late first-round capital. | draft_capital evidence only |
| De'Zhaun Stribling | 33 | SF | SF traded down from 30 to 33 and added pick 179. Context suggests trade-down outcome, not necessarily an aggressive trade-up for Stribling. | context-only provenance |
| Denzel Boston | 39 | CLE | No direct fantasy-useful trade-intent signal beyond final pick/team in supplied list. | draft_capital evidence only |
| Germie Bernard | 47 | PIT | Pick moved Colts to Steelers during draft. Context can explain landing but should not move value by itself. | context-only provenance |
| Eli Stowers | 54 | PHI | No strong player-specific trade signal from supplied notes. | draft_capital evidence only |
| Mike Washington | 122 | LV | Midday-three pick moved through Falcons/Raiders trade. Useful context, but day-three trade paths are noisy. | context-only provenance |
| Skyler Bell | 125 | BUF | Pick changed hands multiple times. Useful for provenance; not a talent signal. | context-only provenance |
| Kaelon Black | 90 | SF | Pick came to SF through a trade involving pick 30/Chris Johnson/Omar Cooper. Useful Niners context, not automatic value boost. | context-only provenance |

## Safe Model Treatment

Recommended future fields:

- `pick_trade_provenance_status`
- `pick_acquired_via_trade`
- `pick_trade_path_summary`
- `trade_context_type`
- `trade_context_allowed_use`
- `trade_context_private_value_allowed`

Suggested values:

- `original_pick_or_no_trade_note`
- `pre_draft_veteran_trade_pick`
- `draft_day_trade_up_context`
- `draft_day_trade_down_context`
- `multi_step_trade_path_noisy`
- `conditional_pick_did_not_convey`

Hard rule:

`trade_context_private_value_allowed = false`

Exception to review later:

If a team trades up on draft day and immediately selects an offensive rookie, that
can become a very small landing-spot or team-intent context component after audit.
It still should not override production, draft capital, age, athletic profile, or
identity confidence.

## Specific Model Implications

1. Draft capital repair remains valid.

   Round and overall pick should stay admitted prospect-prior evidence.

2. Pick-trade provenance should be added as context-only first.

   The model should show it in the Prospect Board/Draft Room so the user can
   understand why a player landed with a team.

3. The SF trade chain deserves a Niners-specific note.

   The 49ers moved from pick 27 to 30/90, then from 30 to 33/179. This makes
   De'Zhaun Stribling and Kaelon Black important Niners review rows, but it does
   not mean the model should force-rank them higher.

4. Multi-step day-three trade paths are noisy.

   Players like Skyler Bell, Mike Washington, and late TEs/RBs should not receive
   value boosts just because the pick changed hands.

## Recommended Next Step

Convert the full user-provided trade list into a machine-readable local source:

- `local_exports/model_v4/draft_capital/latest/rookie_draft_pick_trade_provenance_2026.csv`

Then add a review-only overlay:

- `rookie_draft_pick_trade_provenance_review_rows.csv`
- `rookie_draft_pick_trade_provenance_warnings.csv`

The overlay should join by `overall_pick` first, then validate player name. It
should not fuzzy join silently.

## Current Readiness

This trade history does not block rookie analysis. It is a useful explainability
upgrade and a source-audit improvement, not a formula blocker.
