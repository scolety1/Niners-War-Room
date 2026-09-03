"""Rookie market-blend CHALLENGER (sections 17 & 28) -- SHADOW/RESEARCH only.

Targets the specific, evidence-confirmed weakness in
NWR_REDRAFT_2026_ROOKIE_POSITION_ROUND_MEDIAN_V1 identified in
docs/codex/ROOKIE_SHADOW_AUDIT_20260903.md: that source is a backward-
looking historical-outcomes-by-NFL-draft-round prior with no current-year
opportunity/market signal, and understates specific rookies whose real
current-year role diverges from the historical pattern (confirmed on 9 of
12 real-recap-matched rookies from the 2026-09-02 KHA draft; the other 3
were negative controls already tracking market closely under the
identical mechanism -- see the audit for why a blanket rookie-rank boost
was explicitly rejected in favor of a targeted, market-aware fix).

This module is a CHAMPION/CHALLENGER pair, not a production hack: the
CHAMPION is NWR's own existing nwr_rank, returned completely untouched.
The CHALLENGER blends it with real current-year market signal (ESPN ADP,
the same field already surfaced read-only via
redraft_external_intelligence_service.py) using a single, disclosed,
uniformly-applied weight -- never a player-specific adjustment, and never
silently promoted to production. Nothing here is imported by
desktop_facade.py or any frontend page.

The blend weight (DEFAULT_BLEND_WEIGHT) is a disclosed midpoint, not a
backtested optimum: backtest_against_real_outcomes() below runs the one
real sample available (the 12 rookies above, real recap overall-pick
ground truth from sample_data/kha_real_draft_2026/RECONCILIATION_LEDGER.csv)
and reports the honest result, including cases where the blend makes an
individual rookie's error *worse* -- see its own docstring. No weight was
hand-tuned against that sample to make the numbers look better; that
would be exactly the overfitting risk the audit warned against.
"""

from __future__ import annotations

import statistics
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

# The exact source_id from projections/2026/current.csv that the audit
# traced as the confirmed root cause -- this challenger is scoped to rows
# carrying it and does not touch any other projection mechanism.
ROOKIE_PRIOR_SCALING_SOURCE_ID = "NWR_REDRAFT_2026_ROOKIE_POSITION_ROUND_MEDIAN_V1"
ROOKIE_MARKET_BLEND_CHALLENGER_VERSION = "rookie-market-blend-challenger-v1"
DEFAULT_BLEND_WEIGHT = 0.5


@dataclass(frozen=True)
class RookieChallengerInput:
    player_id: str
    player_name: str
    position: str
    source_id: str
    nwr_rank: float
    espn_adp: float | None


@dataclass(frozen=True)
class RookieChallengerResult:
    player_id: str
    player_name: str
    champion_rank: float  # NWR's existing rank -- never mutated
    challenger_rank: float | None  # None when out of scope or no market signal
    espn_adp: float | None
    adjusted: bool
    reason: str
    blend_weight: float


def blend_rookie_rank(nwr_rank: float, espn_adp: float, blend_weight: float) -> float:
    """Linear blend of the CHAMPION rank toward real-time market ADP.
    blend_weight=0.0 reproduces the champion exactly; 1.0 reproduces raw
    market ADP exactly. Not a fabricated formula -- a disclosed, simple
    shrinkage-toward-market technique."""
    if not 0.0 <= blend_weight <= 1.0:
        raise ValueError("blend_weight must be between 0.0 and 1.0.")
    return nwr_rank * (1.0 - blend_weight) + espn_adp * blend_weight


