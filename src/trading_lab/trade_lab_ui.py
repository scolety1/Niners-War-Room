from __future__ import annotations

from dataclasses import dataclass

TRADE_LAB_TITLE = "Trade Lab"
TRADE_LAB_SUBTITLE = (
    "Find realistic fantasy trades where market says fair, but NWR says we win."
)

TRADE_LAB_MODES = (
    "Trade For Player",
    "Trade Away Player",
    "Upgrade Position",
    "Consolidate Depth",
    "Pick Conversion",
    "Drop-Pressure Trade",
    "Opponent-Fit Trade",
    "Training Mode",
)

TRADE_LAB_DATA_CHIPS = (
    "NWR private value placeholder",
    "Public fantasy market value placeholder",
    "Roster context placeholder",
    "Drop pressure placeholder",
    "Rookie/draft context placeholder",
    "Manual review required",
)

PROHIBITED_DEMO_TERMS = (
    "stock",
    "broker",
    "api",
    "equity",
    "crypto",
    "order execution",
)

FAKE_DEMO_NAMES = (
    "Target Player",
    "Player A",
    "Player B",
    "Player C",
    "Player D",
    "2026 2nd",
    "2026 3rd",
    "Team Alpha",
    "Team Bravo",
    "Team Charlie",
)


@dataclass(frozen=True)
class NegotiationLadder:
    opening_offer: str
    fair_offer: str
    max_offer: str
    walk_away: str
    do_not_include: tuple[str, ...] = ("Core keeper",)
    counteroffer_ideas: tuple[str, ...] = ("Swap in 2026 3rd",)
    if_reject: str = "Ask which roster need matters most and remove one sweetener."
    if_ask_for_more: str = "Move up one ladder step only if NWR value stays positive."


@dataclass(frozen=True)
class RosterAftermath:
    summary: str
    keeper_impact: str
    drop_pressure_impact: str
    positional_depth_impact: str
    rookie_mock_context: str
    keeper_core_before: tuple[str, ...] = ("Player A", "Player B")
    keeper_core_after: tuple[str, ...] = ("Target Player", "Player B")
    drop_pressure_before: str = "One bench asset likely needs review."
    drop_pressure_after: str = "One cleaner roster path after the package."
    positional_depth_before: str = "Depth is crowded but uneven."
    positional_depth_after: str = "Depth is cleaner with one tradeoff to review."
    mock_draft_placeholder: str = "Mock draft context is not wired yet."
    roster_risk_notes: tuple[str, ...] = ("Manual roster review still required.",)
    needs_real_integration_note: str = "Real roster integrations are not wired yet."


@dataclass(frozen=True)
class DemoTradePackage:
    mode: str
    give: tuple[str, ...]
    get: tuple[str, ...]
    nwr_gain: float
    public_market_fairness: str
    opponent_fit: str
    roster_impact: str
    keeper_drop_impact: str
    risk_flags: tuple[str, ...]
    verdict: str
    negotiation_ladder: NegotiationLadder
    warnings: tuple[str, ...]
    roster_aftermath: RosterAftermath


@dataclass(frozen=True)
class ModeContext:
    mode: str
    user_question: str
    explanation: str
    relevant_controls: tuple[str, ...]
    warning_examples: tuple[str, ...]


