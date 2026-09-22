import { describe, expect, it } from "vitest";
import type { PlayerAvailabilityStatus, WeeklyLineupSlot, WeeklyLineupSwap } from "@nwr/contracts";
import { describeExcludedLineupPlayer, explainLineupSwap, findResultingSlot } from "./lineup-explain";

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
    deltaBasis: "KNOWN",
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

  // NWR connection/update pass, Worker 2 (2026-09-19): the owner-reported
  // Zay Flowers bug, reproduced at this presentation layer -- a swap whose
  // displaced (bench) player has no real weekly projection ("Zay Flowers's
  // projection is missing this week") must never render a fabricated
  // "+11.7 projected points"-style impact, and must not be presented as a
  // confident (tone=recommended) recommendation.
  it("shows an honest 'unknown' impact, never a fabricated number, for a missing-projection delta", () => {
    const swap = makeSwap({
      startPlayer: "Michael Pittman",
      benchPlayer: "Zay Flowers",
      projectedDelta: null,
      deltaBasis: "UNKNOWN_MISSING_BENCH_PROJECTION",
      summary: "START Michael Pittman over Zay Flowers -- Zay Flowers's projection is missing this week; point swing unknown.",
    });
    const result = explainLineupSwap(swap, makeSlot({ status: "healthy", closeCall: false }));
    expect(result.headline).toBe("Start Michael Pittman over Zay Flowers");
    expect(result.impact).not.toMatch(/\+11\.7|\+\d/);
    expect(result.impact).toMatch(/[Uu]nknown/);
    expect(result.why).toMatch(/missing/);
    expect(result.tone).toBe("warning");
    expect(result.confidence).toBe("LOW");
  });
});

function makeAvailabilityStatus(overrides: Partial<PlayerAvailabilityStatus> = {}): PlayerAvailabilityStatus {
  return {
    playerId: "00-0040130",
    playerName: "Jayden Higgins",
    statusCategory: "OUT_FOR_SEASON",
    injuryDesignation: "OUT",
    practiceState: null,
    irPupNfi: null,
    suspension: false,
    administrativeExempt: false,
    released: false,
    currentTeam: null,
    reason: "Torn ACL in training camp; placed on Reserve/Injured (no Designated for Return) -- season-ending for 2026.",
    source: "MANUAL_VERIFIED_OVERRIDE",
    sourceAsOf: "2026-08-19",
    overrideKind: "SEASON_OUT",
    ...overrides,
  };
}

// Waiver-Night Readiness / Hardening cycle, Worker A (2026-09-22): real,
// reproduced bug fix. Live-reproduced against the real Las Vegas Enginerds
// roster in week 3: `WeeklyLineupResult.excluded` is populated ONLY by a
// real, sourced status override (never a roster-slot or missing-projection
// reason -- see `weekly_lineup_optimizer_service.ZERO_VALUE_KINDS`), but the
// Lineup page's "Not included this week" panel used to render a single
// static, FALSE sentence ("no roster slot they're eligible for, or no
// usable projection") for every entry regardless of the real reason already
// available on `playerAvailabilityStatus`.
describe("describeExcludedLineupPlayer", () => {
  it("surfaces the real, sourced exclusion reason instead of the old fabricated roster-slot/projection sentence", () => {
    const result = describeExcludedLineupPlayer(makeAvailabilityStatus());
    expect(result.reason).toBe(
      "Torn ACL in training camp; placed on Reserve/Injured (no Designated for Return) -- season-ending for 2026.",
    );
    expect(result.reason).not.toMatch(/no roster slot|no usable projection/i);
    expect(result.badgeLabel).toBe("OUT FOR SEASON");
  });

  it("distinguishes NOT_WITH_TEAM from SEASON_OUT rather than collapsing every override to one label", () => {
    const result = describeExcludedLineupPlayer(
      makeAvailabilityStatus({ statusCategory: "NOT_WITH_TEAM", overrideKind: "NOT_WITH_TEAM", reason: "Released by club; not currently on any NFL roster." }),
    );
    expect(result.badgeLabel).toBe("NOT WITH TEAM");
    expect(result.reason).toBe("Released by club; not currently on any NFL roster.");
  });

  it("falls back to an honest 'no detail recorded' message, never a fabricated one, when status is null", () => {
    const result = describeExcludedLineupPlayer(null);
    expect(result.reason).toMatch(/no further detail recorded/i);
    expect(result.reason).not.toMatch(/no roster slot|no usable projection/i);
  });
});
