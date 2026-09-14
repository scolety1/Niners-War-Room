import type {
  DecisionTraceHistoryEvent,
  DecisionTraceOutcomeDetail,
  DecisionTraceToolType,
  FaabOutcomeDetail,
  StartSitOutcomeDetail,
  StreamerOutcomeDetail,
  TradeFinderOutcomeDetail,
  TradeOutcomeDetail,
} from "@nwr/contracts";

/**
 * P1-4 (2026-09-12, Prospective Recommendation Ledger): pure presentation
 * derivation for the History/Review surface (decision-history.tsx). No
 * computation over real outcomes lives here -- there is no real 2026-season
 * outcome data behind anything recorded so far, so this module never
 * invents a calibration/accuracy figure. Everything here is a faithful,
 * honest label over an already-recorded `DecisionTraceHistoryEvent`.
 */

export const DECISION_TYPE_LABEL: Record<DecisionTraceToolType, string> = {
  START_SIT: "Start / Sit",
  WAIVER: "Waiver add",
  ADD_DROP: "Add / drop",
  FAAB: "FAAB bid",
  TRADE: "Trade analysis",
  K_STREAMER: "K streamer",
  DST_STREAMER: "DST streamer",
  TRADE_FINDER: "Trade finder",
  TRADE_PACKAGE_SEARCH: "Trade package search",
  DRAFT: "Draft pick",
};

/** Never fabricates a label for an unrecognized tool string -- falls back
 * to the raw value itself (still honest, just less pretty) rather than a
 * generic "Unknown" that would hide real, useful information. */
export function formatDecisionType(decisionType: string): string {
  return DECISION_TYPE_LABEL[decisionType as DecisionTraceToolType] ?? decisionType;
}

/** `generatedAt` is a real ISO-8601 UTC timestamp from the backend ledger;
 * an empty/malformed value (never expected, but never trusted blindly)
 * renders as an honest "Unknown time" rather than "Invalid Date". */
export function formatGeneratedAt(generatedAt: string): string {
  if (!generatedAt) return "Unknown time";
  const parsed = new Date(generatedAt);
  if (Number.isNaN(parsed.getTime())) return "Unknown time";
  return parsed.toLocaleString(undefined, {
    year: "numeric", month: "short", day: "numeric", hour: "numeric", minute: "2-digit",
  });
}

/** A short, honest one-line summary of the free-form `recommendation`
 * payload -- shape varies genuinely by tool (the ledger stores whatever
 * that tool's own facade call recorded), so this reads only well-known
 * keys per decision type and otherwise says so plainly rather than
 * guessing at an unfamiliar shape. */
export function summarizeRecommendation(event: DecisionTraceHistoryEvent): string {
  const rec = event.recommendation ?? {};
  const str = (value: unknown): string | null => (typeof value === "string" && value ? value : null);
  const num = (value: unknown): number | null => (typeof value === "number" && Number.isFinite(value) ? value : null);
  switch (event.decisionType) {
    case "START_SIT": {
      const total = num(rec.projectedTotal);
      return total !== null ? `Optimal lineup, projected ${total.toFixed(1)} pts` : "Optimal lineup computed";
    }
    case "WAIVER": {
      const name = str(rec.topAdd);
      return name ? `Add ${name}` : "No positive add candidate found";
    }
    case "FAAB": {
      const name = str(rec.playerName);
      const low = num(rec.bidLowDollars);
      const high = num(rec.bidHighDollars);
      if (name && low !== null && high !== null) return `Bid $${low}-$${high} on ${name}`;
      return name ? `FAAB bid on ${name}` : "FAAB bid computed";
    }
    case "TRADE": {
      const gives = Array.isArray(rec.gives) ? rec.gives.length : 0;
      const receives = Array.isArray(rec.receives) ? rec.receives.length : 0;
      const utility = num(rec.netMarginalUtility);
      return `${gives}-for-${receives} package${utility !== null ? ` (net utility ${utility >= 0 ? "+" : ""}${utility.toFixed(1)})` : ""}`;
    }
    case "TRADE_FINDER": {
      const utility = num(rec.myNetMarginalUtility);
      return utility !== null ? `Win-win trade found (my net utility +${utility.toFixed(1)})` : "Win-win trade search";
    }
    case "TRADE_PACKAGE_SEARCH": {
      const shape = str(rec.packageShape);
      return shape ? `${shape} package (${str(rec.mode) ?? "search"})` : "Trade package search";
    }
    case "K_STREAMER":
    case "DST_STREAMER": {
      const name = str(rec.playerName);
      const action = str(rec.recommendation);
      return name ? `${action ?? "Recommend"} ${name}` : "Streamer recommendation";
    }
    default: {
      const name = str(rec.playerName);
      if (name) return name;
      const keys = Object.keys(rec);
      return keys.length ? `${keys.length} recorded field(s)` : "No recommendation detail recorded";
    }
  }
}

