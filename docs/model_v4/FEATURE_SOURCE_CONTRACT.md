# Model v4 Feature And Source Contract

This contract defines what Model v4 is allowed to treat as football evidence.
If a future scoring rebuild or UI surface disagrees with this file, the rebuild
is wrong until proven otherwise.

Model v4 is still frozen for audit. This contract does not change formulas,
scores, readiness gates, or player ranks.

## Source Context

Authoritative v4 context:

- `docs/model_v4/LEAGUE_RULES_LOCK.md`
- `docs/model_v4/OFFSEASON_RANKING_SHEET_LOCK.md`
- `docs/model_v4/FOOTBALL_SANITY_BELIEFS.md`
- `docs/model_v4/MODEL_V4_SPEC.md`

Machine-readable table:

- `docs/model_v4/FEATURE_SOURCE_CONTRACT.csv`
- `docs/model_v4/PHASE_10F_SOURCE_TRUST_CONTRACT.csv`

Phase 10F extends this contract for the newly collected RotoWire NFL, first-down,
return, college/prospect, ADP, mock-draft, identity, and source-gap files. The
Phase 10F extension is the required lane map before any feature matrix may use
those fields.

## Classification Definitions

| Classification | Meaning |
| --- | --- |
| `scoring_allowed` | May contribute to a v4 scoring lane after identity, freshness, receipt, and tests pass. |
| `scoring_allowed_with_confidence_penalty` | May contribute, but must carry an explicit source limitation or volatility penalty. |
| `context_only` | May explain decisions or confidence, but cannot directly increase private/model value. |
| `review_only` | May appear in audit reports or receipts, but cannot affect active scoring yet. |
| `rejected` | Must not be used for scoring, confidence boosts, or hidden defaults. |
| `unavailable` | Not available from a safe free/public structured source. The absence must be visible. |

## Source Trust Tiers

| Tier | Allowed Treatment |
| --- | --- |
| `structured_public_officialish` | Public structured source such as nflverse/nflreadr/Sleeper/DynastyProcess where fields and IDs are stable enough to validate. |
| `structured_export_or_public_projection` | Projection source with raw stat fields that can be exported and recomputed to exact LVE scoring. |
| `structured_crosswalk_or_sleeper` | Identity and roster sources used to join players safely. |
| `official_league_file` | League rules, roster, ranking sheet, and draft/pick inputs. Rule context only unless the file defines actual scoring settings. |
| `market_context_source` | Trade or liquidity source. Never private football value. |
| `structured_draft_source` | NFL draft capital or prospect source with factual fields. |
| `structured_sourced_prospect_data` | College/prospect data with stable source, fields, and dates. |
| `derived_estimate` | Locally estimated value that must be labeled and penalized. |
| `restricted_or_missing_source` | Missing from safe free/public sources or blocked by terms/licensing. |
| `manual_unverified_or_malformed` | Agent/manual stat tables or malformed exports. Rejected until transformed into a validated structured import. |

## Model Lane Rules

### Dynasty Asset Value

May use only football evidence: production, real first downs, targets, carries,
derived usage, snap share with proxy penalty, age/bio, identity, carefully
qualified projections, and young-player priors when lifecycle-eligible.

It must not use:

- league-rank top-five mechanics
- trade market/liquidity
- rejected manual tables
- hidden neutral defaults as evidence
- unavailable route metrics

### Roster Decision Value

May use Dynasty Asset Value plus Niners roster context and the required
top-five rule. It may not treat league rank as player quality.

### Required Top-Five Release Analysis

Uses only the `Roster's League-Rank Top Five` as the candidate pool. Non-top-five
players may appear as secondary roster context, but cannot be the required
top-five release candidate.

### Trade Context

May use trade market/liquidity, but market data contributes 0 percent to private
football value. Missing/default market data must never create a fake edge.

### Draft Value

Uses draftable players only. Protected roster players are excluded unless a
manual draftable override is explicitly marked review-needed.

### Confidence

Confidence controls language strength. Missing or proxy-heavy data should
produce visible review language. It must not silently bury uncertainty.

## Contract Table

