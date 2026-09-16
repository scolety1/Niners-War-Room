import type {
  DecisionClassSummary,
  DecisionTraceHistoryEvent,
  FaabEvaluatorPayload,
  OutcomeEvaluation,
  StartSitEvaluatorPayload,
  StreamerEvaluatorPayload,
  TradeEvaluatorPayload,
  TradeFinderEvaluatorPayload,
  WaiverEvaluatorPayload,
} from "@nwr/contracts";
// Real, committed fixture produced by
// `scripts/build_history_ui_v2_live_verification_v1.py` -- the EXACT real
// `_decision_trace_history_event_payload` shape the backend sends for a
// real, live-fetched Fantasy Gamers Week 1 2026 Sleeper matchup, not a
// hand-typed approximation (see that script's own module docstring for
// full provenance). `resolveJsonModule` makes this a real, type-checked
// import, not a runtime file read.
import realFantasyGamersWeek1Event from "../../../../docs/codex/live_player_intelligence_v1/history_ui_v2_live_verification_v1/real_decision_trace_history_event.json";
import { describe, expect, it } from "vitest";

import {
  buildClassSummaryDisplay,
  buildOutcomeDetailSections,
  evaluationStatusLabel,
  evaluationStatusTone,
  formatClassSpecificHeadline,
  formatDecisionType,
  formatGeneratedAt,
  formatOutcome,
  formatOwnerAction,
  hasEvaluationDetail,
  hasOutcomeDetail,
  hasSufficientSampleForRollup,
  INITIAL_OWNER_ACTION_CELL_STATE,
  MIN_SAMPLE_SIZE_FOR_PER_CLASS_ROLLUP,
  OWNER_ACTION_DID_SOMETHING_ELSE,
  OWNER_ACTION_DIDNT_ACT,
  OWNER_ACTION_FOLLOWED_IT,
  ownerActionCellReducer,
  ownerActionOptionsForDecisionType,
  sortDecisionTraceEventsDesc,
  statusLabel,
  statusTone,
  summarizeRecommendation,
} from "./decision-history-format";

function makeEvent(overrides: Partial<DecisionTraceHistoryEvent> = {}): DecisionTraceHistoryEvent {
  return {
    traceId: "trace-1",
    league: "lg1",
    leagueSnapshotId: "snap-1",
    season: 2026,
    week: 1,
    decisionType: "WAIVER",
    recommendation: {},
    alternatives: [],
    engineVersion: "v1",
    dataVersions: {},
    statusVersions: {},
    generatedAt: "2026-09-12T18:00:00+00:00",
    status: "RECOMMENDED",
    ownerAction: null,
    ownerActionRecordedAt: null,
    outcome: null,
    outcomeRecordedAt: null,
    ...overrides,
  };
}

describe("formatDecisionType", () => {
  it("maps every known tool type to a real, human label", () => {
    expect(formatDecisionType("START_SIT")).toBe("Start / Sit");
    expect(formatDecisionType("TRADE_FINDER")).toBe("Trade finder");
    expect(formatDecisionType("TRADE_PACKAGE_SEARCH")).toBe("Trade package search");
    expect(formatDecisionType("DRAFT")).toBe("Draft pick");
  });

  it("falls back to the raw value for an unrecognized tool -- never a fabricated label", () => {
    expect(formatDecisionType("SOMETHING_NEW")).toBe("SOMETHING_NEW");
  });
});

describe("formatGeneratedAt", () => {
  it("formats a real ISO timestamp", () => {
    const label = formatGeneratedAt("2026-09-12T18:00:00+00:00");
    expect(label).not.toBe("Unknown time");
    expect(label.length).toBeGreaterThan(0);
  });

  it("never crashes on an empty or malformed timestamp -- honest fallback", () => {
    expect(formatGeneratedAt("")).toBe("Unknown time");
    expect(formatGeneratedAt("not-a-date")).toBe("Unknown time");
  });
});

describe("summarizeRecommendation", () => {
  it("summarizes a WAIVER recommendation", () => {
    const event = makeEvent({ decisionType: "WAIVER", recommendation: { topAdd: "Free Agent X" } });
    expect(summarizeRecommendation(event)).toBe("Add Free Agent X");
  });

  it("honestly reports no candidate when the recommendation is empty", () => {
    const event = makeEvent({ decisionType: "WAIVER", recommendation: {} });
    expect(summarizeRecommendation(event)).toBe("No positive add candidate found");
  });

  it("summarizes a TRADE recommendation with real counts and utility", () => {
    const event = makeEvent({
      decisionType: "TRADE",
      recommendation: { gives: ["p1"], receives: ["p2", "p3"], netMarginalUtility: 4.567 },
    });
    expect(summarizeRecommendation(event)).toBe("1-for-2 package (net utility +4.6)");
  });

  it("summarizes a FAAB recommendation with real bid range", () => {
    const event = makeEvent({
      decisionType: "FAAB",
      recommendation: { playerName: "Free Agent Y", bidLowDollars: 5, bidHighDollars: 12 },
    });
    expect(summarizeRecommendation(event)).toBe("Bid $5-$12 on Free Agent Y");
  });

  it("never crashes on an unrecognized decision type with unknown fields", () => {
    const event = makeEvent({ decisionType: "SOMETHING_NEW", recommendation: { foo: "bar" } });
    expect(summarizeRecommendation(event)).toBe("1 recorded field(s)");
  });

  it("never crashes and reports honestly when the recommendation is fully empty", () => {
    const event = makeEvent({ decisionType: "SOMETHING_NEW", recommendation: {} });
    expect(summarizeRecommendation(event)).toBe("No recommendation detail recorded");
  });
});