/** Honest, plain-language cell for "Owner action if known" -- never implies
 * an action was taken when the ledger has no `ownerAction` append yet. */
export function formatOwnerAction(event: DecisionTraceHistoryEvent): string {
  if (!event.ownerAction) return "Not recorded";
  const { action, notes } = event.ownerAction;
  return notes ? `${action} (${notes})` : action;
}

/**
 * NWR Post-Closure Fixes V1 (Worker F, owner-action capture UI): the exact
 * label strings the capture buttons record. Sent verbatim as the backend's
 * free-text `action` field (see `record_owner_action`'s own docstring --
 * it is explicitly caller-defined, not a closed enum the backend
 * validates), which is also exactly what `formatOwnerAction` above renders
 * back -- so no separate display-label lookup table is needed on read.
 */
export const OWNER_ACTION_FOLLOWED_IT = "Followed it";
export const OWNER_ACTION_DID_SOMETHING_ELSE = "Did something else";
export const OWNER_ACTION_DIDNT_ACT = "Didn't act";

/**
 * Which owner-action options make sense for a given decision type.
 *
 * TASTE DECISION (flagged for the owner): the governing directive named
 * exact vocabulary for only two cases -- START_SIT ("Followed it" / "Did
 * something else", since a lineup decision is always acted on one way or
 * another -- there is no "didn't act" for a lineup, the owner necessarily
 * sets some lineup every week) and WAIVER/ADD_DROP ("Followed it" / "Did
 * something else" / "Didn't act"). Every OTHER real tool type
 * (FAAB/TRADE/TRADE_FINDER/TRADE_PACKAGE_SEARCH/K_STREAMER/DST_STREAMER,
 * plus the schema-only DRAFT) is generalized onto the same 3-option
 * WAIVER-style set here, since each of those is also a real, discrete
 * action the owner can decline to take (not submit the FAAB bid, not
 * propose the trade, not start the streamer) -- a human may want to
 * reconsider this generalization for any one of them.
 */
export function ownerActionOptionsForDecisionType(decisionType: string): string[] {
  if (decisionType === "START_SIT") {
    return [OWNER_ACTION_FOLLOWED_IT, OWNER_ACTION_DID_SOMETHING_ELSE];
  }
  return [OWNER_ACTION_FOLLOWED_IT, OWNER_ACTION_DID_SOMETHING_ELSE, OWNER_ACTION_DIDNT_ACT];
}

/** Honest, plain-language cell for "Outcome status" -- this pass records
 * no real outcome for anything yet (see the module doc on
 * in_season_decision_trace_service.py's `record_outcome`), so the default
 * copy says exactly that rather than a bare "—". */
export function formatOutcome(event: DecisionTraceHistoryEvent): string {
  if (!event.outcome) return "No outcome recorded yet";
  const { outcome, notes } = event.outcome;
  return notes ? `${outcome} (${notes})` : outcome;
}

