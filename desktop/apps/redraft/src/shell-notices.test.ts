import type { DraftBoard, LeagueProfile, Notice, RedraftBootstrap, RedraftHealth, SourceStatus } from "@nwr/contracts";
import { describe, expect, it } from "vitest";

import { summarizeShellNotices } from "./shell-notices";

/**
 * P2-1 (Data Notice Strip, 2026-09-12/13): focused unit tests for the pure
 * classification `summarizeShellNotices` -- the shell header chip and its
 * click-through panel (shell-identity.tsx's `FreshnessIndicator`) render
 * exactly this result, so covering the derivation here covers the real
 * owner-visible states.
 */

function profile(overrides: Partial<LeagueProfile> = {}): LeagueProfile {
  return {
    profileId: "p1",
    leagueName: "Test League",
    season: 2026,
    teamCount: 10,
    roster: { qb: 1, rb: 2, wr: 2, te: 1, flex: 1, superflex: 0, k: 1, dst: 1, benchSize: 6 },
    scoring: {
      passingYards: 0.04, passingTd: 4, interception: -2, rushingYards: 0.1, rushingTd: 6,
      receivingYards: 0.1, reception: 1, receivingTd: 6, passingFirstDown: 0, rushingFirstDown: 0,
      receivingFirstDown: 0, returnYards: 0, returnTd: 6, fumbleLost: -2, tePremium: 0, bonuses: {},
    },
    draft: {
      draftType: "snake", draftSlot: null, rounds: 15, keeperCount: 0, auctionBudget: null,
      rosterLimits: [], adpContextEnabled: true, replacementMethod: "expected_available",
    },
    presetKey: null,
    archived: false,
    createdAtUtc: "2026-01-01T00:00:00Z",
    updatedAtUtc: "2026-01-01T00:00:00Z",
    practicalMode: false,
    nwrPureExperimental: false,
    provider: "local",
    providerLeagueId: null,
    ...overrides,
  };
}

function health(overrides: Partial<RedraftHealth> = {}): RedraftHealth {
  return {
    status: "READY",
    playerUniverseAvailable: true,
    currentSeasonForecastAvailable: true,
    scoringProfileValid: true,
    replacementCalculationValid: true,
    rankedPlayers: 500,
    blockedPlayers: 0,
    lastGeneratedTimestamp: "2026-09-12T00:00:00Z",
    messages: [],
    ...overrides,
  };
}

function status(overrides: Partial<SourceStatus> = {}): SourceStatus {
  return {
    ready: true,
    tone: "ready",
    authority: "Redraft V1 — review authority",
    sourceAsOf: "2026-09-12",
    freshness: "Governed current-season projection snapshot",
    summary: "Profile-adjusted Redraft rankings are ready.",
    scheduledRefresh: "Off — owner approval required",
    errors: [],
    warnings: [],
    ...overrides,
  };
}

const ALWAYS_PRESENT_NOTICES: Notice[] = [
  { tone: "ready", title: "Redraft is isolated from Dynasty", message: "League profiles and draft state never change Dynasty authority." },
  { tone: "review", title: "Current-season evidence only", message: "Redraft rankings require governed projections for the active season." },
  { tone: "review", title: "Role-change context is not yet modeled", message: "This projection snapshot uses prior-season production plus current identity/status." },
  { tone: "review", title: "External K/DST consensus boundary", message: "FantasyPros API key is not configured. No provider request was attempted; the existing K/DST manual-draft fallback is not yet admitted." },
];

function draftBoard(overrides: Partial<DraftBoard> = {}): DraftBoard {
  return { schemaVersion: 1, profileId: "p1", drafted: [], ...overrides };
}

function bootstrap(overrides: Partial<RedraftBootstrap> = {}): RedraftBootstrap {
  return {
    product: { title: "Niners War Room — Redraft", contextLabel: "Redraft workspace", authority: "Redraft V1" },
    status: status(),
    profiles: [profile()],
    presets: [],
    activeProfileId: "p1",
    activeProfile: profile(),
    rankings: [],
    replacementLevels: [],
    draftBoard: draftBoard(),
    health: health(),
    notices: [...ALWAYS_PRESENT_NOTICES],
    ...overrides,
  };
}

