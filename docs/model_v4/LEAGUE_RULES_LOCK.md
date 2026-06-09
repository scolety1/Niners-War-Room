# Model v4 League Rules Lock

This is the canonical rule source for Model v4. If app logic, scoring constants,
decision gates, or UI labels disagree with this file, the code is wrong until
proven otherwise.

## Source Files

- Original PDF: `docs/model_v4/source_docs/FFL_Rules_CURRENT_080125_DRAFT_FOR_SLEEPER_TRANSFER_2.pdf`
- Extracted text: `docs/model_v4/source_extracts/FFL_RULES_CURRENT_080125_DRAFT_FOR_SLEEPER_TRANSFER_2.txt`
- Extracted on: 2026-05-15

## Locked League Context

- League: Las Vegas Enginerds / FFL.
- Teams: 10.
- Format: dynasty with offseason roster declaration and offline mixed draft.
- Official 2026 Roster Declaration Day / drop date from user: June 15.
- The model should be usable before June 15 so trade and roster work can happen
  before final declarations.
- User's official team name: Niners.
- Model scope: QB, RB, WR, TE skill-position decisions unless explicitly expanded.
- Kicker exists in the rules and regular-season lineup, but user confirmed they
  do not care about kickers for model value. Model v4 should ignore kickers for
  value/ranking decisions and only account for them where roster mechanics
  require it.
- Team defense is no longer applicable starting in the 2024 regular season.

## Roster And Lineup

Current roster rules from the PDF:

- Offseason roster limit: 24 players before Roster Declaration Day.
- Roster Declaration Day keeper limit: 23 players starting in 2026.
- Pre-season roster limit after the 5-round draft: 28 players until Cut Day.
- Cut Day roster limit: 24 players.
- Regular season roster: 24 players plus two IR spots.
- Starting lineup from 2025 onward:
  - 1 QB
  - 2 RB
  - 3 WR
  - 1 TE
  - 2 WR/RB/TE flex
  - 1 K
  - 14 bench
- IR during 2026 regular season: two IR spots.
- IR during 2026 pre-season: zero IR spots.

Model implication:

- Cross-position value must reflect 1QB, 2RB, 3WR, 1TE, 2 flex, no TE premium.
- Kicker should be treated as a roster mechanics detail, not part of the dynasty
  value model by default.

## Scoring Constants

Offensive scoring locked from the PDF:

| Event | Points |
| --- | ---: |
| Passing yards | 1 per 30 yards |
| Passing TD | 3 |
| Interception | -1 |
| Rushing yards | 1 per 10 yards |
| Rushing TD | 4 |
| Receiving yards | 1 per 10 yards |
| Receiving TD | 4 |
| Return yards | 1 per 30 yards |
| Return TD | 4 |
| Two-point conversion | 2 |
| Fumble lost | -1 |
| Rush or receiving first down | 0.4 |
| Reception | 0 |

Kicker scoring locked from the PDF:

| Event | Points |
| --- | ---: |
| FG 0-19 | 2 |
| FG 20-29 | 2 |
| FG 30-39 | 2 |
| FG 40-49 | 3 |
| FG 50+ | 4 |
| PAT made | 1 |

Model implication:

- No PPR.
- No TE premium.
- Passing interceptions are -1, not -2.
- First-down scoring applies only to rushing and receiving first downs.
- Projection recompute must not use generic fantasy points from outside sources.
  It must recompute this exact LVE scoring.

## Roster Declaration Rule

The league uses an official Offseason Ranking Sheet from a reputable third-party
source. That ranking sheet is a rule signal, not the model's player-quality
truth.

Locked rule:

- Every rostered player receives a league rank from the official Offseason
  Ranking Sheet.
- Starting in 2026, each team may protect up to 23 players.
- On Roster Declaration Day, each team may retain the rights to up to four of
  the top five ranked players on its current roster.
- At least one of the top five ranked players on each roster must be released
  to the free-agent pool.
- If a team does not submit protections, the commissioner protects the top 23
  players by the Offseason Ranking Sheet.

Required v4 wording:

- Use `Roster's League-Rank Top Five`.
- Use `Required Top-Five Release Slot`.
- Use `Top-Five Rule Status`.
- Do not use `top five` without context.

Model implication:

- Forced-release logic must choose from the roster's league-rank top-five group
  only.
- Non-top-five drops can be secondary roster context, but they must never be
  the primary forced-release candidate.
- League rank should not be used as model player quality.

## Draft Rules

- Draft type: offline draft.
- Draft length: 5 rounds.
- Teams: 10.
- Total scheduled picks: 50 before traded-pick complications.
- Post-draft players: free agents.
- Draft occurs one week after Roster Declaration Day starting in 2026, subject
  to commissioner discretion.
- After the draft, roster limits increase to 28 until Cut Day.

Model implication:

- Draft Board should use draftable players only:
  - incoming rookies
  - officially released veterans
  - legal free agents
  - manual adds marked as review-needed
- Protected roster players must not appear in the normal draftable pool.
- Roster decision readiness can pass before official released veterans are
  loaded.
- Draft readiness cannot pass until the draftable pool is complete enough for
  the actual room.

## Trade And Waiver Rules

- Max trades: no maximum.
- Max moves: no maximum.
- Draft picks may be traded from the next three annual drafts.
- FAAB begins in the 2026 pre-season.
- Starting pre-season FAAB: $100 per team.
- Starting regular-season FAAB: $100 per team.
- FAAB may be traded for players or draft picks.

Model implication:

- Trade Lab can evaluate model value, market/liquidity, roster spot cost, and
  likely acquisition friction.
- Market/liquidity must remain separate from private football value.
- FAAB can eventually become a trade-context field, but it should not affect
  dynasty asset value.

## Open Verification Items

These are not blockers to start Model v4, but they should be confirmed before
unlocking readiness gates:

1. Official 2026 Offseason Ranking Sheet source/file has been received and
   archived. See `docs/model_v4/OFFSEASON_RANKING_SHEET_LOCK.md`.
2. Convert the multi-column roster/ranking PDF into a structured import before
   it drives production code.
3. Current traded draft-pick ownership should be treated as correct in Sleeper,
   but user can provide a roster/pick export if needed.
4. Whether Sleeper replaced Yahoo as the operating website for 2026, despite
   the PDF still naming Yahoo in an older rule section.
5. Whether any local league ruling changes the PDF scoring constants inside
   Sleeper settings.

## V4 Gate Rule

No app surface may show roster-ready, draft-ready, final-money-ready, or
decision-ready unless its readiness gate has been rebuilt and tested against
this rules lock.
