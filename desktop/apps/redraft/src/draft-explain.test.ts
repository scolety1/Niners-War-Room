import type { DecisionBundle, DecisionBundleCandidate } from "@nwr/contracts";
import { describe, expect, it } from "vitest";

import { explainPickNow } from "./draft-explain";
import type { PickNowBanner, SuggestionRow } from "./draft-room-v2";

function row(overrides: Partial<SuggestionRow> = {}): SuggestionRow {
  return {
    playerId: "p1",
    playerName: "Star Runner",
    position: "RB",
    team: "SEA",
    playerAvailabilityStatus: null,
    nwrRank: 5,
    marketExpectedPick: 8,
    playerScore: 88.2,
    pickScore: 94.0,
    pickScoreTiedNoSpread: false,
    teamScoreAfter: 72.8,
    teamScoreDelta: 8.6,
    championshipEquityAfter: 0.107,
    equityGain: 0.023,
    costOfWaiting: 4.1,
    makeItBackProbability: 0.12,
    makeItBackTrials: 10,
    action: "TAKE NOW",
    warnings: [],
    uncertainty: "LOW_MODEL_UNCERTAINTY (SE=0.0100)",
    alertSeverity: null,
    alertText: null,
    expectedRegret: null,
    decisionQualityPercentile: null,
    rawActionValueStatus: null,
    decisionQualityStatus: null,
    metricStatus: {},
    ...overrides,
  };
}

function candidate(overrides: Partial<DecisionBundleCandidate> = {}): DecisionBundleCandidate {
  return {
    playerId: "p1",
    playerName: "Star Runner",
    position: "RB",
    playerAvailabilityStatus: null,
    playerScore: 88.2,
    teamScoreAfter: 72.8,
    teamScoreDelta: 8.6,
    championshipEquityAfter: 0.107,
    equityGain: 0.023,
    costOfWaiting: 4.1,
    makeItBackProbability: 0.12,
    makeItBackTrials: 10,
    rawDecisionUtility: 10.9,
    teamScoreUtilityComponent: 8.6,
    equityUtilityComponent: 2.3,
    pickScore: 94.0,
    pickScoreTiedNoSpread: false,
    action: "TAKE NOW",
    warnings: [],
    uncertainty: "LOW_MODEL_UNCERTAINTY (SE=0.0100)",
    metricStatus: {},
    marginalUtility: 3.2,
    marginalRosterUtility: null,
    ...overrides,
  };
}

function bundle(candidates: DecisionBundleCandidate[]): DecisionBundle {
  return {
    available: true,
    speed: "FAST",
    version: "decision-bundle-live-v1",
    currentTeamScore: { percentile: 64.2, rosterValue: 1000, populationSize: 200, label: "TEAM SCORE — RESEARCH" },
    currentChampionshipEquity: { winProbability: 0.084, standardError: 0.01, seasonsSimulated: 200, assumedFormat: true, label: "SIMULATED CHAMPIONSHIP EQUITY — RESEARCH" },
    candidates,
    provenance: {} as never,
    simulationMetadata: {},
    latencySeconds: 0.5,
  };
}