describe("formatOwnerAction / formatOutcome", () => {
  it("reports 'Not recorded' when no owner action has been appended yet", () => {
    expect(formatOwnerAction(makeEvent({ ownerAction: null }))).toBe("Not recorded");
  });

  it("renders a real recorded owner action with notes", () => {
    const event = makeEvent({ ownerAction: { action: "ADDED", notes: "took it" } });
    expect(formatOwnerAction(event)).toBe("ADDED (took it)");
  });

  it("reports honestly that no real outcome exists yet -- never fabricates one", () => {
    expect(formatOutcome(makeEvent({ outcome: null }))).toBe("No outcome recorded yet");
  });

  it("renders a real recorded outcome", () => {
    const event = makeEvent({ outcome: { outcome: "WON_MATCHUP", notes: "" } });
    expect(formatOutcome(event)).toBe("WON_MATCHUP");
  });
});

describe("statusTone / statusLabel", () => {
  it("never marks a pending recommendation as resolved", () => {
    expect(statusTone("RECOMMENDED")).toBe("review");
    expect(statusLabel("RECOMMENDED")).toBe("Recommended");
  });

  it("marks a real recorded outcome as the terminal, safe state", () => {
    expect(statusTone("OUTCOME_RECORDED")).toBe("safe");
    expect(statusLabel("OUTCOME_RECORDED")).toBe("Outcome recorded");
  });

  it("never crashes on an unrecognized status", () => {
    expect(statusTone("SOMETHING_NEW")).toBe("review");
    expect(statusLabel("SOMETHING_NEW")).toBe("SOMETHING_NEW");
  });
});

describe("ownerActionOptionsForDecisionType", () => {
  it("gives START_SIT only the 2 lineup-appropriate options -- no 'Didn't act'", () => {
    expect(ownerActionOptionsForDecisionType("START_SIT")).toEqual([
      OWNER_ACTION_FOLLOWED_IT,
      OWNER_ACTION_DID_SOMETHING_ELSE,
    ]);
  });

  it("gives WAIVER and ADD_DROP the 3-option set including 'Didn't act'", () => {
    expect(ownerActionOptionsForDecisionType("WAIVER")).toEqual([
      OWNER_ACTION_FOLLOWED_IT,
      OWNER_ACTION_DID_SOMETHING_ELSE,
      OWNER_ACTION_DIDNT_ACT,
    ]);
    expect(ownerActionOptionsForDecisionType("ADD_DROP")).toEqual(
      ownerActionOptionsForDecisionType("WAIVER"),
    );
  });

  it("generalizes every other real tool type onto the same 3-option set (a disclosed taste call)", () => {
    for (const decisionType of [
      "FAAB", "TRADE", "TRADE_FINDER", "TRADE_PACKAGE_SEARCH", "K_STREAMER", "DST_STREAMER", "DRAFT",
    ]) {
      expect(ownerActionOptionsForDecisionType(decisionType)).toEqual(
        ownerActionOptionsForDecisionType("WAIVER"),
      );
    }
  });

  it("never crashes for an unrecognized decision type -- falls back to the 3-option set", () => {
    expect(ownerActionOptionsForDecisionType("SOMETHING_NEW")).toEqual(
      ownerActionOptionsForDecisionType("WAIVER"),
    );
  });
});

describe("ownerActionCellReducer (NWR Full Cycle V1, Worker 6 -- real stuck-'Recording…' bug fix)", () => {
  it("starts in a clean, non-editing, non-submitting state", () => {
    expect(INITIAL_OWNER_ACTION_CELL_STATE).toEqual({ editing: false, submitting: false, error: null });
  });

  it("CHANGE_CLICKED enters editing and clears any stale submitting/error", () => {
    const dirty = { editing: false, submitting: true, error: "old error" };
    expect(ownerActionCellReducer(dirty, { type: "CHANGE_CLICKED" })).toEqual({
      editing: true,
      submitting: false,
      error: null,
    });
  });

  it("RECORD_STARTED flips submitting without touching editing", () => {
    const state = { editing: true, submitting: false, error: null };
    expect(ownerActionCellReducer(state, { type: "RECORD_STARTED" })).toEqual({
      editing: true,
      submitting: true,
      error: null,
    });
  });

  it("RECORD_SUCCEEDED resets BOTH editing and submitting together -- the exact fix", () => {
    // This is the precise state a real live-browser walkthrough found the
    // component stuck in: mid-submit (submitting=true) after a "Change"
    // click (editing=true).
    const midSubmit = { editing: true, submitting: true, error: null };
    expect(ownerActionCellReducer(midSubmit, { type: "RECORD_SUCCEEDED" })).toEqual({
      editing: false,
      submitting: false,
      error: null,
    });
  });

  it("a second real 'Change' -> record cycle never inherits a stuck submitting flag", () => {
    // Full reproduction of the live bug's exact click sequence, purely
    // through the reducer: Change -> record (success) -> Change again ->
    // record a DIFFERENT option (success). Before the fix, the second
    // record's option buttons would already show `submitting: true`
    // (permanently disabled) the moment "Change" was clicked the second
    // time, because the first record's success never cleared it.
    let state = INITIAL_OWNER_ACTION_CELL_STATE;
    state = ownerActionCellReducer(state, { type: "CHANGE_CLICKED" });
    state = ownerActionCellReducer(state, { type: "RECORD_STARTED" });
    state = ownerActionCellReducer(state, { type: "RECORD_SUCCEEDED" });
    expect(state.submitting).toBe(false);

    // Second cycle -- must start clean, not stuck.
    state = ownerActionCellReducer(state, { type: "CHANGE_CLICKED" });
    expect(state.submitting).toBe(false);
    expect(state.editing).toBe(true);
    const optionButtonsDisabled = state.submitting;
    expect(optionButtonsDisabled).toBe(false);

    state = ownerActionCellReducer(state, { type: "RECORD_STARTED" });
    state = ownerActionCellReducer(state, { type: "RECORD_SUCCEEDED" });
    expect(state).toEqual({ editing: false, submitting: false, error: null });
  });

  it("RECORD_FAILED clears submitting and surfaces the message, keeping editing open for a retry", () => {
    const state = { editing: true, submitting: true, error: null };
    expect(ownerActionCellReducer(state, { type: "RECORD_FAILED", message: "network down" })).toEqual({
      editing: true,
      submitting: false,
      error: "network down",
    });
  });

  it("CANCEL_CLICKED always returns to a clean, non-editing state", () => {
    const state = { editing: true, submitting: false, error: "stale error" };
    expect(ownerActionCellReducer(state, { type: "CANCEL_CLICKED" })).toEqual({
      editing: false,
      submitting: false,
      error: null,
    });
  });
});

