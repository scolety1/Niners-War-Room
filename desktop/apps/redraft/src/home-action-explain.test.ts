import { describe, expect, it } from "vitest";
import type { WeeklyHomeAction } from "@nwr/contracts";
import { explainHomeAction } from "./home-action-explain";

describe("explainHomeAction", () => {
  it("explains a START_SIT swap using its real projectedDelta", () => {
    const action: WeeklyHomeAction = {
      category: "START_SIT",
      priority: 1,
      summary: "Start Player A over Player B",
      detail: { slotType: "WR", startPlayer: "Player A", benchPlayer: "Player B", projectedDelta: 2.8, summary: "Start Player A over Player B" },
    };
    const result = explainHomeAction(action);
    expect(result.expectedImpact).toBe("+2.8 projected points");
    expect(result.confidence).toBeNull();
    expect(result.alternative).toBeNull();
  });

  it("marks a START_SIT_CLOSE_CALL as LOW confidence using the real closeCall signal", () => {
    const action: WeeklyHomeAction = {
      category: "START_SIT_CLOSE_CALL",
      priority: 2,
      summary: "CLOSE CALL at WR",
      detail: { slotType: "WR", player: null, status: "OK", closeCall: true, closeCallAlternative: "Player C", closeCallMargin: 0.4 },
    };
    const result = explainHomeAction(action);
    expect(result.confidence).toBe("LOW");
    expect(result.alternative).toBe("Player C");
    expect(result.expectedImpact).toBe("0.4 pt margin");
  });

  it("explains a WAIVER add using its real marginalUtilityExplanation, never fabricating one", () => {
    const action: WeeklyHomeAction = {
      category: "WAIVER",
      priority: 3,
      summary: "Consider adding Player D",
      detail: {
        sleeperPlayerId: "1", canonicalPlayerId: "1", playerName: "Player D", position: "RB", team: "SF",
        rosReplacementValue: null, rosOverallRank: null, weeklyProjectedPoints: null,
        marginalUtility: 4.2, becomesStarter: true, marginalUtilityExplanation: "Fills a real starter hole at RB.",
        identityStatus: "MATCHED", faabBidLowDollars: null, faabBidHighDollars: null, faabUrgency: null, faabRationale: null,
        playerAvailabilityStatus: null,
      },
    };
    const result = explainHomeAction(action);
    expect(result.why).toBe("Fills a real starter hole at RB.");
    expect(result.secondaryWhy).toMatch(/become a starter/);
    expect(result.expectedImpact).toBe("Marginal utility +4.2");
  });

  it("reads TRADE mutual-improvement from the same signal TradeFinderCard already renders", () => {
    const mutual: WeeklyHomeAction = {
      category: "TRADE",
      priority: 4,
      summary: "Possible trade",
      detail: {
        myGivePlayerId: "1", myGivePlayerName: "A", myGivePlayerAvailabilityStatus: null,
        opponentGivePlayerId: "2", opponentGivePlayerName: "B", opponentGivePlayerAvailabilityStatus: null,
        opponentRosterId: "r1", opponentTeamName: "Team X",
        myNetMarginalUtility: 1.5, opponentNetMarginalUtility: 0.5, myRosValueDelta: 2,
      },
    };
    expect(explainHomeAction(mutual).confidence).toBe("NOMINAL");

    const oneSided: WeeklyHomeAction = {
      ...mutual,
      detail: { ...(mutual.detail as Record<string, unknown>), opponentNetMarginalUtility: -0.5 },
    };
    expect(explainHomeAction(oneSided).confidence).toBe("LOW");
  });

  it("explains a STREAMER row using its real tier/ecr fields", () => {
    const action: WeeklyHomeAction = {
      category: "STREAMER",
      priority: 5,
      summary: "Stream K: Player E",
      detail: { playerName: "Player E", position: "K", team: "SF", ecr: 4, tier: 1, week: 3, authority: "FantasyPros", rosterStatus: "AVAILABLE", recommendation: "ADD" },
    };
    const result = explainHomeAction(action);
    expect(result.why).toMatch(/Tier 1/);
    expect(result.expectedImpact).toBeNull();
  });
});
