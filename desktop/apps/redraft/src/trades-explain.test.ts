import { NwrApiError } from "@nwr/api-client";
import { describe, expect, it } from "vitest";

import {
  describeTradePackageSearchError,
  explainTradeAnalysis,
  explainTradeFinderCandidate,
  explainTradePackageCandidate,
  tradeVerdictFor,
} from "./trades-explain";
import type { TradeAnalysisResult, TradeFinderCandidate, TradePackageCandidate, TradePackageEvaluation, TradePlayerImpact } from "@nwr/contracts";

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

// ---------------------------------------------------------------------------
// TRADE PACKAGE SEARCH (P1-3, Worker 7)
// ---------------------------------------------------------------------------

function packageEvaluation(overrides: Partial<TradePackageEvaluation> = {}): TradePackageEvaluation {
  return {
    gives: [playerImpact({ playerId: "my-rb1", playerName: "My RB1", position: "RB" })],
    receives: [playerImpact({ playerId: "opp-wr1", playerName: "Opp WR1", position: "WR" })],
    rosValueDelta: 10.0,
    netMarginalUtility: 60.0,
    startingLineupValueBefore: 980.0,
    startingLineupValueAfter: 1020.0,
    startingLineupValueDelta: 40.0,
    benchContingencyValueBefore: 130.0,
    benchContingencyValueAfter: 80.0,
    starterHolesBefore: ["WR 1/2", "TE 0/1"],
    starterHolesAfter: ["TE 0/1"],
    positionRedundancyBefore: { RB: 2, WR: 0 },
    positionRedundancyAfter: { RB: 1, WR: 1 },
    riskFlags: [],
    ...overrides,
  };
}

function packageCandidate(overrides: Partial<TradePackageCandidate> = {}): TradePackageCandidate {
  return {
    opponentRosterId: "2",
    opponentTeamName: "Rival Team",
    packageShape: "1-for-1",
    youSend: ["my-rb1"],
    youSendNames: ["My RB1"],
    youReceive: ["opp-wr1"],
    youReceiveNames: ["Opp WR1"],
    ownerEvaluation: packageEvaluation(),
    opponentEvaluation: packageEvaluation({ netMarginalUtility: 28.14, rosValueDelta: 10.0 }),
    whyItHelpsYou: ["Net marginal roster utility +60.0.", "Fills real starter hole(s): WR 1/2."],
    whyItMayFitThem: ["Net marginal roster utility +28.1."],
    ...overrides,
  };
}