export function statusTone(status: string): "safe" | "review" | "blocked" {
  if (status === "OUTCOME_RECORDED") return "safe";
  if (status === "OWNER_ACTION_RECORDED") return "review";
  return "review"; // RECOMMENDED (or any unrecognized status) -- pending, never "safe"/"blocked" by fabrication
}

export function statusLabel(status: string): string {
  if (status === "OUTCOME_RECORDED") return "Outcome recorded";
  if (status === "OWNER_ACTION_RECORDED") return "Owner action recorded";
  if (status === "RECOMMENDED") return "Recommended";
  return status;
}

/** Defensive re-sort (the facade already returns newest-first) -- pure and
 * unit-testable independent of the network layer. Never mutates the input
 * array. */
export function sortDecisionTraceEventsDesc(
  events: readonly DecisionTraceHistoryEvent[],
): DecisionTraceHistoryEvent[] {
  return [...events].sort((a, b) => (a.generatedAt < b.generatedAt ? 1 : a.generatedAt > b.generatedAt ? -1 : 0));
}

/**
 * NWR Live Player Intelligence V1 (Worker 6) -- History UI V2.
 *
 * Renders the real, decision-type-specific `outcome.detail` payload Worker
 * 5's `prospective_outcome_schema_v1_service.py` built (already reaches
 * this contract verbatim via `_decision_trace_history_event_payload` --
 * zero facade change needed for this pass). Deliberately NOT one generic
 * shape: each decision type gets its own section builder below, matching
 * the real, distinct schema fields the directive named (START_SIT's
 * `lineupOpportunityCost`/eligible alternatives, FAAB's two SEPARATE
 * player-decision-quality vs. bid-range-calibration axes, TRADE's
 * realized-roster-outcome shown ONLY when actually accepted).
 *
 * TASTE DECISION (flagged for the owner): raw Sleeper/canonical player ids
 * are shown as-is, never resolved to player names here. This page has no
 * existing id->name lookup of its own, and building one risks exactly the
 * canonical-vs-provider-id conflation bug class this same pass's boundary
 * tests target (`nwr-draft-room-gui-consolidation` and prior sessions hit
 * real bugs from mixing those two id spaces) -- showing the honest raw id
 * is safer than a fast, possibly-wrong name resolution. A future pass with
 * a real, audited id->name resolver available on this page could improve
 * this.
 *
 * No aggregate accuracy/calibration score is computed or shown anywhere in
 * this module -- per the governing directive, decision classes are not
 * commensurate and real outcome volume is still tiny this early in the
 * season (see `hasSufficientSampleForRollup` below, which is never called
 * by this pass because nothing here clears its own conservative bar yet).
 */

export interface OutcomeDetailRow {
  label: string;
  value: string;
}

export interface OutcomeDetailSection {
  heading: string;
  rows: OutcomeDetailRow[];
}

/** True only when this event carries a real, structured outcome detail
 * payload worth rendering an expandable section for -- never true for a
 * bare `outcome`/`notes` pair with no `detail` key (most rows, today). */
export function hasOutcomeDetail(event: DecisionTraceHistoryEvent): boolean {
  return Boolean(event.outcome?.detail);
}

function idList(ids: readonly string[] | undefined): string {
  return ids && ids.length ? ids.join(", ") : "None";
}

function numOrUnknown(value: number | null | undefined, digits = 2, suffix = ""): string {
  return value === null || value === undefined ? "Not yet computable" : `${value.toFixed(digits)}${suffix}`;
}

function boolOrUnknown(value: boolean | null | undefined): string {
  return value === null || value === undefined ? "Unknown" : value ? "Yes" : "No";
}