describe("sortDecisionTraceEventsDesc", () => {
  it("sorts newest first without mutating the input array", () => {
    const older = makeEvent({ traceId: "older", generatedAt: "2026-09-10T00:00:00+00:00" });
    const newer = makeEvent({ traceId: "newer", generatedAt: "2026-09-12T00:00:00+00:00" });
    const input = [older, newer];
    const sorted = sortDecisionTraceEventsDesc(input);
    expect(sorted.map((event) => event.traceId)).toEqual(["newer", "older"]);
    expect(input.map((event) => event.traceId)).toEqual(["older", "newer"]); // original untouched
  });
});

/**
 * History UI V2 (Worker 6) -- `hasOutcomeDetail` / `buildOutcomeDetailSections`.
 *
 * The real Fantasy Gamers Week 1 2026 case below is loaded from a real,
 * committed JSON fixture produced by
 * `scripts/build_history_ui_v2_live_verification_v1.py` -- the EXACT real
 * `_decision_trace_history_event_payload` shape the backend sends for a
 * real, live-fetched Sleeper matchup, not a hand-typed approximation. Every
 * other decision-type case here is representative/constructed (honestly no
 * real 2026 outcome yet exists for any of them, per Worker 5's own count),
 * built directly from `prospective_outcome_schema_v1_service.py`'s real
 * `to_detail_dict()` field names and `KIND` constants.
 */