describe("explainTradePackageCandidate", () => {
  it("builds a real 'Send X for Y' headline from the candidate's own confirmed identity fields, supporting multi-player packages", () => {
    const explanation = explainTradePackageCandidate(
      packageCandidate({ youSendNames: ["My RB1", "My RB4"], youReceiveNames: ["Opp WR1"] }),
    );
    expect(explanation.headline).toBe("Send My RB1, My RB4 for Opp WR1");
  });

  it("labels WHY IT HELPS YOU / WHY IT MAY FIT THEM explicitly and joins the backend's own real sentences verbatim", () => {
    const explanation = explainTradePackageCandidate(packageCandidate());
    expect(explanation.why).toBe("Why it helps you: Net marginal roster utility +60.0. Fills real starter hole(s): WR 1/2.");
    expect(explanation.secondaryWhy).toBe("Why it may fit them: Net marginal roster utility +28.1.");
  });

  it("falls back to an honest 'no specific reason recorded' rather than fabricating one when the backend sends no sentences", () => {
    const explanation = explainTradePackageCandidate(packageCandidate({ whyItHelpsYou: [], whyItMayFitThem: [] }));
    expect(explanation.why).toBe("Why it helps you: NWR's evaluator found this package legal but recorded no specific reason.");
    expect(explanation.secondaryWhy).toBe("Why it may fit them: NWR did not record a specific reason this may fit the other team.");
  });

  it("never fabricates an acceptance probability anywhere in the rendered explanation", () => {
    const explanation = explainTradePackageCandidate(packageCandidate());
    const rendered = [explanation.why, explanation.secondaryWhy, explanation.thisWeekImpact, explanation.rosImpact].join(" ").toLowerCase();
    expect(rendered).not.toContain("probability");
    expect(rendered).not.toContain("accept");
  });

  it("formats WEEKLY IMPACT from the owner side's real starting lineup value before/after/delta", () => {
    const explanation = explainTradePackageCandidate(packageCandidate());
    expect(explanation.thisWeekImpact).toBe("Starting lineup value 980.0 → 1020.0 (+40.0)");
  });

  it("formats ROS IMPACT from the owner side's net marginal utility and ROS value delta -- never appending a championship-equity note (the nested evaluation carries no such field)", () => {
    const explanation = explainTradePackageCandidate(packageCandidate());
    expect(explanation.rosImpact).toBe("Net marginal utility +60.0 · ROS value delta +10.0");
  });

  it("formats DEPTH and POSITION EFFECT from the owner side's real before/after values", () => {
    const explanation = explainTradePackageCandidate(packageCandidate());
    expect(explanation.depth).toBe("Bench contingency value 130.0 → 80.0");
    expect(explanation.positionEffect).toBe("Starter holes 2 → 1 (TE 0/1) · Redundancy RB 2→1, WR 0→1");
  });

  it("leaves risk null rather than fabricating a 'no risk' claim when the backend records no risk flags", () => {
    expect(explainTradePackageCandidate(packageCandidate()).risk).toBeNull();
  });

  it("joins real backend risk flags when present", () => {
    const explanation = explainTradePackageCandidate(
      packageCandidate({ ownerEvaluation: packageEvaluation({ riskFlags: ["Receiving player is Questionable"] }) }),
    );
    expect(explanation.risk).toBe("Receiving player is Questionable");
  });

  it("reads a real net-positive owner side as recommended, a net-negative side as negative, and a mixed-direction side as warning -- never fabricating a confident tone from a mixed signal", () => {
    expect(explainTradePackageCandidate(packageCandidate()).tone).toBe("recommended");
    expect(
      explainTradePackageCandidate(
        packageCandidate({ ownerEvaluation: packageEvaluation({ netMarginalUtility: -5, rosValueDelta: -2 }) }),
      ).tone,
    ).toBe("negative");
    expect(
      explainTradePackageCandidate(
        packageCandidate({ ownerEvaluation: packageEvaluation({ netMarginalUtility: 5, rosValueDelta: -2 }) }),
      ).tone,
    ).toBe("warning");
  });
});

describe("describeTradePackageSearchError", () => {
  it("softens the disclosed TRADE_PACKAGE_SEARCH_TARGET_IDENTITY_UNRESOLVED code into honest, owner-friendly copy -- never showing the raw error code", () => {
    const error = new NwrApiError(
      "The requested target player could not be identity-matched to the governed ranking pool.",
      { code: "TRADE_PACKAGE_SEARCH_TARGET_IDENTITY_UNRESOLVED", status: 409, recoveryAction: "Retry after checking Data Health." },
    );
    const softened = describeTradePackageSearchError(error);
    expect(softened.message).toBe("Couldn't find that player on a tradeable roster.");
    expect(softened.message.toLowerCase()).not.toContain("identity");
    expect(softened.message).not.toContain("TRADE_PACKAGE_SEARCH");
  });

  it("passes through the facade's own already-human-readable message/recovery for every other real error code, honestly, rather than inventing a second layer of copy", () => {
    const error = new NwrApiError(
      "Sleeper roster/user/player data could not be read. No local or remote state was changed.",
      { code: "TRADE_PACKAGE_SEARCH_READ_FAILED", status: 503, recoveryAction: "Retry after checking Data Health." },
    );
    const softened = describeTradePackageSearchError(error);
    expect(softened.message).toBe(error.message);
    expect(softened.recovery).toBe(error.recoveryAction);
  });
});
