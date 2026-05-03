# Formula Spec

## Scores
V1 must calculate pick value, QB/RB/WR/TE private scores, confidence, keeper score, drop candidate score, keeper pressure, top-five release candidates, trade scores, acceptance chance, and war score.

## Formulas
Overall pick:
`overall_pick = 10 * (round - 1) + slot`

Final pick value:
`FinalPickValue = BaseCurve * FutureDiscount * CertaintyAdjustment + DeclarationAdjustment`

Keeper score:
`0.30*LongTermPrivateValue + 0.20*Next2YearStarterValue + 0.15*ScarcityBonus + 0.10*TradeLiquidity + 0.10*AgeCurve + 0.10*RiskAdj + 0.05*BuildFit`

Drop candidate score:
`0.45*InverseKeeperScore + 0.25*(OfficialValue - PrivateValue) + 0.15*RosterRedundancy + 0.15*DeclineRisk`

Confidence:
`0.35*data_completeness + 0.25*historical_cohort_size + 0.20*market_agreement + 0.20*model_separation`

War score:
`0.35*PrivateScore + 0.20*KeeperScore + 0.15*PickAdjustedValue + 0.10*ScarcityScore + 0.10*TradeLiquidity + 0.10*RiskAdjustedUpside`

Trade package scores:
- `PrivateTradeScore = IncomingPrivateValue - OutgoingPrivateValue`
- `MarketTradeScore = IncomingMarketValue - OutgoingMarketValue`
- `KeeperImpactScore = IncomingKeeperValue - OutgoingKeeperValue`
- `NinersEdgeScore = 0.50*PrivateTradeScore + 0.20*MarketTradeScore + 0.30*KeeperImpactScore`
- `OpponentBenefitScore = OutgoingOwnerValue - IncomingOwnerValue`, where `OwnerValue = 0.60*MarketValue + 0.40*KeeperValue`
- `AcceptanceChance = clamp(50 + 0.20*OpponentBenefitScore - 0.05*NinersEdgeScore - 0.30*PoliticalRisk, 0, 100)`

AcceptanceChance is a deterministic acceptance score for review bands, not a calibrated probability.
Trade labels are deterministic: OFFER, CONSIDER, HOLD, DECLINE, AVOID, and POLITICAL RISK.

## Weights
Use the brief's exact position formulas:
- QB: 0.40 draft_cap, 0.30 rush_profile, 0.15 start_path, 0.10 passing_trait, 0.05 environment.
- RB: 0.28 draft_cap, 0.22 opportunity, 0.15 production, 0.14 receiving, 0.12 elusiveness, 0.05 size_durability, 0.04 athleticism.
- WR: 0.27 draft_cap, 0.21 age_adj_production, 0.17 target_earning_efficiency, 0.12 breakout_class, 0.11 film_separation, 0.05 size_role, 0.03 athleticism, 0.04 environment.
- TE: 0.23 draft_cap, 0.22 receiving_production, 0.17 route_role, 0.12 athleticism, 0.11 film_receiving, 0.08 role_path, 0.04 age_timeline, 0.03 environment.

Private-score inputs are normalized 0-100 features. First-down rate and volume adjustments are modest audit modifiers before risk penalty:
- Rate adjustment: `clamp(((first_downs / opportunities) - position_rate_baseline) * 10, -2.0, 2.0)`, with zero rate when opportunities are zero.
- Volume adjustment: `clamp(((first_downs - position_volume_baseline) / position_volume_baseline) * 1.5, -1.5, 1.5)`.
- Rate baselines: QB 0.31, RB 0.24, WR 0.54, TE 0.50.
- Volume baselines: QB 160, RB 55, WR 50, TE 38.

Use the exact 50-pick base curve from the brief, including `1.01=1000`, `1.04=630`, `2.04=200`, `5.04=18`, and `5.10=12`.

## Confidence
Display confidence as deterministic score or High/Medium/Low bucket. Missing data must lower confidence and should never create fake precision.

## Examples
Tests must use hand-calculated fixtures for each formula. Niners sample official top five must be Achane, Lamar Jackson, Chase Brown, Luther Burden, and Brian Thomas.