describe("hasOutcomeDetail / buildOutcomeDetailSections", () => {
  it("is false with no sections for an event with no outcome at all", () => {
    const event = makeEvent({ outcome: null });
    expect(hasOutcomeDetail(event)).toBe(false);
    expect(buildOutcomeDetailSections(event)).toEqual([]);
  });

  it("is false with no sections for a bare outcome/notes pair with no detail key (the common, pre-this-pass shape)", () => {
    const event = makeEvent({ outcome: { outcome: "WON_MATCHUP", notes: "" } });
    expect(hasOutcomeDetail(event)).toBe(false);
    expect(buildOutcomeDetailSections(event)).toEqual([]);
  });

  it("renders the REAL, live Fantasy Gamers Week 1 2026 START_SIT outcome detail", () => {
    const event = realFantasyGamersWeek1Event as unknown as DecisionTraceHistoryEvent;
    expect(event.decisionType).toBe("START_SIT");
    expect(hasOutcomeDetail(event)).toBe(true);
    const sections = buildOutcomeDetailSections(event);
    expect(sections.map((section) => section.heading)).toEqual([
      "Lineup outcome",
      "Lineup differences",
      "Actual points by player",
    ]);
    const [lineupOutcome, lineupDifferences, pointsByPlayer] = sections;
    // Real Week 1 2026 result: the owner's actual lineup matched the
    // (mechanism-demonstration) recommendation exactly -- a real, live
    // lineup opportunity cost of 0.
    expect(lineupOutcome?.rows.find((row) => row.label === "Lineup opportunity cost")?.value).toBe("0.00 pts");
    expect(lineupOutcome?.rows.find((row) => row.label === "Actual points (full lineup)")?.value).toBe("156.96");
    // Real, live eligible bench alternatives at lock -- never a "current"
    // roster read, per the ingestion module's no-future-leakage guarantee.
    expect(lineupDifferences?.rows.find((row) => row.label === "Eligible bench alternatives at lock")?.value)
      .toBe("11628, 13279, 6819, 7523, 7567, 8126");
    // Real per-player actual points, one row per real Sleeper player id.
    expect(pointsByPlayer?.rows.length).toBe(9);
    expect(pointsByPlayer?.rows.find((row) => row.label === "11560")?.value).toBe("37.26");
    // Real regression proof for the bug this pass found + fixed: the real
    // Fantasy Gamers Week 1 2026 lineup genuinely includes a Sleeper DST
    // whose real player id IS the literal team code "NE" (New England) --
    // if this were still a dict keyed by player id, the backend's generic
    // camelCase key transform would have mangled it to "nE" on the way out
    // over HTTP. The fixed LIST-of-{playerId,points} shape survives intact.
    expect(pointsByPlayer?.rows.find((row) => row.label === "NE")?.value).toBe("6.00");
    expect(pointsByPlayer?.rows.some((row) => row.label === "nE")).toBe(false);
  });

  it("shows lineup opportunity cost as 'Not yet computable' rather than 0 when genuinely unknown", () => {
    const event = makeEvent({
      decisionType: "START_SIT",
      outcome: {
        outcome: "STARTER_DEVIATED",
        notes: "",
        detail: {
          kind: "START_SIT_LINEUP_V1",
          week: 2,
          recommendedStarterIds: ["a"],
          actualStarterIds: ["b"],
          eligibleAlternativeIdsAtLock: [],
          recommendedOnlyIds: ["a"],
          actualOnlyIds: ["b"],
          recommendedProjectedTotal: null,
          actualPointsTotal: null,
          actualPointsByPlayer: [],
          lineupOpportunityCost: null,
        },
      },
    });
    const sections = buildOutcomeDetailSections(event);
    expect(sections[0]?.rows.find((row) => row.label === "Lineup opportunity cost")?.value).toBe("Not yet computable");
    expect(sections[1]?.rows.find((row) => row.label === "Eligible bench alternatives at lock")?.value).toBe("None");
  });

  it("renders FAAB's two axes as genuinely SEPARATE sections -- never merged into one figure", () => {
    const event = makeEvent({
      decisionType: "FAAB",
      outcome: {
        outcome: "PICKUP_GOOD_BID_TOO_HIGH",
        notes: "",
        detail: {
          kind: "FAAB_V1",
          recommendedPlayerId: "p1",
          playerDecisionQuality: { subsequentPoints: 24.5, subsequentRosterUsageWeeks: 3, horizonWeeks: 4 },
          bidRangeCalibration: {
            suggestedBidLow: 5, suggestedBidHigh: 12, amountBid: 30, won: true,
            actualWinningBid: 30, bidWithinSuggestedRange: false, marginVsActualWinningBid: 18,
          },
        },
      },
    });
    const sections = buildOutcomeDetailSections(event);
    expect(sections).toHaveLength(2);
    expect(sections[0]?.heading).toMatch(/pickup itself good/);
    expect(sections[1]?.heading).toMatch(/suggested \$ range accurate/);
    expect(sections[1]?.rows.find((row) => row.label === "Within suggested range")?.value).toBe("No");
    // The pickup was good (real subsequent points) EVEN THOUGH the bid was
    // out of range -- the two axes can disagree, proven structurally
    // separate here, not just conceptually.
    expect(sections[0]?.rows.find((row) => row.label.startsWith("Subsequent points"))?.value).toBe("24.50");
  });

  it("shows the realized-roster-outcome section ONLY for an actually accepted trade", () => {
    const rejected = makeEvent({
      decisionType: "TRADE",
      outcome: {
        outcome: "TRADE_REJECTED", notes: "",
        detail: { kind: "TRADE_V1", acceptanceStatus: "REJECTED", tradeAccepted: false, realizedRosterOutcome: null },
      },
    });
    const rejectedSections = buildOutcomeDetailSections(rejected);
    expect(rejectedSections).toHaveLength(1);
    expect(rejectedSections[0]?.heading).toBe("Trade acceptance");

    const accepted = makeEvent({
      decisionType: "TRADE",
      outcome: {
        outcome: "TRADE_ACCEPTED", notes: "",
        detail: {
          kind: "TRADE_V1", acceptanceStatus: "ACCEPTED", tradeAccepted: true,
          realizedRosterOutcome: {
            horizonWeeks: 4,
            givesSubsequentPointsByPlayer: [{ playerId: "g1", points: 10 }],
            receivesSubsequentPointsByPlayer: [{ playerId: "r1", points: 18 }],
            netSubsequentPointsDelta: 8,
          },
        },
      },
    });
    const acceptedSections = buildOutcomeDetailSections(accepted);
    expect(acceptedSections.map((section) => section.heading)).toEqual([
      "Trade acceptance",
      "Realized roster outcome (accepted trade only)",
    ]);
  });

  it("never crashes and falls back honestly for an unrecognized detail kind", () => {
    // `as unknown as` deliberately: this simulates a backend shipped AHEAD
    // of this frontend build, e.g. sending a `kind` this TS union doesn't
    // know about yet -- the exact case `rawFallbackSections` exists for.
    const event = makeEvent({
      outcome: {
        outcome: "SOMETHING", notes: "",
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        detail: { kind: "SOME_FUTURE_KIND_V2", foo: "bar" } as any,
      },
    });
    expect(hasOutcomeDetail(event)).toBe(true);
    const sections = buildOutcomeDetailSections(event);
    expect(sections).toHaveLength(1);
    expect(sections[0]?.heading).toContain("SOME_FUTURE_KIND_V2");
    expect(sections[0]?.rows).toEqual([{ label: "foo", value: "bar" }]);
  });
});

describe("hasSufficientSampleForRollup (the unused, conservative per-class rollup gate)", () => {
  it("is false below the disclosed floor, including at real current volumes (0-1)", () => {
    expect(hasSufficientSampleForRollup(0)).toBe(false);
    expect(hasSufficientSampleForRollup(1)).toBe(false);
    expect(hasSufficientSampleForRollup(MIN_SAMPLE_SIZE_FOR_PER_CLASS_ROLLUP - 1)).toBe(false);
  });

  it("is true only at/above the disclosed floor", () => {
    expect(hasSufficientSampleForRollup(MIN_SAMPLE_SIZE_FOR_PER_CLASS_ROLLUP)).toBe(true);
    expect(hasSufficientSampleForRollup(MIN_SAMPLE_SIZE_FOR_PER_CLASS_ROLLUP + 50)).toBe(true);
  });
});

