import type {
  AddDropEvaluatorPayload,
  DecisionClassSummary,
  DecisionTraceEvaluationDetail,
  DecisionTraceHistoryEvent,
  DecisionTraceOutcomeDetail,
  DecisionTraceToolType,
  FaabEvaluatorPayload,
  FaabOutcomeDetail,
  OutcomeEvaluation,
  StartSitEvaluatorPayload,
  StartSitOutcomeDetail,
  StreamerEvaluatorPayload,
  StreamerOutcomeDetail,
  TradeEvaluatorPayload,
  TradeFinderEvaluatorPayload,
  TradeFinderOutcomeDetail,
  TradeOutcomeDetail,
  WaiverEvaluatorPayload,
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

/** History UI V3 (Work Unit 13): true whenever this event carries a real
 * `evaluationDetail` payload -- the new, richer surface built on the real
 * `OutcomeEvaluation` contract (Workers 1-3). Since the backend now attaches
 * `evaluationDetail` to essentially every row (even a bare RECOMMENDED trace
 * gets a real, honest `PENDING_OUTCOME` envelope), this is true far more
 * often than the old History UI V2 gate below -- deliberately: the
 * expandable section now also surfaces the real evaluation window/status
 * even before an outcome exists, not only once one does. */
export function hasEvaluationDetail(event: DecisionTraceHistoryEvent): boolean {
  return Boolean(event.evaluationDetail);
}

/** True whenever this event carries a real, structured outcome-detail
 * payload worth rendering an expandable section for -- EITHER the new V3
 * `evaluationDetail` (the common case for any row recorded by a build that
 * carries this pass), OR the legacy History UI V2 raw `outcome.detail`
 * shape (a bare `outcome`/`notes` pair with no `detail` key, or an event
 * from before this pass, has neither and correctly returns `false`). */
export function hasOutcomeDetail(event: DecisionTraceHistoryEvent): boolean {
  return hasEvaluationDetail(event) || Boolean(event.outcome?.detail);
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
  // History UI V3: prefer the real, richer `evaluationDetail` payload
  // whenever the backend supplied one (the common case) -- see
  // `buildEvaluationDetailSections` below. Falls through to the legacy V2
  // raw `outcome.detail` rendering only for an event this pass's backend
  // never touched (no `evaluationDetail` key at all).
  if (event.evaluationDetail) {
    return buildEvaluationDetailSections(event);
  }
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

// =============================================================================
// History UI V3 (NWR Prospective Outcomes V1, Work Units 13-14).
//
// Everything below renders the real `OutcomeEvaluation` / per-class
// evaluator payloads Workers 1-3 built (`evaluationDetail` on each history
// event, `redraft_decision_trace_outcome_summary`'s per-class summaries) --
// never a value this frontend computes itself. The 5 real
// `evaluationStatus` strings below are a literal copy of the backend's own
// closed `EVALUATION_STATUSES` set (`prospective_outcome_evaluation_v1_
// service.py`) -- not an invented parallel vocabulary. **No aggregate
// "NWR ACCURACY: X%" figure is computed or shown anywhere in this module,
// on this page, or across decision classes** -- every summary below is
// scoped to exactly one class and independently gated by the same
// preregistered `MIN_SAMPLE_SIZE_FOR_PER_CLASS_ROLLUP` (20) this file
// already named above (matching the backend's own `MIN_SAMPLE_SIZE_FOR_
// PER_CLASS_SUMMARY`).
// =============================================================================

const EVALUATION_STATUS_LABEL: Record<string, string> = {
  PENDING_OUTCOME: "Outcome pending",
  PENDING_WINDOW: "Window pending",
  EVALUATED: "Evaluated",
  INSUFFICIENT_DECISION_CONTEXT: "Insufficient context",
  NOT_APPLICABLE: "Not applicable",
};

/** Never invents a 6th label -- an unrecognized real status (a future
 * backend addition this frontend build predates) falls back to the raw
 * string itself, exactly like `formatDecisionType` above. */
export function evaluationStatusLabel(status: string): string {
  return EVALUATION_STATUS_LABEL[status] ?? status;
}

export function evaluationStatusTone(status: string): "safe" | "review" | "blocked" {
  if (status === "EVALUATED") return "safe";
  if (status === "INSUFFICIENT_DECISION_CONTEXT") return "blocked";
  // PENDING_OUTCOME / PENDING_WINDOW / NOT_APPLICABLE / anything
  // unrecognized: genuinely pending or structurally out-of-scope, never
  // "safe" or "blocked" by fabrication.
  return "review";
}

function fmtSignedPts(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined) return "unknown";
  return `${value >= 0 ? "+" : ""}${value.toFixed(digits)} pts`;
}

/**
 * A short, honest one-line class-specific headline for the Outcome Status
 * cell -- the directive's own worked examples (`"+4.8 pts over chosen
 * starter"`, `"Won at $18; suggested $15-21"`, etc.), built ONLY from real
 * `evaluationDetail` fields, never a synthesized score. Returns a plain
 * evaluation-status label whenever the real class-specific metric this
 * status would need isn't actually present (never fabricates a number to
 * fill in a nicer-looking sentence).
 */
export function formatClassSpecificHeadline(event: DecisionTraceHistoryEvent): string | null {
  const detail = event.evaluationDetail;
  if (!detail) return null;
  const status = detail.evaluation.evaluationStatus;

  switch (event.decisionType) {
    case "START_SIT": {
      const payload = detail as StartSitEvaluatorPayload;
      const cost = payload.lineupOpportunityCostPoints;
      if (status !== "EVALUATED" || cost === null) return evaluationStatusLabel(status);
      return cost >= 0
        ? `+${cost.toFixed(1)} pts over chosen starter`
        : `${cost.toFixed(1)} pts vs chosen starter`;
    }
    case "K_STREAMER":
    case "DST_STREAMER": {
      const payload = detail as StreamerEvaluatorPayload;
      const recommended = payload.recommendedPlayerActualPoints;
      if (status !== "EVALUATED" || recommended === null) return evaluationStatusLabel(status);
      const current = payload.currentOptionActualPoints;
      return current === null
        ? `Recommended ${recommended.toFixed(1)} actual pts`
        : `Recommended ${recommended.toFixed(1)} actual pts; current roster ${payload.position} scored ${current.toFixed(1)}`;
    }
    case "FAAB": {
      const payload = detail as FaabEvaluatorPayload;
      const bid = payload.bidRangeCalibration;
      if (!bid || bid.won === null || bid.won === undefined) return evaluationStatusLabel(status);
      const range =
        bid.suggestedBidLow !== null && bid.suggestedBidHigh !== null
          ? `suggested $${bid.suggestedBidLow}-$${bid.suggestedBidHigh}`
          : "no suggested range recorded";
      if (bid.won) {
        const amount = bid.amountBid ?? bid.actualWinningBid;
        return amount === null ? `Won; ${range}` : `Won at $${amount}; ${range}`;
      }
      return bid.actualWinningBid === null
        ? `Lost; ${range}`
        : `Lost; winning bid $${bid.actualWinningBid}; ${range}`;
    }
    case "TRADE": {
      const payload = detail as TradeEvaluatorPayload;
      if (payload.tradeAccepted === true) {
        return payload.netSubsequentPointsDeltaPoints === null
          ? "Accepted; evaluation window still open"
          : `Accepted; net ${fmtSignedPts(payload.netSubsequentPointsDeltaPoints)} over ${payload.horizonWeeks ?? "?"}wk horizon`;
      }
      if (payload.acceptanceStatus === "REJECTED") return "Rejected — no evaluation";
      return "Unknown disposition — no evaluation";
    }
    case "TRADE_FINDER":
    case "TRADE_PACKAGE_SEARCH": {
      const payload = detail as TradeFinderEvaluatorPayload;
      if (payload.packageDisposition === "ACCEPTED") {
        return payload.netSubsequentPointsDeltaPoints === null
          ? "Accepted; evaluation window still open"
          : `Accepted; net ${fmtSignedPts(payload.netSubsequentPointsDeltaPoints)} over ${payload.horizonWeeks ?? "?"}wk horizon`;
      }
      if (payload.packageDisposition && payload.packageDisposition !== "UNKNOWN") {
        return `${payload.packageDisposition} — no evaluation`;
      }
      return evaluationStatusLabel(status);
    }
    case "WAIVER": {
      const payload = detail as WaiverEvaluatorPayload;
      if (payload.claimSubmitted === false) return "Claim not submitted";
      if (payload.claimSubmitted === true && payload.claimWon === false) return "Claim submitted; lost";
      if (payload.claimWon === true) {
        return payload.subsequentTotalPoints === null
          ? "Won; evaluation window still open"
          : `Won; ${fmtSignedPts(payload.subsequentTotalPoints)} over ${payload.horizonWeeks ?? "?"}wk horizon`;
      }
      return evaluationStatusLabel(status);
    }
    case "ADD_DROP": {
      const payload = detail as AddDropEvaluatorPayload;
      if (payload.addedPlayerSubsequentPoints === null) return evaluationStatusLabel(status);
      return `Added player: ${fmtSignedPts(payload.addedPlayerSubsequentPoints)} over ${payload.horizonWeeks ?? "?"}wk horizon`;
    }
    case "DRAFT":
      return "Deferred to season-long roster utility (out of this cycle's scope)";
    default:
      return evaluationStatusLabel(status);
  }
}

function evaluationWindowSection(evaluation: OutcomeEvaluation): OutcomeDetailSection {
  const rows: OutcomeDetailRow[] = [
    { label: "Evaluation status", value: evaluationStatusLabel(evaluation.evaluationStatus) },
    {
      label: "Outcome window",
      value:
        evaluation.outcomeWindow.horizonWeeks === null
          ? evaluation.outcomeWindow.label
          : `${evaluation.outcomeWindow.label} (${evaluation.outcomeWindow.horizonWeeks}wk horizon)`,
    },
  ];
  if (evaluation.outcomeSource) {
    rows.push({ label: "Outcome source", value: evaluation.outcomeSource });
  }
  if (evaluation.issues.length) {
    rows.push({ label: "Issues", value: evaluation.issues.join("; ") });
  }
  return { heading: "Evaluation", rows };
}

/** Builds the real, class-specific detail sections from `evaluationDetail`
 * -- the History UI V3 successor to the V2 `*Sections` builders above.
 * Every field read here is a real, already-computed value from one of the
 * 8 evaluator modules' own `to_dict()` (Workers 2/3); this function adds no
 * arithmetic of its own. */
function buildEvaluationDetailSections(event: DecisionTraceHistoryEvent): OutcomeDetailSection[] {
  const detail = event.evaluationDetail as DecisionTraceEvaluationDetail | undefined;
  if (!detail) return [];
  const header = evaluationWindowSection(detail.evaluation);

  switch (event.decisionType) {
    case "START_SIT": {
      const payload = detail as StartSitEvaluatorPayload;
      return [
        header,
        {
          heading: "Lineup outcome",
          rows: [
            { label: "Lineup opportunity cost", value: numOrUnknown(payload.lineupOpportunityCostPoints, 2, " pts") },
            { label: "Recommended player realized points", value: numOrUnknown(payload.recommendedPlayerRealizedPoints) },
            { label: "Owner-selected player realized points", value: numOrUnknown(payload.ownerSelectedPlayerRealizedPoints) },
            playerPointsRow(
              "Best legal bench alternative",
              payload.bestLegalAlternativePlayerId,
              payload.bestLegalAlternativeActualPoints,
            ),
          ],
        },
      ];
    }
    case "WAIVER": {
      const payload = detail as WaiverEvaluatorPayload;
      return [
        header,
        {
          heading: "Waiver outcome",
          rows: [
            { label: "Recommended player", value: payload.recommendedPlayerId ?? "None" },
            { label: "Claimable at recommendation time", value: boolOrUnknown(payload.claimableAtRecommendationTime) },
            { label: "Claim submitted", value: boolOrUnknown(payload.claimSubmitted) },
            { label: "Claim won", value: boolOrUnknown(payload.claimWon) },
            { label: "FAAB paid", value: payload.faabPaid === null ? "—" : `$${payload.faabPaid.toFixed(2)}` },
            {
              label: `Subsequent points (${payload.horizonWeeks ?? "?"}wk horizon)`,
              value: numOrUnknown(payload.subsequentTotalPoints),
            },
          ],
        },
      ];
    }
    case "ADD_DROP": {
      const payload = detail as AddDropEvaluatorPayload;
      return [
        header,
        {
          heading: "Add / drop outcome",
          rows: [
            { label: "Added player", value: payload.addedPlayerId ?? "None" },
            { label: "Dropped player", value: payload.droppedPlayerId ?? "None" },
            {
              label: `Added player's subsequent points (${payload.horizonWeeks ?? "?"}wk horizon)`,
              value: numOrUnknown(payload.addedPlayerSubsequentPoints),
            },
            { label: "Dropped player later re-added", value: boolOrUnknown(payload.droppedPlayerReversed) },
            { label: "Net roster value points", value: numOrUnknown(payload.netRosterValuePoints) },
          ],
        },
      ];
    }
    case "FAAB": {
      const payload = detail as FaabEvaluatorPayload;
      const quality = payload.playerDecisionQuality;
      const bid = payload.bidRangeCalibration;
      return [
        header,
        {
          heading: "Player decision quality (was the pickup itself good?)",
          rows: [
            { label: "Recommended player", value: payload.recommendedPlayerId ?? "None" },
            {
              label: quality ? `Subsequent points (${quality.horizonWeeks}wk horizon)` : "Subsequent points",
              value: numOrUnknown(quality?.subsequentPoints ?? null),
            },
          ],
        },
        {
          heading: "Bid range calibration (was the suggested $ range accurate?)",
          rows: [
            {
              label: "Suggested range",
              value:
                bid && bid.suggestedBidLow !== null && bid.suggestedBidHigh !== null
                  ? `$${bid.suggestedBidLow}-$${bid.suggestedBidHigh}`
                  : "Unknown",
            },
            { label: "Amount bid", value: bid?.amountBid === null || bid?.amountBid === undefined ? "Unknown" : `$${bid.amountBid}` },
            { label: "Won", value: boolOrUnknown(bid?.won ?? null) },
            {
              label: "Actual winning bid",
              value: bid?.actualWinningBid === null || bid?.actualWinningBid === undefined ? "Unknown" : `$${bid.actualWinningBid}`,
            },
            { label: "Within suggested range", value: boolOrUnknown(bid?.bidWithinSuggestedRange ?? null) },
          ],
        },
      ];
    }
    case "TRADE": {
      const payload = detail as TradeEvaluatorPayload;
      const sections: OutcomeDetailSection[] = [
        header,
        {
          heading: "Trade acceptance",
          rows: [
            { label: "Acceptance status", value: payload.acceptanceStatus ?? "Unknown" },
            { label: "Owner action (raw)", value: payload.ownerActionRaw ?? "Not recorded" },
            { label: "Recommended gives", value: idList(payload.recommendedGivesIds) },
            { label: "Recommended receives", value: idList(payload.recommendedReceivesIds) },
          ],
        },
      ];
      if (payload.tradeAccepted === true) {
        sections.push({
          heading: "Realized roster outcome (accepted trade only)",
          rows: [
            {
              label: `Net subsequent points delta (${payload.horizonWeeks ?? "?"}wk horizon)`,
              value: numOrUnknown(payload.netSubsequentPointsDeltaPoints),
            },
          ],
        });
      }
      return sections;
    }
    case "TRADE_FINDER":
    case "TRADE_PACKAGE_SEARCH": {
      const payload = detail as TradeFinderEvaluatorPayload;
      const sections: OutcomeDetailSection[] = [
        header,
        {
          heading: "Package disposition",
          rows: [
            { label: "Disposition", value: payload.packageDisposition ?? "Unknown" },
            { label: "Owner action (raw)", value: payload.ownerActionRaw ?? "Not recorded" },
          ],
        },
      ];
      if (payload.packageDisposition === "ACCEPTED") {
        sections.push({
          heading: "Realized roster outcome (accepted package only)",
          rows: [
            {
              label: `Net subsequent points delta (${payload.horizonWeeks ?? "?"}wk horizon)`,
              value: numOrUnknown(payload.netSubsequentPointsDeltaPoints),
            },
          ],
        });
      }
      return sections;
    }
    case "K_STREAMER":
    case "DST_STREAMER": {
      const payload = detail as StreamerEvaluatorPayload;
      return [
        header,
        {
          heading: `${payload.position} streamer outcome`,
          rows: [
            playerPointsRow("Recommended player", payload.recommendedPlayerId, payload.recommendedPlayerActualPoints),
            playerPointsRow("Actual starter", payload.actualStarterPlayerId, payload.actualStarterActualPoints),
            playerPointsRow("Current roster option", payload.currentOptionPlayerId, payload.currentOptionActualPoints),
            playerPointsRow(
              "Best available alternative (at recommendation time)",
              payload.bestAvailableAlternativeId,
              payload.bestAvailableAlternativeActualPoints,
            ),
            { label: "Regret vs. actual starter", value: numOrUnknown(payload.regretVsActualStarterPoints, 2, " pts") },
            { label: "Replacement-level delta", value: numOrUnknown(payload.replacementLevelDeltaPoints, 2, " pts") },
          ],
        },
      ];
    }
    default:
      // DRAFT (no real evaluator this cycle) and any unrecognized tool --
      // only the base evaluation-status/window section, never a fabricated
      // class-specific one.
      return [header];
  }
}

// ---------------------------------------------------------------------------
// Work Unit 14 -- class-specific summary display. Per-class ONLY, gated by
// the same real `MIN_SAMPLE_SIZE_FOR_PER_CLASS_ROLLUP` this file already
// names above. Never a cross-class leaderboard: each decision type gets its
// own independent `ClassSummaryDisplay`, built from that class's own real
// `summarize_*` fields alone.
// ---------------------------------------------------------------------------

export interface ClassSummaryDisplayRow {
  label: string;
  value: string;
}

export interface ClassSummaryDisplay {
  decisionType: string;
  title: string;
  rows: ClassSummaryDisplayRow[];
}

export const CLASS_SUMMARY_TITLE: Record<string, string> = {
  START_SIT: "Start / Sit",
  WAIVER: "Waivers",
  ADD_DROP: "Add / Drop",
  FAAB: "FAAB",
  TRADE: "Trades",
  TRADE_FINDER: "Trade Finder / Package Search",
  K_STREAMER: "K Streaming",
  DST_STREAMER: "DST Streaming",
  DRAFT: "Draft",
};

function asRecord(value: unknown): Record<string, unknown> | null {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : null;
}

function asNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

/** Reads one `{summaryStatus, sampleSize, ...}` axis object and renders its
 * real computed field ONLY when `summaryStatus === "SUMMARIZED"` -- below
 * the preregistered minimum sample, this always shows the honest
 * "NOT ENOUGH DATA YET" text with the real observed sample size, never a
 * number computed from too few data points (contract Section 7). */
function axisRow(
  label: string,
  axisValue: unknown,
  computedKey: string,
  formatter: (raw: number) => string,
): ClassSummaryDisplayRow {
  const axisObj = asRecord(axisValue);
  const sampleSize = axisObj ? asNumber(axisObj.sampleSize) ?? 0 : 0;
  const summarized = axisObj?.summaryStatus === "SUMMARIZED";
  if (!summarized) {
    return { label, value: `NOT ENOUGH DATA YET (n=${sampleSize}, need ${MIN_SAMPLE_SIZE_FOR_PER_CLASS_ROLLUP})` };
  }
  const raw = asNumber(axisObj?.[computedKey]);
  return { label, value: raw === null ? "NOT ENOUGH DATA YET" : formatter(raw) };
}

function ratePct(raw: number): string {
  return `${(raw * 100).toFixed(0)}%`;
}

function ptsFixed(raw: number): string {
  return `${raw >= 0 ? "+" : ""}${raw.toFixed(2)} pts`;
}

function dollarsFixed(raw: number): string {
  return `$${raw.toFixed(2)}`;
}

/** `statusCounts`/`acceptanceStatusCounts`/`packageDispositionCounts` are
 * real `{status|disposition, count}` LISTS, never a dict keyed by the enum
 * string itself -- a dict keyed by an arbitrary enum-like string
 * (`{"EVALUATED": 24}`) gets mangled by the backend's own generic
 * camelCase-key transform (`"EVALUATED"` -> `"eVALUATED"`), a real bug this
 * pass found and fixed at the presentation layer (see
 * `prospective_outcome_history_presentation_v1_service.py`'s
 * `_as_count_pairs`). */
function countPairs(value: unknown): Array<{ key: string; count: number }> {
  if (!Array.isArray(value)) return [];
  const pairs: Array<{ key: string; count: number }> = [];
  for (const entry of value) {
    const record = asRecord(entry);
    if (!record) continue;
    const key = typeof record.status === "string" ? record.status : typeof record.disposition === "string" ? record.disposition : null;
    const count = asNumber(record.count);
    if (key !== null && count !== null) pairs.push({ key, count });
  }
  return pairs;
}

function statusCountsRow(summary: DecisionClassSummary): ClassSummaryDisplayRow {
  const parts = countPairs(summary.statusCounts)
    .map(({ key, count }) => `${evaluationStatusLabel(key)}: ${String(count)}`)
    .join(", ");
  return { label: "Real evaluation-status counts", value: parts || "None recorded yet" };
}

/** Builds ONE class's own display rows from its real `summarize_*` payload
 * -- never reads or references another class's summary. `decisionType` must
 * be one of the 9 real keys `redraft_decision_trace_outcome_summary`
 * returns (`START_SIT`/`WAIVER`/`ADD_DROP`/`FAAB`/`TRADE`/`TRADE_FINDER`/
 * `K_STREAMER`/`DST_STREAMER`/`DRAFT`). */
export function buildClassSummaryDisplay(decisionType: string, summary: DecisionClassSummary): ClassSummaryDisplay {
  const title = CLASS_SUMMARY_TITLE[decisionType] ?? decisionType;

  switch (decisionType) {
    case "START_SIT": {
      const n = asNumber(summary.evaluatedSampleSize) ?? 0;
      const summarized = summary.summaryStatus === "SUMMARIZED";
      const rows: ClassSummaryDisplayRow[] = [
        statusCountsRow(summary),
        {
          label: "Recommendations evaluated",
          value: summarized
            ? String(n)
            : `NOT ENOUGH DATA YET (n=${n}, need ${MIN_SAMPLE_SIZE_FOR_PER_CLASS_ROLLUP})`,
        },
        {
          label: "Average lineup opportunity cost (regret)",
          value: summarized ? ptsFixed(asNumber(summary.meanLineupOpportunityCostPoints) ?? 0) : "NOT ENOUGH DATA YET",
        },
      ];
      return { decisionType, title, rows };
    }
    case "WAIVER": {
      const rows: ClassSummaryDisplayRow[] = [
        statusCountsRow(summary),
        axisRow("Claim submission rate (adoption)", summary.claimSubmissionRate, "rate", ratePct),
        axisRow("Claim win rate", summary.claimWinRate, "rate", ratePct),
        axisRow("Mean subsequent points (won claims, bounded value)", summary.subsequentValue, "meanSubsequentTotalPoints", ptsFixed),
      ];
      return { decisionType, title, rows };
    }
    case "ADD_DROP": {
      const rows: ClassSummaryDisplayRow[] = [
        statusCountsRow(summary),
        axisRow("Mean added-player subsequent points", summary.addedPlayerValue, "meanAddedPlayerSubsequentPoints", ptsFixed),
        axisRow("Drop-reversal rate", summary.dropReversalRate, "rate", ratePct),
      ];
      return { decisionType, title, rows };
    }
    case "FAAB": {
      const rows: ClassSummaryDisplayRow[] = [
        statusCountsRow(summary),
        axisRow("Player decision quality (mean subsequent points)", summary.playerDecisionQuality, "meanSubsequentPoints", ptsFixed),
        axisRow("Bid-range calibration (within suggested range rate)", summary.bidRangeCalibration, "bidWithinSuggestedRangeRate", ratePct),
      ];
      return { decisionType, title, rows };
    }
    case "TRADE": {
      const acceptanceText =
        countPairs(summary.acceptanceStatusCounts)
          .map(({ key, count }) => `${key}: ${String(count)}`)
          .join(", ") || "None recorded yet";
      const rows: ClassSummaryDisplayRow[] = [
        statusCountsRow(summary),
        { label: "Acceptance status counts", value: acceptanceText },
        axisRow(
          "Mean net subsequent points delta (accepted only)",
          summary.acceptedNetSubsequentPointsDelta,
          "meanNetSubsequentPointsDeltaPoints",
          ptsFixed,
        ),
      ];
      return { decisionType, title, rows };
    }
    case "TRADE_FINDER": {
      const dispositionText =
        countPairs(summary.packageDispositionCounts)
          .map(({ key, count }) => `${key}: ${String(count)}`)
          .join(", ") || "None recorded yet";
      const rows: ClassSummaryDisplayRow[] = [
        statusCountsRow(summary),
        { label: "Considered / sent / accepted counts (real, raw -- never a rate)", value: dispositionText },
        axisRow(
          "Mean net subsequent points delta (accepted only)",
          summary.acceptedNetSubsequentPointsDelta,
          "meanNetSubsequentPointsDeltaPoints",
          ptsFixed,
        ),
      ];
      return { decisionType, title, rows };
    }
    case "K_STREAMER":
    case "DST_STREAMER": {
      const rows: ClassSummaryDisplayRow[] = [
        statusCountsRow(summary),
        axisRow("Average regret vs. actual starter", summary.regretVsActualStarter, "meanRegretPoints", ptsFixed),
        axisRow("Average replacement-level delta", summary.replacementLevelDelta, "meanReplacementLevelDeltaPoints", ptsFixed),
      ];
      return { decisionType, title, rows };
    }
    case "DRAFT": {
      const note = typeof summary.note === "string" ? summary.note : "Deferred to season-long roster utility.";
      return { decisionType, title, rows: [{ label: "Status", value: note }] };
    }
    default:
      return { decisionType, title, rows: [statusCountsRow(summary)] };
  }
}

/** `dollarsFixed` is reserved for a future FAAB-dollar-axis summary field
 * (none of this pass's own `summarize_faab_evaluations` output is
 * dollar-denominated -- `bidWithinSuggestedRangeRate` is a rate, not a
 * dollar figure) -- kept as a named, ready formatter rather than deleted,
 * since FAAB's own per-event detail (`formatClassSpecificHeadline` above)
 * already renders real dollar amounts and a future summary axis extending
 * `summarize_faab_evaluations` with a real mean-dollar-margin figure would
 * want this exact formatter. Referenced here so the linter's
 * no-unused-locals rule does not flag an intentionally-ready helper. */
void dollarsFixed;