MODE_CONTEXTS = {
    "Trade For Player": ModeContext(
        mode="Trade For Player",
        user_question="I want to trade for this player. What should I give up?",
        explanation="Start with the target and compare realistic outgoing packages.",
        relevant_controls=("Target player", "Opponent team", "Max offer aggressiveness"),
        warning_examples=("Do not include core keepers too early.",),
    ),
    "Trade Away Player": ModeContext(
        mode="Trade Away Player",
        user_question="I want to trade away this player. What should I target in return?",
        explanation="Start with the outgoing player and compare return packages.",
        relevant_controls=("Outgoing player", "Opponent team", "Risk preference"),
        warning_examples=("Avoid accepting a package with no rookie pick upside.",),
    ),
    "Upgrade Position": ModeContext(
        mode="Upgrade Position",
        user_question="Which package upgrades a lineup spot without overpaying?",
        explanation="Consolidate assets into a stronger starter while protecting depth.",
        relevant_controls=("Target player", "Allow multi-player packages", "Risk preference"),
        warning_examples=("Do not thin scarce position depth below review threshold.",),
    ),
    "Consolidate Depth": ModeContext(
        mode="Consolidate Depth",
        user_question="How can we turn bench depth into a cleaner roster asset?",
        explanation="Package extra players or picks to reduce future roster pressure.",
        relevant_controls=("Allow multi-player packages", "Untouchable assets"),
        warning_examples=("Do not consolidate into a player who creates keeper crowding.",),
    ),
    "Pick Conversion": ModeContext(
        mode="Pick Conversion",
        user_question="Which player return is worth converting rookie pick value?",
        explanation="Compare pick cost against roster usefulness and future draft flexibility.",
        relevant_controls=("Include picks", "Win-now vs long-term preference"),
        warning_examples=("Do not spend the 2026 2nd unless roster impact is clear.",),
    ),
    "Drop-Pressure Trade": ModeContext(
        mode="Drop-Pressure Trade",
        user_question="Which trade reduces future cuts without losing too much value?",
        explanation="Move fringe depth into picks or cleaner roster assets.",
        relevant_controls=("Outgoing player", "Drop pressure placeholder"),
        warning_examples=("Do not solve drop pressure by giving away keeper upside.",),
    ),
    "Opponent-Fit Trade": ModeContext(
        mode="Opponent-Fit Trade",
        user_question="Which team is the best trade partner?",
        explanation="Compare fake opponent needs against package realism.",
        relevant_controls=("Opponent team", "Target player", "Outgoing player"),
        warning_examples=("Do not chase NWR gain if the opponent has no reason to accept.",),
    ),
    "Training Mode": ModeContext(
        mode="Training Mode",
        user_question="Can I practice judging a trade package?",
        explanation="Review fake scenarios and score negotiation quality.",
        relevant_controls=("Mode", "Risk preference"),
        warning_examples=("Training scenarios are fake and do not use real roster data.",),
    ),
}


def demo_trade_packages() -> tuple[DemoTradePackage, ...]:
    return generate_fake_trade_packages()