/**
 * History UI V3 (NWR Prospective Outcomes V1, Work Units 13-14). Every
 * fixture below uses the REAL camelCase field names each Python
 * evaluator's own `to_dict()` emits (confirmed by reading
 * `prospective_outcome_*_evaluator_v1_service.py` directly this pass), not
 * an invented shape -- and the real, closed 5-member `evaluationStatus` set
 * (`prospective_outcome_evaluation_v1_service.py`'s own `EVALUATION_
 * STATUSES`).
 */

function makeEvaluation(overrides: Partial<OutcomeEvaluation> = {}): OutcomeEvaluation {
  return {
    schemaVersion: "prospective_outcome_evaluation_v1",
    traceId: "trace-1",
    decisionType: "START_SIT",
    leagueKey: "profile-1",
    leagueId: "lg1",
    leagueSnapshotId: null,
    recommendationGeneratedAt: "2026-09-08T00:00:00+00:00",
    outcomeObservedAt: null,
    outcomeWindow: { label: "SAME_WEEK_LOCK_TO_FINAL", horizonWeeks: 0 },
    outcomeSource: null,
    outcomeSourceAsOf: null,
    ownerAction: null,
    factualOutcome: null,
    evaluationStatus: "PENDING_OUTCOME",
    evaluationMetrics: {},
    issues: [],
    ...overrides,
  };
}

describe("evaluationStatusLabel / evaluationStatusTone", () => {
  it("maps every real, closed evaluationStatus string to an honest label and tone", () => {
    expect(evaluationStatusLabel("PENDING_OUTCOME")).toBe("Outcome pending");
    expect(evaluationStatusTone("PENDING_OUTCOME")).toBe("review");
    expect(evaluationStatusLabel("PENDING_WINDOW")).toBe("Window pending");
    expect(evaluationStatusTone("PENDING_WINDOW")).toBe("review");
    expect(evaluationStatusLabel("EVALUATED")).toBe("Evaluated");
    expect(evaluationStatusTone("EVALUATED")).toBe("safe");
    expect(evaluationStatusLabel("INSUFFICIENT_DECISION_CONTEXT")).toBe("Insufficient context");
    expect(evaluationStatusTone("INSUFFICIENT_DECISION_CONTEXT")).toBe("blocked");
    expect(evaluationStatusLabel("NOT_APPLICABLE")).toBe("Not applicable");
    expect(evaluationStatusTone("NOT_APPLICABLE")).toBe("review");
  });

  it("never crashes on an unrecognized status -- falls back to the raw string", () => {
    expect(evaluationStatusLabel("SOME_FUTURE_STATUS")).toBe("SOME_FUTURE_STATUS");
    expect(evaluationStatusTone("SOME_FUTURE_STATUS")).toBe("review");
  });
});

describe("hasEvaluationDetail", () => {
  it("is false when no evaluationDetail key is present at all (a pre-V3 event)", () => {
    expect(hasEvaluationDetail(makeEvent())).toBe(false);
  });

  it("is true whenever the backend attached a real evaluationDetail, even a PENDING_OUTCOME one", () => {
    const event = makeEvent({
      evaluationDetail: { traceId: "trace-1", evaluation: makeEvaluation() },
    });
    expect(hasEvaluationDetail(event)).toBe(true);
    expect(hasOutcomeDetail(event)).toBe(true);
  });
});

