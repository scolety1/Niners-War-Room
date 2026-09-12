import { describe, expect, it } from "vitest";

import { explainTradeAnalysis, explainTradeFinderCandidate, tradeVerdictFor } from "./trades-explain";
import type { TradeAnalysisResult, TradeFinderCandidate, TradePlayerImpact } from "@nwr/contracts";

function playerImpact(overrides: Partial<TradePlayerImpact> = {}): TradePlayerImpact {
  return {
    playerId: "player-1",
    playerName: "Bijan Robinson",
    position: "RB",
    rosReplacementValue: 5.2,
    marginalUtility: 3.1,
    becomesStarter: true,
    statusFlag: null,
    playerAvailabilityStatus: null,
    ...overrides,
  };
}

function analysisResult(overrides: Partial<TradeAnalysisResult> = {}): TradeAnalysisResult {
  return {
    leagueId: "league-1",
    gives: [playerImpact({ playerId: "give-1", playerName: "Wan'Dale Robinson" })],
    receives: [playerImpact({ playerId: "receive-1", playerName: "Bijan Robinson" })],
    rosValueDelta: 4.5,
    netMarginalUtility: 3.1,
    startingLineupValueBefore: 102.4,
    startingLineupValueAfter: 108.9,
    startingLineupValueDelta: 6.5,
    benchContingencyValueBefore: 22.1,
    benchContingencyValueAfter: 19.8,
    starterHolesBefore: [],
    starterHolesAfter: [],
    positionRedundancyBefore: { RB: 3, WR: 4 },
    positionRedundancyAfter: { RB: 2, WR: 4 },
    riskFlags: [],
    championshipEquityNote: null,
    writeBehavior: "NO_SLEEPER_WRITES",
    ...overrides,
  };
}

describe("tradeVerdictFor", () => {
  it("reads a real net-positive trade as Improves my roster / recommended", () => {
    const verdict = tradeVerdictFor(analysisResult());
    expect(verdict.label).toBe("Improves my roster");
    expect(verdict.tone).toBe("recommended");
    expect(verdict.statusBadgeTone).toBe("safe");
  });

  it("reads a real net-negative trade as Hurts my roster / negative", () => {
    const verdict = tradeVerdictFor(analysisResult({ netMarginalUtility: -2, rosValueDelta: -1 }));
    expect(verdict.label).toBe("Hurts my roster");
    expect(verdict.tone).toBe("negative");
    expect(verdict.statusBadgeTone).toBe("blocked");
  });

  it("reads a mixed-direction trade as Close / warning", () => {
    const verdict = tradeVerdictFor(analysisResult({ netMarginalUtility: 2, rosValueDelta: -1 }));
    expect(verdict.label).toBe("Close");
    expect(verdict.tone).toBe("warning");
    expect(verdict.statusBadgeTone).toBe("review");
  });

  it("reads a genuinely tiny/zero change as Close, never fabricating a confident verdict", () => {
    const verdict = tradeVerdictFor(analysisResult({ netMarginalUtility: 0, rosValueDelta: 0 }));
    expect(verdict.label).toBe("Close");
  });
});