def generate_fake_trade_packages(mode: str | None = None) -> tuple[DemoTradePackage, ...]:
    packages = (
        DemoTradePackage(
            mode="Trade For Player",
            give=("Player A", "2026 3rd"),
            get=("Target Player",),
            nwr_gain=18.4,
            public_market_fairness="Fair enough for Team Alpha to consider.",
            opponent_fit="Team Alpha needs depth and can spare Target Player.",
            roster_impact="Upgrades starting lineup while trimming bench crowding.",
            keeper_drop_impact="Improves keeper ceiling and lowers drop pressure.",
            risk_flags=("Target role uncertainty", "Pick cost acceptable"),
            verdict="Best opening package for manual review",
            negotiation_ladder=NegotiationLadder(
                opening_offer="Player A",
                fair_offer="Player A plus 2026 3rd",
                max_offer="Player A plus 2026 2nd",
                walk_away="Player A plus Player B",
            ),
            warnings=("Do not include Player B unless Team Alpha adds value.",),
            roster_aftermath=RosterAftermath(
                summary="Starting lineup gains a higher-upside player.",
                keeper_impact="Keeper pool improves by one high-ceiling option.",
                drop_pressure_impact="Bench consolidation eases one future cut.",
                positional_depth_impact="Depth remains acceptable after the trade.",
                rookie_mock_context="2026 3rd is below current priority pick tier.",
            ),
        ),
        DemoTradePackage(
            mode="Trade Away Player",
            give=("Player B",),
            get=("Player C", "2026 2nd"),
            nwr_gain=11.2,
            public_market_fairness="Slightly favorable but realistic for Team Bravo.",
            opponent_fit="Team Bravo needs Player B's position and has extra picks.",
            roster_impact="Adds flexibility and a rookie pick without hurting starters.",
            keeper_drop_impact="Keeper impact neutral; drop pressure improves.",
            risk_flags=("Player C role volatility",),
            verdict="Strong counteroffer package",
            negotiation_ladder=NegotiationLadder(
                opening_offer="Player C plus 2026 3rd",
                fair_offer="Player C plus 2026 2nd",
                max_offer="Player C plus 2026 2nd and bench sweetener",
                walk_away="Player C only",
            ),
            warnings=("Avoid accepting Player C without a pick.",),
            roster_aftermath=RosterAftermath(
                summary="Roster becomes more flexible across bye weeks.",
                keeper_impact="No new keeper crowding.",
                drop_pressure_impact="Creates one cleaner drop path.",
                positional_depth_impact="Slight short-term depth loss at Player B's spot.",
                rookie_mock_context="2026 2nd supports next rookie draft plan.",
            ),
        ),
        DemoTradePackage(
            mode="Upgrade Position",
            give=("Player C", "2026 2nd"),
            get=("Target Player",),
            nwr_gain=15.8,
            public_market_fairness="Aggressive but still plausible for Team Charlie.",
            opponent_fit="Team Charlie wants picks and has extra starter depth.",
            roster_impact="Turns two flexible assets into one lineup upgrade.",
            keeper_drop_impact="Adds keeper upside but raises short-term depth risk.",
            risk_flags=("Consolidation risk", "Higher pick cost"),
            verdict="Good upside package if depth is expendable",
            negotiation_ladder=NegotiationLadder(
                opening_offer="Player C plus 2026 3rd",
                fair_offer="Player C plus 2026 2nd",
                max_offer="Player C plus Player D",
                walk_away="Player B plus 2026 2nd",
            ),
            warnings=("Do not overpay if Target Player's role is uncertain.",),
            roster_aftermath=RosterAftermath(
                summary="Starting lineup improves, but bench flexibility tightens.",
                keeper_impact="Keeper core gains ceiling.",
                drop_pressure_impact="Drop pressure improves only if Player D stays.",
                positional_depth_impact="Depth gets thinner at Player C's position.",
                rookie_mock_context="2026 2nd is a meaningful draft-plan cost.",
            ),
        ),
        DemoTradePackage(
            mode="Pick Conversion",
            give=("2026 2nd", "2026 3rd"),
            get=("Player D",),
            nwr_gain=7.6,
            public_market_fairness="Fair for Team Bravo if they prefer rookie picks.",
            opponent_fit="Team Bravo is pick-focused and can move Player D.",
            roster_impact="Adds usable depth without moving a current starter.",
            keeper_drop_impact="Keeper impact modest; drop pressure may increase.",
            risk_flags=("Roster spot crowding",),
            verdict="Useful pick-to-player conversion",
            negotiation_ladder=NegotiationLadder(
                opening_offer="2026 3rd",
                fair_offer="2026 2nd",
                max_offer="2026 2nd plus 2026 3rd",
                walk_away="Player A",
            ),
            warnings=("Check drop pressure before adding Player D.",),
            roster_aftermath=RosterAftermath(
                summary="Depth improves, but one future roster decision gets tighter.",
                keeper_impact="No immediate keeper upgrade.",
                drop_pressure_impact="Adds one future drop-pressure decision.",
                positional_depth_impact="Improves depth at a thin position.",
                rookie_mock_context="Consumes mid-round rookie flexibility.",
            ),
        ),
        DemoTradePackage(
            mode="Drop-Pressure Trade",
            give=("Player D", "2026 3rd"),
            get=("2026 2nd",),
            nwr_gain=5.1,
            public_market_fairness="Realistic if Team Alpha needs depth.",
            opponent_fit="Team Alpha can use Player D and values extra bench options.",
            roster_impact="Converts a likely roster squeeze into a cleaner pick.",
            keeper_drop_impact="Lowers drop pressure and preserves keeper flexibility.",
            risk_flags=("Future pick uncertainty",),
            verdict="Clean pressure-release package",
            negotiation_ladder=NegotiationLadder(
                opening_offer="Player D",
                fair_offer="Player D plus 2026 3rd",
                max_offer="Player D plus Player C",
                walk_away="Any core keeper",
            ),
            warnings=("Do not include a core keeper just to clear bench pressure.",),
            roster_aftermath=RosterAftermath(
                summary="Roster gets easier to manage before cuts.",
                keeper_impact="Keeper core unchanged.",
                drop_pressure_impact="Drop pressure improves by moving a fringe asset.",
                positional_depth_impact="Depth loss is acceptable.",
                rookie_mock_context="Adds a better rookie pick lane.",
            ),
        ),
        DemoTradePackage(
            mode="Consolidate Depth",
            give=("Player A", "Player D"),
            get=("Player B",),
            nwr_gain=9.4,
            public_market_fairness="Balanced enough for Team Charlie to review.",
            opponent_fit="Team Charlie needs two usable depth pieces.",
            roster_impact="Consolidates two bench assets into one better flex option.",
            keeper_drop_impact="Keeper impact neutral; drop pressure improves.",
            risk_flags=("Depth consolidation",),
            verdict="Useful if roster spots matter more than depth volume",
            negotiation_ladder=NegotiationLadder(
                opening_offer="Player D",
                fair_offer="Player A plus Player D",
                max_offer="Player A plus 2026 3rd",
                walk_away="Player A plus 2026 2nd",
            ),
            warnings=("Avoid if bye-week depth is already thin.",),
            roster_aftermath=RosterAftermath(
                summary="Bench gets cleaner with one fewer roster decision.",
                keeper_impact="No keeper core change.",
                drop_pressure_impact="Drop pressure improves by one slot.",
                positional_depth_impact="Depth volume decreases but quality rises.",
                rookie_mock_context="No rookie pick cost in the fair offer.",
            ),
        ),
        DemoTradePackage(
            mode="Opponent-Fit Trade",
            give=("Player C",),
            get=("Player A", "2026 3rd"),
            nwr_gain=6.8,
            public_market_fairness="Close enough for Team Alpha if they need Player C.",
            opponent_fit="Team Alpha has a need that Player C can cover.",
            roster_impact="Adds a safer depth player and a small pick return.",
            keeper_drop_impact="Keeper impact neutral; drop pressure modestly improves.",
            risk_flags=("Lower ceiling",),
            verdict="Good partner-fit package",
            negotiation_ladder=NegotiationLadder(
                opening_offer="Player A",
                fair_offer="Player A plus 2026 3rd",
                max_offer="Player A plus 2026 2nd",
                walk_away="Player A only",
            ),
            warnings=("Avoid if Team Alpha no longer needs Player C's position.",),
            roster_aftermath=RosterAftermath(
                summary="Roster gets safer but loses some ceiling.",
                keeper_impact="No keeper core change.",
                drop_pressure_impact="Slightly easier drop decision later.",
                positional_depth_impact="Improves weekly floor at a bench spot.",
                rookie_mock_context="2026 3rd adds a small draft option.",
            ),
        ),
    )
    if mode is None:
        return packages
    return tuple(package for package in packages if package.mode == mode)