describe("formatClassSpecificHeadline", () => {
  it("returns null when no evaluationDetail exists at all", () => {
    expect(formatClassSpecificHeadline(makeEvent())).toBeNull();
  });

  it("renders START_SIT's real opportunity-cost figure -- '+X.X pts over chosen starter'", () => {
    const payload: StartSitEvaluatorPayload = {
      traceId: "trace-1",
      evaluation: makeEvaluation({ evaluationStatus: "EVALUATED", evaluationMetrics: { lineupOpportunityCostPoints: 4.8 } }),
      recommendedPlayerRealizedPoints: 14.8,
      ownerSelectedPlayerRealizedPoints: 10.0,
      lineupOpportunityCostPoints: 4.8,
      bestLegalAlternativePlayerId: null,
      bestLegalAlternativeActualPoints: null,
      ownerActionObserved: true,
      issues: [],
    };
    const event = makeEvent({ decisionType: "START_SIT", evaluationDetail: payload });
    expect(formatClassSpecificHeadline(event)).toBe("+4.8 pts over chosen starter");
  });

  it("renders a negative START_SIT opportunity cost honestly, never as a fake positive", () => {
    const payload: StartSitEvaluatorPayload = {
      traceId: "trace-1",
      evaluation: makeEvaluation({ evaluationStatus: "EVALUATED", evaluationMetrics: { lineupOpportunityCostPoints: -2.3 } }),
      recommendedPlayerRealizedPoints: 5.0,
      ownerSelectedPlayerRealizedPoints: 7.3,
      lineupOpportunityCostPoints: -2.3,
      bestLegalAlternativePlayerId: null,
      bestLegalAlternativeActualPoints: null,
      ownerActionObserved: true,
      issues: [],
    };
    const event = makeEvent({ decisionType: "START_SIT", evaluationDetail: payload });
    expect(formatClassSpecificHeadline(event)).toBe("-2.3 pts vs chosen starter");
  });

  it("falls back to the real evaluationStatus label when START_SIT has no real metric yet", () => {
    const payload: StartSitEvaluatorPayload = {
      traceId: "trace-1", evaluation: makeEvaluation({ evaluationStatus: "PENDING_OUTCOME" }),
      recommendedPlayerRealizedPoints: null, ownerSelectedPlayerRealizedPoints: null,
      lineupOpportunityCostPoints: null, bestLegalAlternativePlayerId: null,
      bestLegalAlternativeActualPoints: null, ownerActionObserved: false, issues: [],
    };
    const event = makeEvent({ decisionType: "START_SIT", evaluationDetail: payload });
    expect(formatClassSpecificHeadline(event)).toBe("Outcome pending");
  });

  it("renders FAAB's real 'Won at $X; suggested $Y-$Z' headline", () => {
    const payload: FaabEvaluatorPayload = {
      traceId: "trace-1", evaluation: makeEvaluation({ decisionType: "FAAB", evaluationStatus: "EVALUATED", evaluationMetrics: { x: 1 } }),
      recommendedPlayerId: "p9",
      playerDecisionQuality: { subsequentPoints: 30.0, subsequentRosterUsageWeeks: 3, horizonWeeks: 4 },
      bidRangeCalibration: {
        suggestedBidLow: 15, suggestedBidHigh: 21, amountBid: 18, won: true,
        actualWinningBid: 18, bidWithinSuggestedRange: true, marginVsActualWinningBid: 0,
      },
      issues: [],
    };
    const event = makeEvent({ decisionType: "FAAB", evaluationDetail: payload });
    expect(formatClassSpecificHeadline(event)).toBe("Won at $18; suggested $15-$21");
  });

  it("renders K/DST's real 'Recommended X actual pts; current roster K scored Y' headline", () => {
    const payload: StreamerEvaluatorPayload = {
      traceId: "trace-1", evaluation: makeEvaluation({ decisionType: "K_STREAMER", evaluationStatus: "EVALUATED", evaluationMetrics: { x: 1 } }),
      position: "K", recommendedPlayerId: "k1", recommendedPlayerActualPoints: 12.0,
      actualStarterPlayerId: "k1", actualStarterActualPoints: 12.0,
      currentOptionPlayerId: "k2", currentOptionActualPoints: 6.0,
      availableAlternativeIdsAtRecommendation: [], bestAvailableAlternativeId: null,
      bestAvailableAlternativeActualPoints: null, regretVsActualStarterPoints: 0,
      replacementLevelDeltaPoints: 6.0, issues: [],
    };
    const event = makeEvent({ decisionType: "K_STREAMER", evaluationDetail: payload });
    expect(formatClassSpecificHeadline(event)).toBe("Recommended 12.0 actual pts; current roster K scored 6.0");
  });

  it("renders TRADE's 'Accepted; evaluation window still open' when accepted but unevaluated", () => {
    const payload: TradeEvaluatorPayload = {
      traceId: "trace-1", evaluation: makeEvaluation({ decisionType: "TRADE", evaluationStatus: "PENDING_WINDOW" }),
      ownerActionRaw: "Followed it", recommendedGivesIds: ["p1"], recommendedReceivesIds: ["p2"],
      acceptanceStatus: "ACCEPTED", tradeAccepted: true, horizonWeeks: 4,
      netSubsequentPointsDeltaPoints: null, givesSubsequentPointsByPlayer: null, receivesSubsequentPointsByPlayer: null,
      issues: [],
    };
    const event = makeEvent({ decisionType: "TRADE", evaluationDetail: payload });
    expect(formatClassSpecificHeadline(event)).toBe("Accepted; evaluation window still open");
  });

  it("renders TRADE's 'Rejected — no evaluation' -- never a scored counterfactual", () => {
    const payload: TradeEvaluatorPayload = {
      traceId: "trace-1", evaluation: makeEvaluation({ decisionType: "TRADE", evaluationStatus: "NOT_APPLICABLE" }),
      ownerActionRaw: "Did something else", recommendedGivesIds: ["p1"], recommendedReceivesIds: ["p2"],
      acceptanceStatus: "REJECTED", tradeAccepted: false, horizonWeeks: null,
      netSubsequentPointsDeltaPoints: null, givesSubsequentPointsByPlayer: null, receivesSubsequentPointsByPlayer: null,
      issues: [],
    };
    const event = makeEvent({ decisionType: "TRADE", evaluationDetail: payload });
    expect(formatClassSpecificHeadline(event)).toBe("Rejected — no evaluation");
  });

  it("renders TRADE_FINDER's real accepted-package headline the same way as TRADE", () => {
    const payload: TradeFinderEvaluatorPayload = {
      traceId: "trace-1", decisionType: "TRADE_FINDER",
      evaluation: makeEvaluation({ decisionType: "TRADE_FINDER", evaluationStatus: "EVALUATED", evaluationMetrics: { x: 1 } }),
      ownerActionRaw: "SENT", recommendedGivesIds: ["p1"], recommendedReceivesIds: ["p2"],
      packageDisposition: "ACCEPTED", tradeAccepted: true, horizonWeeks: 4,
      netSubsequentPointsDeltaPoints: -3.5, givesSubsequentPointsByPlayer: null, receivesSubsequentPointsByPlayer: null,
      issues: [],
    };
    const event = makeEvent({ decisionType: "TRADE_FINDER", evaluationDetail: payload });
    expect(formatClassSpecificHeadline(event)).toBe("Accepted; net -3.5 pts over 4wk horizon");
  });

  it("renders WAIVER's real claim-submission/win headlines", () => {
    const notSubmitted: WaiverEvaluatorPayload = {
      traceId: "trace-1", evaluation: makeEvaluation({ decisionType: "WAIVER", evaluationStatus: "EVALUATED", evaluationMetrics: { x: 1 } }),
      recommendedPlayerId: "p1", recommendedDropPlayerId: null, claimableAtRecommendationTime: true,
      claimSubmitted: false, claimWon: null, faabPaid: null, horizonWeeks: 4,
      subsequentTotalPoints: null, subsequentRosterUsageWeeks: null, issues: [],
    };
    expect(formatClassSpecificHeadline(makeEvent({ decisionType: "WAIVER", evaluationDetail: notSubmitted }))).toBe(
      "Claim not submitted",
    );

    const won: WaiverEvaluatorPayload = { ...notSubmitted, claimSubmitted: true, claimWon: true, subsequentTotalPoints: 22.5 };
    expect(formatClassSpecificHeadline(makeEvent({ decisionType: "WAIVER", evaluationDetail: won }))).toBe(
      "Won; +22.5 pts over 4wk horizon",
    );
  });

  it("renders DRAFT's deferred note -- never a fabricated season-long metric", () => {
    const event = makeEvent({
      decisionType: "DRAFT",
      evaluationDetail: { traceId: "trace-1", evaluation: makeEvaluation({ decisionType: "DRAFT", evaluationStatus: "NOT_APPLICABLE" }) },
    });
    expect(formatClassSpecificHeadline(event)).toBe("Deferred to season-long roster utility (out of this cycle's scope)");
  });
});