// Consumes the real LIST shape (`{playerId, points}[]`) -- never a dict
// keyed by player id. That dict shape is exactly the real bug class this
// pass found and fixed (a literal player id used as a JSON dict key gets
// mangled by the backend's generic camelCase key transform, e.g. a
// Sleeper DST team code "NE" -> "nE") -- see
// `_points_by_player_list` in prospective_outcome_schema_v1_service.py.
function pointsListRows(list: readonly { playerId: string; points: number | null }[] | undefined): OutcomeDetailRow[] {
  if (!list) return [];
  return list.map((entry) => ({
    label: entry.playerId,
    value: entry.points === null || entry.points === undefined ? "Unknown" : entry.points.toFixed(2),
  }));
}

function playerPointsRow(label: string, playerId: string | null, points: number | null): OutcomeDetailRow {
  if (!playerId) return { label, value: "None" };
  return { label, value: `${playerId}${points === null ? "" : ` (${points.toFixed(2)} pts)`}` };
}

function startSitSections(detail: StartSitOutcomeDetail): OutcomeDetailSection[] {
  return [
    {
      heading: "Lineup outcome",
      rows: [
        { label: "Lineup opportunity cost", value: numOrUnknown(detail.lineupOpportunityCost, 2, " pts") },
        { label: "Actual points (full lineup)", value: numOrUnknown(detail.actualPointsTotal) },
        { label: "Recommended projected total", value: numOrUnknown(detail.recommendedProjectedTotal) },
      ],
    },
    {
      heading: "Lineup differences",
      rows: [
        { label: "Recommended, but benched", value: idList(detail.recommendedOnlyIds) },
        { label: "Started, but not recommended", value: idList(detail.actualOnlyIds) },
        { label: "Eligible bench alternatives at lock", value: idList(detail.eligibleAlternativeIdsAtLock) },
      ],
    },
    {
      heading: "Actual points by player",
      rows: pointsListRows(detail.actualPointsByPlayer),
    },
  ];
}

function waiverSections(detail: import("@nwr/contracts").WaiverOutcomeDetail): OutcomeDetailSection[] {
  return [
    {
      heading: "Waiver outcome",
      rows: [
        { label: "Claim submitted", value: boolOrUnknown(detail.claimSubmitted) },
        { label: "Claim won", value: boolOrUnknown(detail.claimWon) },
        { label: "FAAB paid", value: detail.faabPaid === null ? "—" : `$${detail.faabPaid.toFixed(2)}` },
        {
          label: `Subsequent usage (${detail.horizonWeeks}wk horizon)`,
          value: detail.subsequentRosterUsageWeeks === null ? "Unknown" : `${detail.subsequentRosterUsageWeeks} wk(s)`,
        },
        { label: "Subsequent total points", value: numOrUnknown(detail.subsequentTotalPoints) },
      ],
    },
  ];
}

function addDropSections(detail: import("@nwr/contracts").AddDropOutcomeDetail): OutcomeDetailSection[] {
  return [
    {
      heading: "Add / drop outcome",
      rows: [
        { label: "Added player", value: detail.addedPlayerId ?? "None" },
        { label: "Dropped player", value: detail.droppedPlayerId ?? "None" },
        {
          label: `Added player's subsequent points (${detail.horizonWeeks}wk horizon)`,
          value: numOrUnknown(detail.addedPlayerSubsequentPoints),
        },
        {
          label: "Added player's subsequent roster usage",
          value: detail.addedPlayerSubsequentRosterUsageWeeks === null
            ? "Unknown" : `${detail.addedPlayerSubsequentRosterUsageWeeks} wk(s)`,
        },
        { label: "Dropped player's subsequent points", value: numOrUnknown(detail.droppedPlayerSubsequentPoints) },
        { label: "Dropped player later re-added", value: boolOrUnknown(detail.droppedPlayerReversed) },
      ],
    },
  ];
}

/** FAAB deliberately renders as TWO separate sections -- "was the pickup
 * good" (player decision quality) never merges with "was the suggested
 * dollar range accurate" (bid range calibration), matching the backend's
 * own structurally-separate dataclasses. */