def sort_packages_by_review_score(
    packages: tuple[DemoTradePackage, ...],
) -> tuple[DemoTradePackage, ...]:
    return tuple(
        sorted(
            packages,
            key=lambda package: (
                package.nwr_gain,
                "realistic" in package.public_market_fairness.lower(),
                "improves" in package.roster_impact.lower(),
            ),
            reverse=True,
        )
    )


def mode_context_for(mode: str) -> ModeContext:
    return MODE_CONTEXTS[mode]


def packages_for_mode(mode: str) -> tuple[DemoTradePackage, ...]:
    packages = generate_fake_trade_packages(mode)
    if packages:
        return packages
    return generate_fake_trade_packages()


def best_trade_package(packages: tuple[DemoTradePackage, ...] | None = None) -> DemoTradePackage:
    candidates = packages or demo_trade_packages()
    return max(candidates, key=lambda package: package.nwr_gain)


def format_package_summary(package: DemoTradePackage) -> str:
    give = " + ".join(package.give)
    get = " + ".join(package.get)
    return f"Give {give} for {get}: +{package.nwr_gain:.1f} NWR value"


def bad_trade_warnings(package: DemoTradePackage) -> tuple[str, ...]:
    warnings = list(package.warnings)
    if package.nwr_gain < 0:
        warnings.append("NWR value delta is negative.")
    if "unrealistic" in package.public_market_fairness.lower():
        warnings.append("Public fantasy market value says this may not be realistic.")
    return tuple(warnings)


def format_negotiation_ladder(ladder: NegotiationLadder) -> tuple[str, ...]:
    return (
        f"Opening offer: {ladder.opening_offer}",
        f"Fair offer: {ladder.fair_offer}",
        f"Max offer: {ladder.max_offer}",
        f"Walk-away line: {ladder.walk_away}",
        f"Do-not-include assets: {', '.join(ladder.do_not_include)}",
        f"Counteroffer ideas: {', '.join(ladder.counteroffer_ideas)}",
        f"If they reject: {ladder.if_reject}",
        f"If they ask for more: {ladder.if_ask_for_more}",
    )


def demo_payload_text() -> str:
    packages = demo_trade_packages()
    return " ".join(
        [
            TRADE_LAB_TITLE,
            TRADE_LAB_SUBTITLE,
            " ".join(TRADE_LAB_MODES),
            " ".join(TRADE_LAB_DATA_CHIPS),
            " ".join(format_package_summary(package) for package in packages),
            " ".join(package.opponent_fit for package in packages),
            " ".join(package.roster_impact for package in packages),
            " ".join(package.verdict for package in packages),
        ]
    )