describe("explainTradeAnalysis", () => {
  it("builds the eyebrow from the backend's own confirmed give/receive names, not the raw picker labels", () => {
    const explanation = explainTradeAnalysis(analysisResult(), ["Wan'Dale Robinson"], ["Bijan Robinson"]);
    expect(explanation.eyebrow).toBe("You give Wan'Dale Robinson / you receive Bijan Robinson");
  });

  it("formats WEEKLY IMPACT from the real starting lineup value before/after/delta", () => {
    const explanation = explainTradeAnalysis(analysisResult(), [], []);
    expect(explanation.weeklyImpact).toBe("Starting lineup value 102.4 → 108.9 (+6.5)");
  });

  it("formats ROS IMPACT from net marginal utility and ROS value delta, appending a real championship-equity note when supplied", () => {
    const withoutNote = explainTradeAnalysis(analysisResult(), [], []);
    expect(withoutNote.rosImpact).toBe("Net marginal utility +3.1 · ROS value delta +4.5");
    const withNote = explainTradeAnalysis(analysisResult({ championshipEquityNote: "Meaningfully raises your championship odds." }), [], []);
    expect(withNote.rosImpact).toBe("Net marginal utility +3.1 · ROS value delta +4.5 · Meaningfully raises your championship odds.");
  });

  it("formats DEPTH from real bench contingency value before/after", () => {
    const explanation = explainTradeAnalysis(analysisResult(), [], []);
    expect(explanation.depth).toBe("Bench contingency value 22.1 → 19.8");
  });

  it("formats POSITION EFFECT from real starter holes and position redundancy before/after", () => {
    const explanation = explainTradeAnalysis(analysisResult({ starterHolesAfter: ["TE"] }), [], []);
    expect(explanation.positionEffect).toBe("Starter holes 0 → 1 (TE) · Redundancy RB 3→2, WR 4→4");
  });

  it("omits the redundancy clause honestly when no position redundancy data exists on either side", () => {
    const explanation = explainTradeAnalysis(analysisResult({ positionRedundancyBefore: {}, positionRedundancyAfter: {} }), [], []);
    expect(explanation.positionEffect).toBe("Starter holes 0 → 0");
  });

  it("leaves risk null rather than fabricating a 'no risk' claim when the backend records no risk flags", () => {
    const explanation = explainTradeAnalysis(analysisResult(), [], []);
    expect(explanation.risk).toBeNull();
  });

  it("joins real backend risk flags when present", () => {
    const explanation = explainTradeAnalysis(analysisResult({ riskFlags: ["Receiving player is Questionable", "Bye-week overlap at RB"] }), [], []);
    expect(explanation.risk).toBe("Receiving player is Questionable · Bye-week overlap at RB");
  });

  it("maps each verdict onto the honest, verdict-specific WHY text", () => {
    expect(explainTradeAnalysis(analysisResult(), [], []).why).toBe("Your starting lineup value and rest-of-season value both improve under NWR's evaluator.");
    expect(explainTradeAnalysis(analysisResult({ netMarginalUtility: -2, rosValueDelta: -1 }), [], []).why).toBe("Your starting lineup value and rest-of-season value both decline under NWR's evaluator.");
    expect(explainTradeAnalysis(analysisResult({ netMarginalUtility: 2, rosValueDelta: -1 }), [], []).why).toBe("Your starting lineup value and rest-of-season value move in different directions, or the net change is too small to call decisively.");
  });
});

function finderCandidate(overrides: Partial<TradeFinderCandidate> = {}): TradeFinderCandidate {
  return {
    myGivePlayerId: "give-1",
    myGivePlayerName: "Wan'Dale Robinson",
    myGivePlayerAvailabilityStatus: null,
    opponentGivePlayerId: "receive-1",
    opponentGivePlayerName: "Bijan Robinson",
    opponentGivePlayerAvailabilityStatus: null,
    opponentRosterId: "roster-2",
    opponentTeamName: "Team Two",
    myNetMarginalUtility: 2.4,
    opponentNetMarginalUtility: 1.1,
    myRosValueDelta: 3.2,
    ...overrides,
  };
}

describe("explainTradeFinderCandidate", () => {
  it("builds a real 'Send X for Y' headline from the candidate's own identity fields", () => {
    const explanation = explainTradeFinderCandidate(finderCandidate());
    expect(explanation.headline).toBe("Send Wan'Dale Robinson for Bijan Robinson");
  });

  it("reads a mutual-improvement candidate as fits=true / recommended, with a mutual why", () => {
    const explanation = explainTradeFinderCandidate(finderCandidate());
    expect(explanation.fits).toBe(true);
    expect(explanation.tone).toBe("recommended");
    expect(explanation.why).toBe("Both sides' real marginal roster utility improves under NWR's evaluator.");
  });

  it("reads a one-sided candidate as fits=false / neutral, with an honest one-sided why", () => {
    const explanation = explainTradeFinderCandidate(finderCandidate({ opponentNetMarginalUtility: -0.5 }));
    expect(explanation.fits).toBe(false);
    expect(explanation.tone).toBe("neutral");
    expect(explanation.why).toBe("Only your side's marginal utility improves under NWR's evaluator -- the other team may not agree.");
  });

  it("never fabricates an acceptance probability -- impact reports only real net marginal utility and ROS value delta", () => {
    const explanation = explainTradeFinderCandidate(finderCandidate());
    expect(explanation.impact).toBe("Your net marginal utility +2.4 · ROS value delta +3.2 · their net marginal utility +1.1");
    expect(explanation.impact.toLowerCase()).not.toContain("probability");
    expect(explanation.impact.toLowerCase()).not.toContain("accept");
  });
});