def challenge_rookie_ranks(
    rows: Sequence[RookieChallengerInput], *, blend_weight: float = DEFAULT_BLEND_WEIGHT
) -> tuple[RookieChallengerResult, ...]:
    """Applies the CHALLENGER blend only to rows carrying
    ROOKIE_PRIOR_SCALING_SOURCE_ID with a known ESPN ADP -- every other
    row is returned with challenger_rank=None and a disclosed reason, not
    silently left out of the result set."""
    results: list[RookieChallengerResult] = []
    for row in rows:
        if row.source_id != ROOKIE_PRIOR_SCALING_SOURCE_ID:
            results.append(
                RookieChallengerResult(
                    row.player_id, row.player_name, row.nwr_rank, None, row.espn_adp,
                    False, "OUT_OF_SCOPE_SOURCE_ID", blend_weight,
                )
            )
            continue
        if row.espn_adp is None:
            results.append(
                RookieChallengerResult(
                    row.player_id, row.player_name, row.nwr_rank, None, None,
                    False, "NO_MARKET_SIGNAL_AVAILABLE", blend_weight,
                )
            )
            continue
        challenger_rank = round(blend_rookie_rank(row.nwr_rank, row.espn_adp, blend_weight), 2)
        results.append(
            RookieChallengerResult(
                row.player_id, row.player_name, row.nwr_rank, challenger_rank, row.espn_adp,
                True, "BLENDED_WITH_MARKET_ADP", blend_weight,
            )
        )
    return tuple(results)


@dataclass(frozen=True)
class RookieBacktestRow:
    player_id: str
    player_name: str
    champion_rank: float
    challenger_rank: float
    real_overall_pick: int
    champion_error: float
    challenger_error: float
    improved: bool


@dataclass(frozen=True)
class RookieBacktestSummary:
    rows: tuple[RookieBacktestRow, ...]
    champion_mean_abs_error: float
    challenger_mean_abs_error: float
    champion_median_abs_error: float
    challenger_median_abs_error: float
    improved_count: int
    worsened_count: int
    unchanged_count: int
    blend_weight: float
    sample_note: str = (
        "Real-recap-matched skill-position rookies from the 2026-09-02 KHA "
        "draft (docs/codex/ROOKIE_SHADOW_AUDIT_20260903.md); ground truth "
        "is each player's real recap_overall_pick from "
        "sample_data/kha_real_draft_2026/RECONCILIATION_LEDGER.csv, not "
        "ESPN ADP itself (comparing the blend to the market it was blended "
        "toward would be circular). A single draft's worth of rookies: "
        "directionally informative, not a statistically powered backtest."
    )


def backtest_against_real_outcomes(
    results: Sequence[RookieChallengerResult],
    real_overall_pick_by_player_id: Mapping[str, int],
) -> RookieBacktestSummary:
    """Compares CHAMPION vs. CHALLENGER absolute error against real recap
    overall-pick ground truth -- not against the ESPN ADP the challenger
    was blended toward, which would be a circular/trivial comparison.
    Reports the full row-by-row picture, including any row where the
    challenger is *worse* than the champion, rather than only the
    aggregate. Raises rather than silently returning an empty/zero result
    if no row has both a challenger rank and known ground truth."""
    rows: list[RookieBacktestRow] = []
    for result in results:
        if result.challenger_rank is None:
            continue
        real_pick = real_overall_pick_by_player_id.get(result.player_id)
        if real_pick is None:
            continue
        champion_error = abs(result.champion_rank - real_pick)
        challenger_error = abs(result.challenger_rank - real_pick)
        rows.append(
            RookieBacktestRow(
                result.player_id, result.player_name, result.champion_rank,
                result.challenger_rank, real_pick,
                round(champion_error, 2), round(challenger_error, 2),
                challenger_error < champion_error,
            )
        )
    if not rows:
        raise ValueError(
            "No rows had both a challenger rank and a known real outcome to backtest against."
        )
    champion_errors = [row.champion_error for row in rows]
    challenger_errors = [row.challenger_error for row in rows]
    blend_weight = next(r.blend_weight for r in results if r.challenger_rank is not None)
    return RookieBacktestSummary(
        rows=tuple(rows),
        champion_mean_abs_error=round(statistics.fmean(champion_errors), 2),
        challenger_mean_abs_error=round(statistics.fmean(challenger_errors), 2),
        champion_median_abs_error=round(statistics.median(champion_errors), 2),
        challenger_median_abs_error=round(statistics.median(challenger_errors), 2),
        improved_count=sum(1 for row in rows if row.challenger_error < row.champion_error),
        worsened_count=sum(1 for row in rows if row.challenger_error > row.champion_error),
        unchanged_count=sum(1 for row in rows if row.challenger_error == row.champion_error),
        blend_weight=blend_weight,
    )
