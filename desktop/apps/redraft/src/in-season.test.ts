import { describe, expect, it } from "vitest";

import { verdictFor } from "./in-season";

function tradeResult(overrides: { netMarginalUtility: number; rosValueDelta: number }) {
  return {
    leagueId: "league-1",
    gives: [],
    receives: [],
    rosValueDelta: overrides.rosValueDelta,
    netMarginalUtility: overrides.netMarginalUtility,
    startingLineupValueBefore: 0,
    startingLineupValueAfter: 0,
    startingLineupValueDelta: 0,
    benchContingencyValueBefore: 0,
    benchContingencyValueAfter: 0,
    starterHolesBefore: [],
    starterHolesAfter: [],
    positionRedundancyBefore: {},
    positionRedundancyAfter: {},
    riskFlags: [],
    championshipEquityNote: null,
    writeBehavior: "NO_SLEEPER_WRITES",
  };
}

describe("Redraft Trade Analysis verdict", () => {
  it("reads Improves my roster when both real signed signals point up", () => {
    const verdict = verdictFor(tradeResult({ netMarginalUtility: 4.2, rosValueDelta: 1.1 }));
    expect(verdict).toEqual({ label: "Improves my roster", tone: "safe" });
  });

  it("reads Hurts my roster when both real signed signals point down", () => {
    const verdict = verdictFor(tradeResult({ netMarginalUtility: -3.5, rosValueDelta: -0.4 }));
    expect(verdict).toEqual({ label: "Hurts my roster", tone: "blocked" });
  });

  it("reads Close when the two real signals disagree in direction", () => {
    expect(verdictFor(tradeResult({ netMarginalUtility: 2.0, rosValueDelta: -0.5 }))).toEqual({
      label: "Close",
      tone: "review",
    });
    expect(verdictFor(tradeResult({ netMarginalUtility: -1.0, rosValueDelta: 0.5 }))).toEqual({
      label: "Close",
      tone: "review",
    });
  });

  it("treats an exact zero delta as Close rather than a false Improves/Hurts claim", () => {
    expect(verdictFor(tradeResult({ netMarginalUtility: 0, rosValueDelta: 0 }))).toEqual({
      label: "Close",
      tone: "review",
    });
  });
});