function faabSections(detail: FaabOutcomeDetail): OutcomeDetailSection[] {
  const quality = detail.playerDecisionQuality;
  const bid = detail.bidRangeCalibration;
  return [
    {
      heading: "Player decision quality (was the pickup itself good?)",
      rows: [
        { label: "Recommended player", value: detail.recommendedPlayerId ?? "None" },
        {
          label: `Subsequent points (${quality.horizonWeeks}wk horizon)`,
          value: numOrUnknown(quality.subsequentPoints),
        },
        {
          label: "Subsequent roster usage",
          value: quality.subsequentRosterUsageWeeks === null ? "Unknown" : `${quality.subsequentRosterUsageWeeks} wk(s)`,
        },
      ],
    },
    {
      heading: "Bid range calibration (was the suggested $ range accurate?)",
      rows: [
        {
          label: "Suggested range",
          value: bid.suggestedBidLow === null || bid.suggestedBidHigh === null
            ? "Unknown" : `$${bid.suggestedBidLow}-$${bid.suggestedBidHigh}`,
        },
        { label: "Amount bid", value: bid.amountBid === null ? "Unknown" : `$${bid.amountBid}` },
        { label: "Won", value: boolOrUnknown(bid.won) },
        { label: "Actual winning bid", value: bid.actualWinningBid === null ? "Unknown" : `$${bid.actualWinningBid}` },
        { label: "Within suggested range", value: boolOrUnknown(bid.bidWithinSuggestedRange) },
        { label: "Margin vs. actual winning bid", value: numOrUnknown(bid.marginVsActualWinningBid, 2) },
      ],
    },
  ];
}

/** A rejected/unknown trade never gets a realized-roster-outcome section --
 * only the acceptance-status signal, matching the backend's structural
 * refusal to score an unobserved counterfactual. */
function tradeSections(detail: TradeOutcomeDetail): OutcomeDetailSection[] {
  const sections: OutcomeDetailSection[] = [
    {
      heading: "Trade acceptance",
      rows: [
        { label: "Acceptance status", value: detail.acceptanceStatus },
        { label: "Trade accepted", value: boolOrUnknown(detail.tradeAccepted) },
      ],
    },
  ];
  if (detail.tradeAccepted === true && detail.realizedRosterOutcome) {
    const outcome = detail.realizedRosterOutcome;
    sections.push({
      heading: "Realized roster outcome (accepted trade only)",
      rows: [
        { label: `Net subsequent points delta (${outcome.horizonWeeks}wk horizon)`, value: numOrUnknown(outcome.netSubsequentPointsDelta) },
        ...pointsListRows(outcome.givesSubsequentPointsByPlayer).map((row) => ({ label: `Gave: ${row.label}`, value: row.value })),
        ...pointsListRows(outcome.receivesSubsequentPointsByPlayer).map((row) => ({ label: `Received: ${row.label}`, value: row.value })),
      ],
    });
  }
  return sections;
}

function tradeFinderSections(detail: TradeFinderOutcomeDetail): OutcomeDetailSection[] {
  const sections: OutcomeDetailSection[] = [
    {
      heading: "Package disposition",
      rows: [{ label: "Disposition", value: detail.packageDisposition }],
    },
  ];
  if (detail.packageDisposition === "ACCEPTED" && detail.linkedTradeOutcome) {
    sections.push(...tradeSections(detail.linkedTradeOutcome));
  }
  return sections;
}

function streamerSections(detail: StreamerOutcomeDetail): OutcomeDetailSection[] {
  return [
    {
      heading: `${detail.position} streamer outcome${detail.week !== null ? ` (Week ${detail.week})` : ""}`,
      rows: [
        playerPointsRow("Recommended player", detail.recommendedPlayerId, detail.recommendedPlayerActualPoints),
        playerPointsRow("Actual starter", detail.actualStarterPlayerId, detail.actualStarterActualPoints),
        playerPointsRow("Prior roster option", detail.priorRosterOptionPlayerId, detail.priorRosterOptionActualPoints),
        playerPointsRow(
          "Best available alternative (at recommendation time)",
          detail.bestAvailableAlternativeId,
          detail.bestAvailableAlternativeActualPoints,
        ),
        { label: "Available alternatives at recommendation time", value: idList(detail.availableAlternativeIdsAtRecommendation) },
      ],
    },
  ];
}

