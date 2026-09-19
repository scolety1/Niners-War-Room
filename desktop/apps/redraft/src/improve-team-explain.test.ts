import { describe, expect, it } from "vitest";

import { explainStreamerPlay, explainWaiverTarget, resolveFaabDisplay } from "./improve-team-explain";
import type { KdstStreamerRow, WaiverAddCandidate, WaiverAddDropPairing, WaiverDropCandidate, WaiverFaabContext } from "@nwr/contracts";

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
    // NWR Sunday Readiness overnight cycle, Worker 3 (W5 fix): a real,
    // already-evaluated weekly-lineup impact by default -- individual
    // tests override to exercise the "not evaluated" honest-disclosure
    // path.
    becomesStarterBasis: "THIS_WEEK_LINEUP_EVALUATION",
    thisWeekLineupGain: 6.8,
    thisWeekEvaluated: true,
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
  return {
    add: add(),
    drop: drop(),
    dropRequired: true,
    addUtilityVsOriginalRoster: 3.1,
    addUtilityVsPostDropRoster: 3.1,
    dropUtilityVsPostDropRoster: -0.4,
    netMarginalUtility: 3.5,
    contextLabel: "SAME_CONTEXT_MARGINAL_COMPARISON",
    ...overrides,
  };
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

  it("Waiver Night V1 Section 4: omits DROP the same way for a real open-roster-slot pairing (pairing exists, drop is null)", () => {
    const openSlotPairing = pairing({
      drop: null,
      dropRequired: false,
      addUtilityVsPostDropRoster: null,
      dropUtilityVsPostDropRoster: null,
      netMarginalUtility: 3.1,
      contextLabel: "OPEN_ROSTER_SLOT_ADD_ONLY",
    });
    const explanation = explainWaiverTarget(add(), openSlotPairing, "REST_OF_SEASON", null);
    expect(explanation.headline).toBe("ADD Marvin Harrison Jr.");
    expect(explanation.rosImpact).toBe("Replacement value +4.2 · Marginal utility +3.1");
  });

  it("never fabricates a THIS WEEK impact in REST_OF_SEASON mode", () => {
    const explanation = explainWaiverTarget(add(), null, "REST_OF_SEASON", null);
    expect(explanation.thisWeekImpact).toBeNull();
  });

  it("reports becomesStarter=true in THIS_WEEK mode with the real legal-lineup gain", () => {
    const explanation = explainWaiverTarget(add(), null, "THIS_WEEK", null);
    expect(explanation.thisWeekImpact).toBe("Projected to become a starter this week (real legal-lineup gain: 6.8 pts).");
  });

  it("honestly reports becomesStarter=false in THIS_WEEK mode", () => {
    const explanation = explainWaiverTarget(
      add({ becomesStarter: false, thisWeekLineupGain: 0.2 }), null, "THIS_WEEK", null,
    );
    expect(explanation.thisWeekImpact).toBe(
      "Would not become a starter this week under NWR's lineup optimizer (real legal-lineup gain: 0.2 pts).",
    );
  });

  // NWR Sunday Readiness overnight cycle, Worker 3 (W5 fix): a real,
  // previously-reproduced bug -- `becomesStarter: null` (not evaluated
  // this pass) used to be silently treated the same as `false` ("would
  // not become a starter"), a fabricated negative claim. Must read as
  // honestly unavailable instead.
  it("never treats an unevaluated candidate (becomesStarter null) as a false negative", () => {
    const explanation = explainWaiverTarget(
      add({
        becomesStarter: null,
        becomesStarterBasis: "UNAVAILABLE_NOT_EVALUATED_THIS_PASS",
        thisWeekLineupGain: null,
      }),
      null, "THIS_WEEK", null,
    );
    expect(explanation.thisWeekImpact).toBe(
      "A real weekly-lineup evaluation was not computed for this candidate this pass -- not the same as "
      + "\"would not start\". Weekly projected points: 11.4.",
    );
    expect(explanation.thisWeekImpact).not.toContain("Would not become a starter");
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
    // NWR Sunday Readiness overnight cycle, Worker 3 (W6 fix): "START" now
    // renders as "KEEP" so a real keep-current-starter recommendation reads
    // as one, not as an instruction to take some new action.
    expect(explanation.headline).toBe("KEEP Chris Boswell (K)");
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

  // Real display bug found + fixed (waiver night V4, Work Unit 7 live
  // verification): `rosterStatus` is the backend's raw enum
  // ("YOUR_STARTER", "ROSTERED_ELSEWHERE") and was rendered unhumanized in
  // both the STREAMERS table and this card's own "this week" line.
  // Presentation-only fix -- confirmed live against the real Fantasy
  // Gamers league (Ka'imi Fairbairn K and New England DST both resolve
  // "YOUR STARTER" now, not "YOUR_STARTER").
  it("humanizes the raw backend rosterStatus enum in thisWeekImpact (underscore -> space)", () => {
    const explanation = explainStreamerPlay(streamerRow({ rosterStatus: "YOUR_STARTER" }), null);
    expect(explanation.thisWeekImpact).toBe("YOUR STARTER · Week 3");
  });

  it("humanizes ROSTERED_ELSEWHERE the same way", () => {
    const explanation = explainStreamerPlay(streamerRow({ rosterStatus: "ROSTERED_ELSEWHERE", recommendation: "ROSTERED_ELSEWHERE" }), null);
    expect(explanation.thisWeekImpact).toBe("ROSTERED ELSEWHERE · Week 3");
  });
});