describe("summarizeShellNotices", () => {
  it("reports the calm 'Current' state when nothing is actually wrong, ignoring the always-present product-boundary disclosures", () => {
    const summary = summarizeShellNotices(bootstrap());
    expect(summary).toEqual({ count: 0, label: "Current", tone: "healthy", items: [] });
  });

  it("returns the calm state with no active league (nothing to summarize yet)", () => {
    const summary = summarizeShellNotices(bootstrap({ activeProfileId: null, activeProfile: null }));
    expect(summary).toEqual({ count: 0, label: "Current", tone: "healthy", items: [] });
  });

  it("surfaces exactly one genuinely conditional notice as a specific, short label", () => {
    const data = bootstrap({
      notices: [
        ...ALWAYS_PRESENT_NOTICES,
        { tone: "review", title: "PRACTICAL SCORING", message: "NWR models the major QB/RB/WR/TE scoring rules for this league. Kicker and DST are manual/unmodeled." },
      ],
    });
    const summary = summarizeShellNotices(data);
    expect(summary.count).toBe(1);
    expect(summary.label).toBe("PRACTICAL SCORING");
    expect(summary.tone).toBe("warning");
    expect(summary.items).toEqual([
      { title: "PRACTICAL SCORING", message: "NWR models the major QB/RB/WR/TE scoring rules for this league. Kicker and DST are manual/unmodeled.", blocked: false },
    ]);
  });

  it("counts multiple genuine issues and reports a plain count, not a list of titles", () => {
    const data = bootstrap({
      health: health({ playerUniverseAvailable: false }),
      notices: [
        ...ALWAYS_PRESENT_NOTICES,
        { tone: "review", title: "1 rookie remains blocked", message: "Some Rookie remains excluded because their draft position conflicts with the current factual registry; no values were imputed." },
        { tone: "review", title: "Draft rounds do not match roster capacity", message: "This profile is configured for 16 rounds but 9 starters + 6 bench = 15 real roster slots." },
      ],
    });
    const summary = summarizeShellNotices(data);
    expect(summary.count).toBe(3);
    expect(summary.label).toBe("3 data issues");
    expect(summary.tone).toBe("unavailable"); // identity-unavailable is a blocked-severity issue
  });

  it("treats an unavailable market ADP snapshot as a real, owner-relevant single issue", () => {
    const data = bootstrap({
      draftBoard: draftBoard({
        adp: {
          available: false,
          source: "none",
          sourceDate: "",
          importedAtUtc: "",
          matchedPlayers: 0,
          rankingPlayers: 0,
          coverage: 0,
          unmatched: [],
          sourceSha256: "",
          authority: "Owner-imported ADP",
          message: "No ADP snapshot is available for this league yet.",
        },
      }),
    });
    const summary = summarizeShellNotices(data);
    expect(summary.count).toBe(1);
    expect(summary.label).toBe("Market ADP unavailable");
    expect(summary.tone).toBe("warning");
  });

  it("surfaces a blocked (not merely reviewable) status as its own issue with 'unavailable' severity", () => {
    const data = bootstrap({ status: status({ ready: false, tone: "blocked", summary: "Governed projections are unavailable." }) });
    const summary = summarizeShellNotices(data);
    expect(summary.count).toBe(1);
    expect(summary.label).toBe("Projections blocked");
    expect(summary.tone).toBe("unavailable");
  });

  it("never lets a stale prior league's notices leak into a freshly-activated league's summary (state-leakage check)", () => {
    const leagueA = bootstrap({
      activeProfileId: "a",
      activeProfile: profile({ profileId: "a", leagueName: "League A" }),
      notices: [...ALWAYS_PRESENT_NOTICES, { tone: "review", title: "PRACTICAL SCORING", message: "League A has practical scoring on." }],
    });
    const leagueB = bootstrap({
      activeProfileId: "b",
      activeProfile: profile({ profileId: "b", leagueName: "League B" }),
      notices: [...ALWAYS_PRESENT_NOTICES],
    });

    const summaryA = summarizeShellNotices(leagueA);
    expect(summaryA.count).toBe(1);
    expect(summaryA.label).toBe("PRACTICAL SCORING");

    // Activating a different league replaces `data` wholesale (RedraftApp's
    // `onUpdate`); a fresh call against that new object must never carry
    // over League A's issue.
    const summaryB = summarizeShellNotices(leagueB);
    expect(summaryB).toEqual({ count: 0, label: "Current", tone: "healthy", items: [] });

    // Re-summarizing League A again afterward must still be exactly what
    // it was -- the function must not have mutated either input.
    expect(summarizeShellNotices(leagueA)).toEqual(summaryA);
  });

  it("excludes the always-present product-boundary disclosures by title even when their tone is 'blocked'", () => {
    const data = bootstrap({
      notices: [
        { tone: "ready", title: "Redraft is isolated from Dynasty", message: "..." },
        { tone: "review", title: "Current-season evidence only", message: "..." },
        { tone: "review", title: "Role-change context is not yet modeled", message: "..." },
        { tone: "blocked", title: "External K/DST consensus boundary", message: "FantasyPros API key is not configured." },
      ],
    });
    const summary = summarizeShellNotices(data);
    expect(summary).toEqual({ count: 0, label: "Current", tone: "healthy", items: [] });
  });
});