describe("explainPickNow", () => {
  it("reads a clear NWR PICK NOW as recommended, with no fabricated alternative", () => {
    const pickNow: PickNowBanner = { row: row(), runnerUp: null, label: "NWR PICK NOW" };
    const explanation = explainPickNow(pickNow, bundle([candidate()]), false);
    expect(explanation.headline).toBe("NWR PICK NOW: Star Runner (RB)");
    expect(explanation.tone).toBe("recommended");
    expect(explanation.alternative).toBeNull();
  });

  it("uses the backend's own marginal-roster-utility explanation as WHY, verbatim, when present", () => {
    const pickNow: PickNowBanner = { row: row(), runnerUp: null, label: "NWR PICK NOW" };
    const explanation = explainPickNow(
      pickNow,
      bundle([candidate({ marginalRosterUtility: { utility: 3.2, becomesStarter: true, benchRedundancyBefore: 0, explanation: "Fills an open starting RB slot.", label: "PROMOTED" } })]),
      false,
    );
    expect(explanation.why).toBe("Fills an open starting RB slot.");
  });

  it("falls back to an honest Pick-Score-based WHY when no marginal-roster-utility explanation exists", () => {
    const pickNow: PickNowBanner = { row: row({ pickScore: 77.4 }), runnerUp: null, label: "NWR PICK NOW" };
    const explanation = explainPickNow(pickNow, bundle([candidate({ pickScore: 77.4, marginalRosterUtility: null })]), false);
    expect(explanation.why).toContain("77.4");
    expect(explanation.why).not.toMatch(/undefined|NaN/);
  });

  it("degrades honestly with a generic tie explanation, never a fabricated one, when the bundle is missing", () => {
    const pickNow: PickNowBanner = { row: row(), runnerUp: null, label: "BEST CURRENT PICK — NO SMASH VALUE" };
    const explanation = explainPickNow(pickNow, null, false);
    expect(explanation.tone).toBe("neutral");
    expect(explanation.why).toMatch(/genuine tie/);
    expect(explanation.rosterEffect).not.toMatch(/undefined|NaN/);
  });

  it("only surfaces a real ALTERNATIVE in the genuine close-call state, matching PickNowBanner.runnerUp exactly", () => {
    const runnerUp = row({ playerId: "p2", playerName: "Runner Up", pickScore: 91.5 });
    const pickNow: PickNowBanner = { row: row(), runnerUp, label: "BEST CURRENT PICK — CLOSE CALL" };
    const explanation = explainPickNow(pickNow, bundle([candidate()]), false);
    expect(explanation.tone).toBe("warning");
    expect(explanation.alternative).toContain("Runner Up (RB)");
    expect(explanation.alternative).toContain("2.5");
  });

  it("reports a real Make-It-Back / Cost-of-Waiting read for WAIT/AVAILABILITY", () => {
    const pickNow: PickNowBanner = { row: row({ makeItBackProbability: 0.999, makeItBackTrials: 200, costOfWaiting: 12.4 }), runnerUp: null, label: "NWR PICK NOW" };
    const explanation = explainPickNow(pickNow, bundle([candidate()]), false);
    expect(explanation.waitAvailability).toContain("100%*");
    expect(explanation.waitAvailability).toContain("Cost of Waiting 12.4");
  });

  it("discloses an honest UNKNOWN, never a fabricated percentage, when Make-It-Back was never evaluated", () => {
    const pickNow: PickNowBanner = { row: row({ makeItBackProbability: null, makeItBackTrials: null }), runnerUp: null, label: "NWR PICK NOW" };
    const explanation = explainPickNow(pickNow, bundle([candidate()]), false);
    expect(explanation.waitAvailability).toContain("not evaluated");
  });

  it("notes a back-to-back turn honestly instead of implying a real waiting cost", () => {
    const pickNow: PickNowBanner = { row: row(), runnerUp: null, label: "NWR PICK NOW" };
    const explanation = explainPickNow(pickNow, bundle([candidate()]), true);
    expect(explanation.waitAvailability).toMatch(/pick again immediately/);
  });

  it("reports real before/after Team Score plus a real starter/bench-depth note for ROSTER EFFECT", () => {
    const pickNow: PickNowBanner = { row: row(), runnerUp: null, label: "NWR PICK NOW" };
    const explanation = explainPickNow(
      pickNow,
      bundle([candidate({ marginalRosterUtility: { utility: 3.2, becomesStarter: true, benchRedundancyBefore: 2, explanation: "x", label: "PROMOTED" } })]),
      false,
    );
    expect(explanation.rosterEffect).toContain("64.2");
    expect(explanation.rosterEffect).toContain("72.8");
    expect(explanation.rosterEffect).toContain("+8.6");
    expect(explanation.rosterEffect).toContain("becomes an immediate starter");
  });

  it("reports an honest bench-depth note (never fabricating a starter claim) when the candidate does not become a starter", () => {
    const pickNow: PickNowBanner = { row: row(), runnerUp: null, label: "NWR PICK NOW" };
    const explanation = explainPickNow(
      pickNow,
      bundle([candidate({ marginalRosterUtility: { utility: 1.1, becomesStarter: false, benchRedundancyBefore: 3, explanation: "x", label: "PROMOTED" } })]),
      false,
    );
    expect(explanation.rosterEffect).toContain("adds bench depth (3 already at this position before the pick)");
  });

  it("maps BEST CURRENT PICK — NO SMASH VALUE to a neutral tone", () => {
    const pickNow: PickNowBanner = { row: row(), runnerUp: null, label: "BEST CURRENT PICK — NO SMASH VALUE" };
    const explanation = explainPickNow(pickNow, bundle([candidate()]), false);
    expect(explanation.tone).toBe("neutral");
  });
});