function faabContext(overrides: Partial<WaiverFaabContext> = {}): WaiverFaabContext {
  return {
    isFaabLeague: true,
    budgetMode: "LIVE",
    totalBudgetDollars: 100,
    remainingBudgetDollars: 100,
    weeksRemaining: 14,
    weeksRemainingSource: "LIVE",
    waiverPosition: 10,
    source: "SLEEPER_LIVE",
    scenario: null,
    ...overrides,
  };
}

/**
 * LIVE/SCENARIO race fix (2026-09-16, real bug reproduced live and via
 * code inspection): the FAAB tab's "LIVE"/"SCENARIO" label used to be
 * computed from `budgetScenario`, current React input state owned by
 * `ImproveTeamPage`, while the numbers/recommendations next to it always
 * came from `waivers.faabContext` -- the last-resolved `useAsync`
 * response. Because the input state updates synchronously on click/edit
 * but the matching response only lands after a real network round trip,
 * the label could visibly disagree with the data it was labeling for the
 * length of that round trip (e.g. an "SCENARIO" badge shown over numbers
 * that were still last request's LIVE response).
 *
 * `resolveFaabDisplay`'s signature is the fix's structural guarantee: it
 * takes ONLY `WaiverFaabContext` (a field living on the SAME resolved
 * response object supplying the numbers/bid list) -- there is no
 * parameter through which any current-input-state flag (like
 * `budgetScenario`) could leak into the label. It is not possible to call
 * this function with "the input's mode" instead of "the response's mode"
 * by construction, not just by runtime discipline.
 */
describe("resolveFaabDisplay (LIVE/SCENARIO race fix -- label derived only from the response)", () => {
  it("reads LIVE from a real live budgetMode, independent of any input-state concept", () => {
    const display = resolveFaabDisplay(faabContext({ budgetMode: "LIVE" }));
    expect(display.isScenario).toBe(false);
    expect(display.metricTone).toBe("gold");
    expect(display.weeksTone).toBe("violet");
    expect(display.eyebrow).toContain("LIVE");
    expect(display.alertHeadline).toBeNull();
    expect(display.alertBody).toBeNull();
  });

  it("reads SCENARIO from a real scenario budgetMode, and echoes the RESPONSE's own scenario numbers -- never a separately-supplied input value", () => {
    const display = resolveFaabDisplay(
      faabContext({
        budgetMode: "SCENARIO",
        remainingBudgetDollars: 42,
        totalBudgetDollars: 60,
        weeksRemaining: 5,
        weeksRemainingSource: "SCENARIO_INPUT",
        scenario: { remainingBudgetDollars: 42, totalBudgetDollars: 60, weeksRemaining: 5 },
      }),
    );
    expect(display.isScenario).toBe(true);
    expect(display.metricTone).toBe("crimson");
    expect(display.weeksTone).toBe("crimson");
    expect(display.eyebrow).toContain("SCENARIO");
    expect(display.alertHeadline).toBe("SCENARIO -- not your real live budget");
    expect(display.alertBody).toBe(
      "You're viewing a hypothetical: what if your budget were $42 of $60, 5 weeks remaining? Bid ranges below are computed from these numbers, not your real Sleeper budget.",
    );
  });

  it("never fabricates scenario alert text when budgetMode says SCENARIO but the response carries no scenario echo (a real degrade-honestly edge, not assumed impossible)", () => {
    const display = resolveFaabDisplay(faabContext({ budgetMode: "SCENARIO", scenario: null }));
    expect(display.isScenario).toBe(true);
    expect(display.alertHeadline).toBe("SCENARIO -- not your real live budget");
    expect(display.alertBody).toBeNull();
  });

  it("the function has no parameter for current-input state at all -- TypeScript itself would reject a second argument", () => {
    // @ts-expect-error -- resolveFaabDisplay(faabContext, someInputStateFlag) must not compile.
    resolveFaabDisplay(faabContext(), true);
    expect(resolveFaabDisplay.length).toBe(1);
  });
});
