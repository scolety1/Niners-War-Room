import type { DecisionTraceHistoryEvent } from "@nwr/contracts";
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
  buildOutcomeDetailSections,
  formatDecisionType,
  formatGeneratedAt,
  formatOutcome,
  formatOwnerAction,
  hasOutcomeDetail,
  hasSufficientSampleForRollup,
  MIN_SAMPLE_SIZE_FOR_PER_CLASS_ROLLUP,
  OWNER_ACTION_DID_SOMETHING_ELSE,
  OWNER_ACTION_DIDNT_ACT,
  OWNER_ACTION_FOLLOWED_IT,
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
