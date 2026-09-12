import { describe, expect, it } from "vitest";
import type { WeeklyLineupSlot, WeeklyLineupSwap } from "@nwr/contracts";
import { explainLineupSwap, findResultingSlot } from "./lineup-explain";

function makeSlot(overrides: Partial<WeeklyLineupSlot> = {}): WeeklyLineupSlot {
  return {
    slotType: "WR",
    player: null,
    status: "healthy",
    closeCall: false,
    closeCallAlternative: null,
    closeCallMargin: null,
    ...overrides,
  };
}

function makeSlotPlayer(playerName: string): NonNullable<WeeklyLineupSlot["player"]> {
  return {
    sleeperPlayerId: playerName,
    canonicalPlayerId: playerName,
    playerName,
    position: "WR",
    team: "SF",
    projectedPoints: 10,
    playerAvailabilityStatus: null,
  };
}

function makeSwap(overrides: Partial<WeeklyLineupSwap> = {}): WeeklyLineupSwap {
  return {
    slotType: "WR",
    startPlayer: "Player A",
    benchPlayer: "Player B",
    projectedDelta: 2.8,
    summary: "Start Player A over Player B",
    ...overrides,
  };
}

describe("findResultingSlot", () => {
  it("matches a swap to its post-swap starter by slotType + player identity", () => {
    const starters = [
      makeSlot({ slotType: "RB" }),
      makeSlot({ slotType: "WR", status: "questionable", player: makeSlotPlayer("Player A") }),
    ];
    const swap = makeSwap({ slotType: "WR", startPlayer: "Player A" });
    expect(findResultingSlot(swap, starters)?.status).toBe("questionable");
  });

  it("returns null, never a wrong slot, when no starter shares the slotType", () => {
    const swap = makeSwap({ slotType: "TE" });
    expect(findResultingSlot(swap, [makeSlot({ slotType: "WR" })])).toBeNull();
  });

  // Real bug found+fixed this pass: slotType alone is not a unique key --
  // a roster can carry two starting slots of the same type (e.g. two WR
  // slots). Matching on slotType only would silently read the WRONG
  // slot's status/close-call data whenever the swap applies to the
  // second slot of that type.
  it("does not grab the wrong same-slotType slot when more than one WR starter exists", () => {
    const starters = [
      makeSlot({ slotType: "WR", status: "healthy", player: makeSlotPlayer("Player A"), closeCall: false }),
      makeSlot({ slotType: "WR", status: "questionable", player: makeSlotPlayer("Player Z"), closeCall: true, closeCallAlternative: "Player Y" }),
    ];
    const swap = makeSwap({ slotType: "WR", startPlayer: "Player Z", benchPlayer: "Player Y" });
    const resultingSlot = findResultingSlot(swap, starters);
    expect(resultingSlot?.player?.playerName).toBe("Player Z");
    expect(resultingSlot?.status).toBe("questionable");
    expect(resultingSlot?.closeCall).toBe(true);
  });
});

describe("explainLineupSwap", () => {
  it("explains a confident swap using the real projectedDelta, tone=recommended", () => {
    const swap = makeSwap();
    const result = explainLineupSwap(swap, makeSlot({ status: "healthy", closeCall: false }));
    expect(result.headline).toBe("Start Player A over Player B");
    expect(result.impact).toBe("+2.8 projected points");
    expect(result.tone).toBe("recommended");
    expect(result.confidence).toBeNull();
    expect(result.alternative).toBeNull();
    expect(result.status).toBe("healthy");
  });

  it("formats a negative-delta swap's impact with a leading minus, not a double sign", () => {
    const result = explainLineupSwap(makeSwap({ projectedDelta: -1.25 }), null);
    expect(result.impact).toBe("-1.3 projected points");
  });

  it("marks a swap whose resulting slot is a real close call as tone=warning, confidence=LOW", () => {
    const slot = makeSlot({ closeCall: true, closeCallAlternative: "Player C", closeCallMargin: 0.4, status: "questionable" });
    const result = explainLineupSwap(makeSwap(), slot);
    expect(result.tone).toBe("warning");
    expect(result.confidence).toBe("LOW");
    expect(result.alternative).toBe("Player C");
    expect(result.status).toBe("questionable");
    expect(result.why).toMatch(/close call/);
  });

  it("degrades honestly (status null, tone unaffected) when no resulting slot is found", () => {
    const result = explainLineupSwap(makeSwap(), null);
    expect(result.status).toBeNull();
    expect(result.tone).toBe("recommended");
    expect(result.alternative).toBeNull();
  });

  it("never fabricates an alternative for a confident swap even if the slot happens to carry one", () => {
    // A close-call flag of false is authoritative -- a stray
    // closeCallAlternative value on a non-close-call slot must not leak
    // into the card (this would be a real fabrication bug).
    const slot = makeSlot({ closeCall: false, closeCallAlternative: "Player Z" });
    const result = explainLineupSwap(makeSwap(), slot);
    expect(result.alternative).toBeNull();
  });
});