describe("buildOutcomeDetailSections (History UI V3, evaluationDetail-sourced)", () => {
  it("prefers the real evaluationDetail payload over the legacy outcome.detail shape when both are present", () => {
    const payload: StartSitEvaluatorPayload = {
      traceId: "trace-1",
      evaluation: makeEvaluation({ evaluationStatus: "EVALUATED", evaluationMetrics: { lineupOpportunityCostPoints: 4.8 } }),
      recommendedPlayerRealizedPoints: 14.8, ownerSelectedPlayerRealizedPoints: 10.0,
      lineupOpportunityCostPoints: 4.8, bestLegalAlternativePlayerId: "bench-1", bestLegalAlternativeActualPoints: 9.0,
      ownerActionObserved: true, issues: [],
    };
    const event = makeEvent({ decisionType: "START_SIT", evaluationDetail: payload });
    const sections = buildOutcomeDetailSections(event);
    expect(sections[0]?.heading).toBe("Evaluation");
    const lineupSection = sections.find((section) => section.heading === "Lineup outcome");
    expect(lineupSection?.rows).toContainEqual({ label: "Lineup opportunity cost", value: "4.80 pts" });
    expect(lineupSection?.rows.find((row) => row.label === "Best legal bench alternative")?.value).toBe("bench-1 (9.00 pts)");
  });

  it("shows FAAB's two axes as genuinely separate sections under evaluationDetail too", () => {
    const payload: FaabEvaluatorPayload = {
      traceId: "trace-1", evaluation: makeEvaluation({ decisionType: "FAAB", evaluationStatus: "EVALUATED", evaluationMetrics: { x: 1 } }),
      recommendedPlayerId: "p9",
      playerDecisionQuality: { subsequentPoints: 30.0, subsequentRosterUsageWeeks: 3, horizonWeeks: 4 },
      bidRangeCalibration: {
        suggestedBidLow: 15, suggestedBidHigh: 21, amountBid: 18, won: true,
        actualWinningBid: 18, bidWithinSuggestedRange: true, marginVsActualWinningBid: 0,
      },
      issues: [],
    };
    const event = makeEvent({ decisionType: "FAAB", evaluationDetail: payload });
    const sections = buildOutcomeDetailSections(event);
    const headings = sections.map((section) => section.heading);
    expect(headings).toContain("Player decision quality (was the pickup itself good?)");
    expect(headings).toContain("Bid range calibration (was the suggested $ range accurate?)");
  });

  it("only shows the realized-roster-outcome section for an actually accepted trade under evaluationDetail", () => {
    const rejected: TradeEvaluatorPayload = {
      traceId: "trace-1", evaluation: makeEvaluation({ decisionType: "TRADE", evaluationStatus: "NOT_APPLICABLE" }),
      ownerActionRaw: null, recommendedGivesIds: [], recommendedReceivesIds: [],
      acceptanceStatus: "REJECTED", tradeAccepted: false, horizonWeeks: null,
      netSubsequentPointsDeltaPoints: null, givesSubsequentPointsByPlayer: null, receivesSubsequentPointsByPlayer: null,
      issues: [],
    };
    const rejectedEvent = makeEvent({ decisionType: "TRADE", evaluationDetail: rejected });
    const rejectedSections = buildOutcomeDetailSections(rejectedEvent);
    expect(rejectedSections.some((section) => section.heading.includes("Realized roster outcome"))).toBe(false);

    const accepted: TradeEvaluatorPayload = {
      ...rejected, acceptanceStatus: "ACCEPTED", tradeAccepted: true, horizonWeeks: 4, netSubsequentPointsDeltaPoints: 6.5,
    };
    const acceptedEvent = makeEvent({ decisionType: "TRADE", evaluationDetail: accepted });
    const acceptedSections = buildOutcomeDetailSections(acceptedEvent);
    expect(acceptedSections.some((section) => section.heading.includes("Realized roster outcome"))).toBe(true);
  });

  it("still renders only the base Evaluation section for DRAFT (no real evaluator this cycle)", () => {
    const event = makeEvent({
      decisionType: "DRAFT",
      evaluationDetail: { traceId: "trace-1", evaluation: makeEvaluation({ decisionType: "DRAFT", evaluationStatus: "NOT_APPLICABLE" }) },
    });
    const sections = buildOutcomeDetailSections(event);
    expect(sections).toHaveLength(1);
    expect(sections[0]?.heading).toBe("Evaluation");
  });
});

