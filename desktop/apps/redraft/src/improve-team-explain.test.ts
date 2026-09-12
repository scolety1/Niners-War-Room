import { describe, expect, it } from "vitest";

import { explainStreamerPlay, explainWaiverTarget } from "./improve-team-explain";
import type { KdstStreamerRow, WaiverAddCandidate, WaiverAddDropPairing, WaiverDropCandidate } from "@nwr/contracts";

function add(overrides: Partial<WaiverAddCandidate> = {}): WaiverAddCandidate {
  return {
    sleeperPlayerId: "sleeper-1",
    canonicalPlayerId: "canon-1",
    playerName: "Marvin Harrison Jr.",
    position: "WR",
    team: "ARI",
    rosReplacementValue: 4.2,
    rosOverallRank: 38,
    weeklyProjectedPoints: 11.4,
    marginalUtility: 3.1,
    becomesStarter: true,
    marginalUtilityExplanation: "Clears your weakest starting WR by a real margin.",
    identityStatus: "MATCHED",
    faabBidLowDollars: 14,
    faabBidHighDollars: 18,
    faabUrgency: "HIGH",
    faabRationale: "Multiple teams likely bidding this week.",
    playerAvailabilityStatus: null,
    ...overrides,
  };
}

function drop(overrides: Partial<WaiverDropCandidate> = {}): WaiverDropCandidate {
  return {
    canonicalPlayerId: "canon-drop",
    playerName: "Wan'Dale Robinson",
    position: "WR",
    marginalUtility: -0.4,
    explanation: "Weakest WR on your bench.",
    playerAvailabilityStatus: null,
    ...overrides,
  };
}

function pairing(overrides: Partial<WaiverAddDropPairing> = {}): WaiverAddDropPairing {
  return { add: add(), drop: drop(), netMarginalUtility: 3.5, ...overrides };
}

describe("explainWaiverTarget", () => {
  it("builds ADD / DROP headline, bid, and ROS impact with a real pairing", () => {
    const explanation = explainWaiverTarget(add(), pairing(), "REST_OF_SEASON", null);
    expect(explanation.headline).toBe("ADD Marvin Harrison Jr. / DROP Wan'Dale Robinson");
    expect(explanation.bid).toBe("$14–18 · HIGH urgency");
    expect(explanation.why).toBe("Clears your weakest starting WR by a real margin.");
    expect(explanation.rosImpact).toBe("Replacement value +4.2 · Marginal utility +3.1 · Net vs. dropping Wan'Dale Robinson +3.5");
    expect(explanation.tone).toBe("recommended");
  });

  it("omits the DROP half of the headline and the net-vs-drop clause when no pairing exists", () => {
    const explanation = explainWaiverTarget(add(), null, "REST_OF_SEASON", null);
    expect(explanation.headline).toBe("ADD Marvin Harrison Jr.");
    expect(explanation.rosImpact).toBe("Replacement value +4.2 · Marginal utility +3.1");
  });

  it("never fabricates a THIS WEEK impact in REST_OF_SEASON mode", () => {
    const explanation = explainWaiverTarget(add(), null, "REST_OF_SEASON", null);
    expect(explanation.thisWeekImpact).toBeNull();
  });

  it("reports becomesStarter=true in THIS_WEEK mode with the real projected points", () => {
    const explanation = explainWaiverTarget(add(), null, "THIS_WEEK", null);
    expect(explanation.thisWeekImpact).toBe("Projected to become a starter this week (11.4 pts).");
  });

  it("honestly reports becomesStarter=false in THIS_WEEK mode", () => {
    const explanation = explainWaiverTarget(add({ becomesStarter: false }), null, "THIS_WEEK", null);
    expect(explanation.thisWeekImpact).toBe("Would not become a starter this week under NWR's lineup optimizer.");
  });

  it("leaves bid null when the backend supplied no real FAAB estimate", () => {
    const explanation = explainWaiverTarget(add({ faabBidLowDollars: null, faabBidHighDollars: null, faabUrgency: null }), null, "REST_OF_SEASON", null);
    expect(explanation.bid).toBeNull();
  });

  it("formats a real next-best alternative add candidate when one is supplied", () => {
    const alt = add({ canonicalPlayerId: "canon-2", playerName: "Xavier Legette", rosOverallRank: 44 });
    const explanation = explainWaiverTarget(add(), null, "REST_OF_SEASON", alt);
    expect(explanation.alternative).toBe("Xavier Legette (ROS #44)");
  });

  it("leaves alternative null rather than fabricating one when none is supplied", () => {
    const explanation = explainWaiverTarget(add(), null, "REST_OF_SEASON", null);
    expect(explanation.alternative).toBeNull();
  });

  it("falls back to a generic why when the backend explanation string is empty", () => {
    const explanation = explainWaiverTarget(add({ marginalUtilityExplanation: "" }), null, "REST_OF_SEASON", null);
    expect(explanation.why).toBe("Ranked by real marginal roster utility.");
  });
});

function streamerRow(overrides: Partial<KdstStreamerRow> = {}): KdstStreamerRow {
  return {
    playerName: "Chris Boswell",
    position: "K",
    team: "PIT",
    ecr: 4,
    tier: 1,
    week: 3,
    authority: "FantasyPros",
    rosterStatus: "AVAILABLE",
    recommendation: "START",
    ...overrides,
  };
}

describe("explainStreamerPlay", () => {
  it("reads a Tier-based why and recommended tone for a START row", () => {
    const explanation = explainStreamerPlay(streamerRow(), null);
    expect(explanation.headline).toBe("START Chris Boswell (K)");
    expect(explanation.why).toBe("NWR's FantasyPros consensus places Chris Boswell in Tier 1 at K for Week 3.");
    expect(explanation.tone).toBe("recommended");
  });

  it("falls back to an ECR-based why when no real tier is assigned", () => {
    const explanation = explainStreamerPlay(streamerRow({ tier: null, ecr: 9 }), null);
    expect(explanation.why).toBe("NWR's FantasyPros consensus ranks Chris Boswell #9 at K for Week 3.");
  });

  it("maps ALTERNATIVE onto DecisionExplain's own alternative tone, not a new one", () => {
    const explanation = explainStreamerPlay(streamerRow({ recommendation: "ALTERNATIVE" }), null);
    expect(explanation.headline).toBe("CONSIDER Chris Boswell (K)");
    expect(explanation.tone).toBe("alternative");
  });

  it("formats a real alternative row when one is supplied", () => {
    const alt = streamerRow({ playerName: "Jake Elliott", tier: 2 });
    const explanation = explainStreamerPlay(streamerRow(), alt);
    expect(explanation.alternative).toBe("Jake Elliott (Tier 2)");
  });

  it("leaves alternative null rather than fabricating one when none is supplied", () => {
    const explanation = explainStreamerPlay(streamerRow(), null);
    expect(explanation.alternative).toBeNull();
  });

  it("reads HOLD/ROSTERED_ELSEWHERE as the neutral tone", () => {
    expect(explainStreamerPlay(streamerRow({ recommendation: "HOLD" }), null).tone).toBe("neutral");
    expect(explainStreamerPlay(streamerRow({ recommendation: "ROSTERED_ELSEWHERE" }), null).tone).toBe("neutral");
  });
});