| Input | Classification | Source Status | Allowed Lane | Receipt Requirement |
| --- | --- | --- | --- | --- |
| nflverse production | `scoring_allowed` | `imported_real_data` | Dynasty, roster, draft | Raw stat window, source season/file, normalized score, contribution. |
| rushing first downs | `scoring_allowed` | `imported_real_data` | Dynasty, roster, draft | Raw rushing first downs, 0.4 scoring constant, contribution. |
| receiving first downs | `scoring_allowed` | `imported_real_data` | Dynasty, roster, draft | Raw receiving first downs, 0.4 scoring constant, contribution. |
| targets | `scoring_allowed` | `imported_real_data` | Dynasty, roster, draft | Raw targets, games, target rate if derived, contribution. |
| carries | `scoring_allowed` | `imported_real_data` | Dynasty, roster, draft | Raw carries, games, carry share if derived, contribution. |
| target share | `scoring_allowed` | `derived_real_data` | Dynasty, roster, draft | Player targets, team denominator, season/week scope, contribution. |
| carry share | `scoring_allowed` | `derived_real_data` | Dynasty, roster, draft | Player carries, team denominator, season/week scope, contribution. |
| red-zone usage | `scoring_allowed_with_confidence_penalty` | `derived_real_data` | Dynasty, roster, draft | Red-zone carries/targets, sample size, volatility warning. |
| goal-line usage | `scoring_allowed_with_confidence_penalty` | `derived_real_data` | Dynasty, roster, draft | Goal-line carries/targets, sample size, volatility warning. |
| snap share | `scoring_allowed_with_confidence_penalty` | `imported_real_data` | Dynasty, roster, draft | Offensive snaps, snap share, games, proxy warning. |
| route participation | `scoring_allowed_with_confidence_penalty` | `licensed_structured_export_required` | Dynasty, roster, draft | Direct route-participation source or derivation denominator, source name, warning if proxy-only. |
| routes run | `scoring_allowed_with_confidence_penalty` | `licensed_rotowire_export` | Dynasty, roster, draft | Routes run, season, source file/hash, route sample-size warning. |
| TPRR | `scoring_allowed_with_confidence_penalty` | `licensed_rotowire_export` | Dynasty, roster, draft | Targets per route run, source file/hash, sample-size warning. |
| YPRR | `scoring_allowed_with_confidence_penalty` | `licensed_rotowire_export` | Dynasty, roster, draft | Yards per route run, source file/hash, sample-size warning. |
| projections | `scoring_allowed_with_confidence_penalty` | `projection_recomputed_lve` | Dynasty, roster, draft | Source, date, raw projected stats, recomputed LVE points, projection status. |
| estimated first-down projections | `review_only` | `estimated_from_history` | Projection review | Estimate method, historical rate, estimated label, confidence penalty. |
| injury status/history | `context_only` | `context_only` | Roster, trade, confidence | Injury source, date, status, games missed, confidence effect. |
| age/bio | `scoring_allowed` | `imported_real_data` | Dynasty, roster, draft, lifecycle | Birth date or age, years experience, source, age bucket. |
| identity | `scoring_allowed` | `identity_gate` | All joins | Match method, IDs, confidence, ambiguity warning. |
| league rank | `context_only` | `rule_context_only` | Required top-five release, roster context | Roster league rank, top-five slot, rule-only label. |
| trade market/liquidity | `context_only` | `trade_context_only` | Trade context, model vs market | Market source, date, liquidity status, no private value contribution. |
| young-player draft capital | `scoring_allowed_with_confidence_penalty` | `young_bridge_prior` | Dynasty, roster, draft, lifecycle | Round, pick, prior score, decay weight, NFL evidence weight. |
| college/prospect profile | `scoring_allowed_with_confidence_penalty` | `prospect_context` | Draft value, young bridge review | College source, metric, normalization, subjective warning. |
| manual agent player-stat tables | `rejected` | `rejected` | None | Rejected field log only. |
| restricted route data exports | `rejected` | `rejected` | None | Restricted-source rejection only. |
| supplied fantasy projection points | `rejected` | `rejected` | None | Supplied-points rejection warning. |

## Hard Guardrails

1. League rank is rule context only. It never raises Dynasty Asset Value.
2. Market value is trade context only. It never changes private/model value.
3. Routes run, TPRR, and YPRR may be used only from licensed structured exports
   such as the user's local RotoWire data. Direct route participation requires a
   direct source or a validated denominator; snap share cannot masquerade as
   route participation.
4. Snap share is allowed only as snap share. It cannot masquerade as route
   participation.
5. Supplied fantasy projection totals are rejected unless recomputed from raw
   stat columns using the LVE scoring constants.
6. Estimated first-down projections are review-only until estimator validation
   and explicit acceptance move them to a penalized scoring lane.
7. Unsourced healthy injury rows cannot boost confidence.
8. Young-player draft capital is lifecycle-limited. It cannot affect established
   veterans.
9. Manual or agent-compiled stat tables are rejected unless they pass a strict
   structured-import contract.
10. Hidden neutral defaults must appear as imputation or unavailable in receipts
    and source coverage.

## Required Tests Before Formula Work

Before Model v4 formulas can use this contract, tests must prove:

- rejected/manual sources are not used in scoring
- route fields cannot promote without an approved structured source
- market changes do not move private/model value
- league rank does not move Dynasty Asset Value
- identity ambiguity blocks or review-labels affected rows
- estimated first-down projections are labeled estimated, not direct
- local or supplied projection totals cannot create fake confidence
- unsourced healthy injury context cannot boost confidence
- production, first-down, usage, and snap rows preserve source status into
  normalized features and receipts
- young-player draft capital does not score established veterans

## Phase 1A Exit Criteria

- This contract exists in markdown and CSV form.
- Every requested potential input is classified.
- Each input has source trust, source status, lane allowance, confidence impact,
  receipt requirement, and test requirement.
- No formulas have changed.
- Static check passes.