function draftSections(detail: import("@nwr/contracts").DraftOutcomeDetail): OutcomeDetailSection[] {
  return [
    {
      heading: "Draft outcome",
      rows: [
        { label: "Evaluation method", value: detail.evaluationMethod },
        {
          label: "Season-long roster utility",
          value: detail.seasonLongRosterUtility === null ? "Not yet computed (deferred)" : detail.seasonLongRosterUtility.toFixed(2),
        },
        { label: "Notes", value: detail.notes || "—" },
      ],
    },
  ];
}

/** Honest fallback for a `detail.kind` this frontend build doesn't
 * recognize (e.g. a newer backend shipped ahead of this frontend) -- shows
 * the raw fields rather than silently hiding real data or crashing. This
 * is also the exact case Work Unit 15's enum round-trip test is meant to
 * catch BEFORE it ships, not paper over at render time. */
function rawFallbackSections(detail: Record<string, unknown>): OutcomeDetailSection[] {
  return [
    {
      heading: `Outcome detail (unrecognized kind: ${String(detail.kind ?? "unknown")})`,
      rows: Object.entries(detail)
        .filter(([key]) => key !== "kind")
        .map(([key, value]) => ({ label: key, value: typeof value === "object" ? JSON.stringify(value) : String(value) })),
    },
  ];
}

/** Builds the progressive/secondary detail sections for one event's real
 * outcome detail, dispatching on the real `kind` discriminant. Pure and
 * exhaustively unit-testable independent of any rendering. Returns `[]`
 * when there is no real detail to show (the common case this early in the
 * season) -- the caller decides whether to render an expandable affordance
 * at all based on `hasOutcomeDetail`. */
export function buildOutcomeDetailSections(event: DecisionTraceHistoryEvent): OutcomeDetailSection[] {
  const detail = event.outcome?.detail as DecisionTraceOutcomeDetail | null | undefined;
  if (!detail) return [];
  switch (detail.kind) {
    case "START_SIT_LINEUP_V1":
      return startSitSections(detail);
    case "WAIVER_V1":
      return waiverSections(detail);
    case "ADD_DROP_V1":
      return addDropSections(detail);
    case "FAAB_V1":
      return faabSections(detail);
    case "TRADE_V1":
      return tradeSections(detail);
    case "TRADE_FINDER_V1":
      return tradeFinderSections(detail);
    case "STREAMER_V1":
      return streamerSections(detail);
    case "DRAFT_V1":
      return draftSections(detail);
    default:
      return rawFallbackSections(detail as unknown as Record<string, unknown>);
  }
}

/**
 * Conservative, disclosed per-decision-class rollup gate.
 *
 * Per the governing directive: **no aggregate "NWR ACCURACY: X%" score is
 * ever shown anywhere on this page.** This function is not called by this
 * page at all today (real outcome volume is 0-1 per class this early in
 * the season, per Worker 5's own honest count) -- it exists only as a
 * named, reviewable bar a FUTURE pass could check before ever adding a
 * per-class rollup, so that decision is never made silently by a raw
 * `array.length > 0` check on live-rendered UI. 20 is a deliberately high,
 * round, disclosed-arbitrary floor (not derived from any statistical power
 * calculation) -- picked because a handful of outcomes is not remotely
 * enough to characterize a decision class honestly, and this pass would
 * rather have a future worker revisit an over-cautious number than have
 * this pass under-guard one.
 */
export const MIN_SAMPLE_SIZE_FOR_PER_CLASS_ROLLUP = 20;

export function hasSufficientSampleForRollup(outcomeCount: number): boolean {
  return outcomeCount >= MIN_SAMPLE_SIZE_FOR_PER_CLASS_ROLLUP;
}
