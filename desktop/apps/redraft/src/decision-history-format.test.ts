import type { DecisionTraceHistoryEvent } from "@nwr/contracts";
import { describe, expect, it } from "vitest";

import {
  formatDecisionType,
  formatGeneratedAt,
  formatOutcome,
  formatOwnerAction,
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
