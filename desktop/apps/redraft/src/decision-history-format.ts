import type { DecisionTraceHistoryEvent, DecisionTraceToolType } from "@nwr/contracts";

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