describe("buildClassSummaryDisplay (Work Unit 14, per-class only)", () => {
  it("shows NOT ENOUGH DATA YET for every real axis below the preregistered threshold", () => {
    const summary: DecisionClassSummary = {
      decisionType: "WAIVER",
      statusCounts: [],
      claimSubmissionRate: { summaryStatus: "NOT_ENOUGH_DATA_YET", sampleSize: 3 },
      claimWinRate: { summaryStatus: "NOT_ENOUGH_DATA_YET", sampleSize: 2 },
      subsequentValue: { summaryStatus: "NOT_ENOUGH_DATA_YET", sampleSize: 1 },
    };
    const display = buildClassSummaryDisplay("WAIVER", summary);
    expect(display.title).toBe("Waivers");
    for (const row of display.rows) {
      if (row.label.startsWith("Claim") || row.label.startsWith("Mean subsequent")) {
        expect(row.value).toContain("NOT ENOUGH DATA YET");
      }
    }
  });

  it("shows a real computed number ONLY once summaryStatus is SUMMARIZED, at/above the real threshold", () => {
    const summary: DecisionClassSummary = {
      decisionType: "K_STREAMER",
      statusCounts: [{ status: "EVALUATED", count: 25 }],
      regretVsActualStarter: { summaryStatus: "SUMMARIZED", sampleSize: 25, meanRegretPoints: 1.4 },
      replacementLevelDelta: { summaryStatus: "NOT_ENOUGH_DATA_YET", sampleSize: 4 },
    };
    const display = buildClassSummaryDisplay("K_STREAMER", summary);
    const regretRow = display.rows.find((row) => row.label === "Average regret vs. actual starter");
    expect(regretRow?.value).toBe("+1.40 pts");
    const replacementRow = display.rows.find((row) => row.label === "Average replacement-level delta");
    expect(replacementRow?.value).toContain("NOT ENOUGH DATA YET");
  });

  it("renders real evaluation-status counts from the real {status, count} list shape (never a raw enum-keyed dict)", () => {
    const summary: DecisionClassSummary = {
      decisionType: "START_SIT",
      statusCounts: [
        { status: "EVALUATED", count: 24 },
        { status: "PENDING_OUTCOME", count: 1 },
      ],
    };
    const display = buildClassSummaryDisplay("START_SIT", summary);
    const statusRow = display.rows.find((row) => row.label === "Real evaluation-status counts");
    expect(statusRow?.value).toBe("Evaluated: 24, Outcome pending: 1");
  });

  it("never blends two classes' summaries -- each class reads only its own real fields", () => {
    const startSit: DecisionClassSummary = {
      decisionType: "START_SIT", statusCounts: [{ status: "EVALUATED", count: 25 }], summaryStatus: "SUMMARIZED",
      evaluatedSampleSize: 25, meanLineupOpportunityCostPoints: 2.1,
    };
    const faab: DecisionClassSummary = {
      decisionType: "FAAB", statusCounts: [],
      playerDecisionQuality: { summaryStatus: "NOT_ENOUGH_DATA_YET", sampleSize: 0 },
      bidRangeCalibration: { summaryStatus: "NOT_ENOUGH_DATA_YET", sampleSize: 0 },
    };
    const startSitDisplay = buildClassSummaryDisplay("START_SIT", startSit);
    const faabDisplay = buildClassSummaryDisplay("FAAB", faab);
    expect(startSitDisplay.rows.some((row) => row.label.toLowerCase().includes("faab"))).toBe(false);
    expect(faabDisplay.rows.some((row) => row.value.includes("2.1"))).toBe(false);
  });

  it("renders DRAFT as a structurally distinct entry -- never NOT ENOUGH DATA YET", () => {
    const summary: DecisionClassSummary = {
      decisionType: "DRAFT", statusCounts: [], note: "Deferred to marginal_roster_utility_v2.",
    };
    const display = buildClassSummaryDisplay("DRAFT", summary);
    expect(display.rows[0]?.value).toBe("Deferred to marginal_roster_utility_v2.");
    expect(display.rows.some((row) => row.value.includes("NOT ENOUGH DATA YET"))).toBe(false);
  });

  it("never renders a cross-class accuracy/leaderboard field for any real class", () => {
    const summary: DecisionClassSummary = {
      decisionType: "TRADE", statusCounts: [],
      acceptanceStatusCounts: [{ status: "ACCEPTED", count: 2 }, { status: "REJECTED", count: 5 }],
    };
    const display = buildClassSummaryDisplay("TRADE", summary);
    const text = JSON.stringify(display).toLowerCase();
    expect(text).not.toContain("accuracy");
    expect(text).not.toContain("leaderboard");
  });
});
