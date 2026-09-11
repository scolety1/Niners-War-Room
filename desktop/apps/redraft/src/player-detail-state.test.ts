import { describe, expect, it } from "vitest";
import type { PlayerAvailabilityStatus } from "@nwr/contracts";

import {
  derivePlayerDetailBackbone,
  isSamePlayerDetailTarget,
  playerAvailabilityBadgeLabel,
  playerAvailabilityBadgeTone,
  togglePlayerDetail,
  type PlayerDetailTarget,
} from "./player-detail-state";

const target = (overrides: Partial<PlayerDetailTarget> = {}): PlayerDetailTarget => ({
  leagueKey: "league-a",
  playerId: "RB-0",
  playerName: "RB 0",
  position: "RB",
  team: "TST",
  source: "LINEUP",
  ...overrides,
});

const status = (overrides: Partial<PlayerAvailabilityStatus> = {}): PlayerAvailabilityStatus => ({
  playerId: "RB-0",
  playerName: "RB 0",
  statusCategory: "OUT_FOR_SEASON",
  injuryDesignation: "OUT",
  practiceState: null,
  irPupNfi: null,
  suspension: false,
  administrativeExempt: false,
  released: false,
  currentTeam: "TST",
  reason: "Season-ending injury",
  source: "MANUAL_VERIFIED_OVERRIDE",
  sourceAsOf: "2026-09-01",
  overrideKind: "SEASON_OUT",
  ...overrides,
});

describe("isSamePlayerDetailTarget", () => {
  it("treats null vs null as the same (both closed)", () => {
    expect(isSamePlayerDetailTarget(null, null)).toBe(true);
  });

  it("treats null vs a real target as different", () => {
    expect(isSamePlayerDetailTarget(null, target())).toBe(false);
    expect(isSamePlayerDetailTarget(target(), null)).toBe(false);
  });

  it("matches on leagueKey + playerId only, regardless of which surface opened it", () => {
    expect(isSamePlayerDetailTarget(target({ source: "LINEUP" }), target({ source: "WAIVER" }))).toBe(true);
  });

  it("treats the same playerId in a different league as different -- no cross-league leak", () => {
    expect(isSamePlayerDetailTarget(target({ leagueKey: "league-a" }), target({ leagueKey: "league-b" }))).toBe(false);
  });

  it("treats a different player in the same league as different", () => {
    expect(isSamePlayerDetailTarget(target({ playerId: "RB-0" }), target({ playerId: "RB-1" }))).toBe(false);
  });
});

describe("togglePlayerDetail", () => {
  it("opens a player when none is currently open", () => {
    expect(togglePlayerDetail(null, target())).toEqual(target());
  });

  it("closes the drawer when the SAME player is opened again (toggle-off)", () => {
    const current = target({ source: "LINEUP" });
    const again = target({ source: "LINEUP" });
    expect(togglePlayerDetail(current, again)).toBeNull();
  });

  it("replaces (never stacks) when a DIFFERENT player is opened -- exactly one drawer app-wide", () => {
    const current = target({ playerId: "RB-0" });
    const next = target({ playerId: "WR-2", playerName: "WR 2", position: "WR" });
    expect(togglePlayerDetail(current, next)).toEqual(next);
  });

  it("switching leagues for the same nominal player id is treated as opening a new target", () => {
    const current = target({ leagueKey: "league-a" });
    const next = target({ leagueKey: "league-b" });
    expect(togglePlayerDetail(current, next)).toEqual(next);
  });
});

describe("derivePlayerDetailBackbone", () => {
  it("returns a null status (never a fabricated OK) when the authority has no entry", () => {
    const backbone = derivePlayerDetailBackbone(target(), []);
    expect(backbone.status).toBeNull();
    expect(backbone.identity).toEqual({
      playerId: "RB-0", playerName: "RB 0", position: "RB", team: "TST",
    });
  });

  it("resolves the SAME canonical status object every surface would see for this player", () => {
    const statuses = [status(), status({ playerId: "WR-9", currentTeam: "OTH" })];
    const backboneFromLineup = derivePlayerDetailBackbone(target({ source: "LINEUP" }), statuses);
    const backboneFromWaivers = derivePlayerDetailBackbone(target({ source: "WAIVER" }), statuses);
    expect(backboneFromLineup.status).toBe(statuses[0]);
    expect(backboneFromWaivers.status).toBe(statuses[0]);
    expect(backboneFromLineup.status).toEqual(backboneFromWaivers.status);
  });

  it("prefers the authority's currentTeam over the caller's seed team when a status exists", () => {
    const backbone = derivePlayerDetailBackbone(
      target({ team: "STALE" }),
      [status({ currentTeam: "REAL" })],
    );
    expect(backbone.identity.team).toBe("REAL");
  });

  it("only matches status by playerId, ignoring leagueKey/source on the target", () => {
    const statuses = [status()];
    const a = derivePlayerDetailBackbone(target({ leagueKey: "league-a", source: "LINEUP" }), statuses);
    const b = derivePlayerDetailBackbone(target({ leagueKey: "league-b", source: "TRADE" }), statuses);
    expect(a.status).toBe(b.status);
  });
});

// NWR pre-UI architecture CLOSURE pass (directive section 2): the ONE
// shared status -> badge tone/label mapping now reused by Draft's
// Suggestions table + PlayerDrawer, Trade Analysis's impact tables, Trade
// Finder's candidate cards, and this primitive's own global drawer.
describe("playerAvailabilityBadgeTone", () => {
  it("reads 'safe' for an absent status -- never a fabricated OK label, but a real no-issue tone", () => {
    expect(playerAvailabilityBadgeTone(null)).toBe("safe");
  });

  it("reads 'blocked' for OUT_FOR_SEASON -- the one real season-ending kind", () => {
    expect(playerAvailabilityBadgeTone(status({ statusCategory: "OUT_FOR_SEASON" }))).toBe("blocked");
  });

  it.each(["NOT_WITH_TEAM", "ADMINISTRATIVE_EXEMPT", "TEAM_CORRECTION"] as const)(
    "reads 'review' (not 'blocked' or 'safe') for the non-season-ending kind %s",
    (statusCategory) => {
      expect(playerAvailabilityBadgeTone(status({ statusCategory }))).toBe("review");
    },
  );
});

describe("playerAvailabilityBadgeLabel", () => {
  it("returns a human-readable 'No status issue' for an absent status", () => {
    expect(playerAvailabilityBadgeLabel(null)).toBe("No status issue");
  });

  it("de-underscores the real statusCategory verbatim, never paraphrasing it", () => {
    expect(playerAvailabilityBadgeLabel(status({ statusCategory: "NOT_WITH_TEAM" }))).toBe("NOT WITH TEAM");
  });
});
