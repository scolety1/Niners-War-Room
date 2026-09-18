import type { AssetOwnership } from "@nwr/contracts";
import { describe, expect, it } from "vitest";

import { resolveOwnershipDisplay } from "./ownership";

function ownership(overrides: Partial<AssetOwnership> = {}): AssetOwnership {
  return {
    ownershipStatus: "OWNED",
    rosterId: 7,
    rosterTeamName: "Niners",
    rosterSlotStatus: "starter",
    isMyTeam: true,
    reason: "",
    ...overrides,
  };
}

describe("resolveOwnershipDisplay (Dynasty League Import V1, Worker 3)", () => {
  it("returns null when no league is connected (undefined/null ownership) -- never a fabricated badge", () => {
    expect(resolveOwnershipDisplay(undefined)).toBeNull();
    expect(resolveOwnershipDisplay(null)).toBeNull();
  });

  it("shows a distinct 'on your roster' badge for the owner's own team", () => {
    const display = resolveOwnershipDisplay(ownership({ isMyTeam: true, rosterSlotStatus: "starter" }));
    expect(display).toEqual({
      label: "On your roster",
      tone: "safe",
      detail: "Your roster · starter",
    });
  });

  it("shows the real opponent team name for an owned-but-not-mine asset, never 'On your roster'", () => {
    const display = resolveOwnershipDisplay(
      ownership({ isMyTeam: false, rosterTeamName: "Rocky Mountain High", rosterSlotStatus: "bench" }),
    );
    expect(display).toEqual({
      label: "Owned by Rocky Mountain High",
      tone: "review",
      detail: "Opponent roster · bench",
    });
  });

  it("falls back to a generic label if an opponent roster's team name is somehow empty", () => {
    const display = resolveOwnershipDisplay(
      ownership({ isMyTeam: false, rosterTeamName: "", rosterSlotStatus: null }),
    );
    expect(display?.label).toBe("Owned by another team");
    expect(display?.detail).toBe("Opponent roster");
  });

  it("shows a free-agent badge distinct from both owned states", () => {
    const display = resolveOwnershipDisplay(
      ownership({ ownershipStatus: "FREE_AGENT", rosterId: null, rosterTeamName: null, rosterSlotStatus: null, isMyTeam: false }),
    );
    expect(display).toEqual({
      label: "Free agent",
      tone: "deprioritized",
      detail: "Unowned in your connected league",
    });
  });

  it("shows an honest UNRESOLVED state for rookie assets, never silently omitted or guessed", () => {
    const display = resolveOwnershipDisplay(
      ownership({
        ownershipStatus: "UNRESOLVED",
        rosterId: null,
        rosterTeamName: null,
        rosterSlotStatus: null,
        isMyTeam: false,
        reason: "No Sleeper-ID crosswalk exists yet for rookie board asset IDs.",
      }),
    );
    expect(display?.label).toBe("Ownership unresolved");
    expect(display?.tone).toBe("review");
    expect(display?.detail).toBe("No Sleeper-ID crosswalk exists yet for rookie board asset IDs.");
  });

  it("still discloses an UNRESOLVED status even with an empty reason string, using a safe generic explanation", () => {
    const display = resolveOwnershipDisplay(
      ownership({ ownershipStatus: "UNRESOLVED", reason: "", isMyTeam: false }),
    );
    expect(display?.label).toBe("Ownership unresolved");
    expect(display?.detail).toContain("No identity crosswalk exists yet");
  });
});
