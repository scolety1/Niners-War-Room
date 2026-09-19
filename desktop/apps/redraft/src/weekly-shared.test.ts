import { describe, expect, it } from "vitest";

import type { WaiverAddCandidate } from "@nwr/contracts";

import {
  ACTION_CATEGORY_LABEL,
  ACTION_CATEGORY_LINK,
  createStaleResponseGuard,
  describeUnmatchedRosterPlayers,
  FAAB_URGENCY_TONE,
  formatClock,
  resolveHomeActionFreshness,
  resolveSeasonProjectionBasisCaption,
  resolveWeekDisplay,
  statusTone,
} from "./weekly-shared";

describe("statusTone (Start/Sit status heuristic)", () => {
  it("reads a healthy status as safe", () => {
    expect(statusTone("OK")).toBe("safe");
  });
  it("reads a real out/IR/suspended status as blocked", () => {
    expect(statusTone("OUT")).toBe("blocked");
    expect(statusTone("IR")).toBe("blocked");
    expect(statusTone("SUSPENDED")).toBe("blocked");
  });
  it("reads uncertain statuses (empty slot, unprojected, questionable, doubtful, unknown) as review, never fabricated safe", () => {
    expect(statusTone("EMPTY")).toBe("review");
    expect(statusTone("UNPROJECTED")).toBe("review");
    expect(statusTone("QUESTIONABLE")).toBe("review");
    expect(statusTone("DOUBTFUL")).toBe("review");
    expect(statusTone("STATUS_UNKNOWN_UNMATCHED_IDENTITY")).toBe("review");
    expect(statusTone(null)).toBe("review");
    expect(statusTone(undefined)).toBe("review");
  });
  // NWR Sunday Readiness overnight cycle, Worker 2 (W3 regression): real
  // bug -- this real backend status string (weekly_lineup_optimizer_
  // service's `UNRESOLVED_IDENTITY`) previously matched none of the
  // "review" substrings and fell through to "safe", making an
  // identity-unconfirmed starter look identical to a confirmed OK one.
  it("reads an unresolved-identity starter as review, never safe", () => {
    expect(statusTone("UNRESOLVED_IDENTITY")).toBe("review");
  });
});

describe("Weekly Home NWR Actions category maps", () => {
  it("has a link for every labeled category, so no action ever renders a dead 'Open' link", () => {
    for (const category of Object.keys(ACTION_CATEGORY_LABEL)) {
      expect(ACTION_CATEGORY_LINK[category]).toBeTruthy();
    }
  });
});

describe("FAAB_URGENCY_TONE (regression: backend/contract enum mismatch)", () => {
  it("covers every real value the shared contract's faabUrgency field allows, with no fallback needed", () => {
    // Real, previously-shipping bug: the backend once emitted
    // STARTER_UPGRADE/BENCH_DEPTH/LOW_VALUE while this table (and
    // improve-team.tsx's FAAB_URGENCY_RANK) only recognized
    // HIGH/MEDIUM/LOW, so every FAAB urgency badge fell through to the
    // "review" fallback tone regardless of the real value. Typing the
    // fixture as the real contract type (not a hand-rolled string) means
    // this test fails to compile if the contract's literal union and this
    // lookup table ever drift apart again.
    const values: NonNullable<WaiverAddCandidate["faabUrgency"]>[] = ["HIGH", "MEDIUM", "LOW"];
    for (const value of values) {
      expect(FAAB_URGENCY_TONE[value]).toBeDefined();
    }
    expect(FAAB_URGENCY_TONE.HIGH).toBe("blocked");
    expect(FAAB_URGENCY_TONE.MEDIUM).toBe("review");
    expect(FAAB_URGENCY_TONE.LOW).toBe("safe");
  });
});

/**
 * Work Unit 15 (Live Player Intelligence V1) -- active-profile /
 * stale-response adversary property.
 *
 * Targets the real bug class named by the governing directive: "a
 * delayed/out-of-order async response after a profile switch...the UI
 * [must] never apply a stale response to the new active profile." This
 * exercises `createStaleResponseGuard` the SAME way `useAsync`'s own
 * effect body actually uses it (`runGuardedFetch` below is a faithful,
 * 1:1 reproduction of that usage, not a simplified restatement), driven
 * by manually-resolvable ("deferred") promises so the test controls
 * arrival order directly rather than hoping real timing cooperates.
 *
 * No property-testing library is available in this repo (checked:
 * `hypothesis` is Python-only and unused here; no JS equivalent --
 * `fast-check` -- is installed, and this pass does not add a new
 * dependency for one test file). These four cases are deliberately
 * chosen to stand in for "any sequence of arrival orders": a simple
 * switch-then-stale-resolves-late case, a switch-after-resolution
 * (non-stale) case, a rapid multi-switch case where every earlier
 * fetch resolves AFTER every later one, and a same-profile RELOAD case
 * (proving the guard covers `useAsync`'s full real dependency array --
 * `[...deps, attempt]` -- not just a profile/league change).
 */
function runGuardedFetch<T>(promise: Promise<T>, applied: T[]): ReturnType<typeof createStaleResponseGuard> {
  const guard = createStaleResponseGuard();
  promise.then((value) => {
    if (!guard.isStale()) applied.push(value);
  });
  return guard;
}

function deferred<T>(): { promise: Promise<T>; resolve: (value: T) => void } {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((r) => {
    resolve = r;
  });
  return { promise, resolve };
}

describe("createStaleResponseGuard (active-profile stale-response adversary)", () => {
  it("never applies a response that resolves AFTER its guard was superseded by a profile switch", async () => {
    const applied: string[] = [];
    const a = deferred<string>();
    const guardA = runGuardedFetch(a.promise, applied);

    // Owner switches leagues/profiles before A's response ever arrives --
    // exactly what `useAsync`'s cleanup does when `deps` changes.
    guardA.supersede();
    const b = deferred<string>();
    runGuardedFetch(b.promise, applied);
    b.resolve("profile-B-data");
    await b.promise;

    // A's stale response FINALLY arrives, out of order, after B already
    // applied -- it must never land.
    a.resolve("profile-A-data");
    await a.promise;

    expect(applied).toEqual(["profile-B-data"]);
  });

  it("still applies a response that resolves BEFORE any switch happens (the ordinary, non-stale case)", async () => {
    const applied: string[] = [];
    const a = deferred<string>();
    runGuardedFetch(a.promise, applied);
    a.resolve("profile-A-data");
    await a.promise;

    expect(applied).toEqual(["profile-A-data"]);
  });

  it("discards every earlier fetch's response even when they all resolve AFTER the current one, across a rapid multi-switch", async () => {
    const applied: string[] = [];
    const a = deferred<string>();
    const guardA = runGuardedFetch(a.promise, applied);
    guardA.supersede(); // switched to B before A resolved

    const b = deferred<string>();
    const guardB = runGuardedFetch(b.promise, applied);
    guardB.supersede(); // switched to C before B resolved

    const c = deferred<string>();
    runGuardedFetch(c.promise, applied);
    c.resolve("profile-C-data");
    await c.promise;

    // A and B's real responses arrive last, in arrival order A-then-B --
    // both are stale relative to their OWN supersession, regardless of
    // when they actually resolve.
    b.resolve("profile-B-data-late");
    await b.promise;
    a.resolve("profile-A-data-very-late");
    await a.promise;

    expect(applied).toEqual(["profile-C-data"]);
  });

  it("also guards a same-profile RELOAD (useAsync's real deps array includes `attempt`, not only profileId)", async () => {
    const applied: number[] = [];
    const firstReload = deferred<number>();
    const guardFirst = runGuardedFetch(firstReload.promise, applied);

    // A second reload (same profile, `attempt` incremented) fires before
    // the first one resolved.
    guardFirst.supersede();
    const secondReload = deferred<number>();
    runGuardedFetch(secondReload.promise, applied);
    secondReload.resolve(2);
    await secondReload.promise;

    firstReload.resolve(1);
    await firstReload.promise;

    expect(applied).toEqual([2]);
  });
});

/**
 * Week-display race fix (shared upgrade B, 2026-09-16) -- same bug class
 * as the FAAB LIVE/SCENARIO race (`resolveFaabDisplay`,
 * improve-team-explain.ts), applied to Weekly Home and Start/Sit. Real,
 * reproduced-by-inspection bug: both pages previously rendered the raw
 * input `week` (from `WeekControl`'s local state) in the page title/"Week"
 * chip, while the action cards/lineup/bench below kept rendering the
 * PREVIOUS `useAsync` response until the new week's fetch resolved --
 *`ProviderStatusLine` on the same page already correctly showed its own
 * week off the resolved response's `providerHealth.week`, so the two
 * labels on one page could disagree mid-transition. Fixed the same way as
 * FAAB: derive the displayed week from the SAME resolved response that
 * supplies the data, never from the separate input state directly.
 */
describe("resolveWeekDisplay (Weekly Home / Start-Sit week-display race fix)", () => {
  it("shows the requested week when no response has resolved yet (first load)", () => {
    expect(resolveWeekDisplay(3, null)).toEqual({ displayWeek: 3, isStale: false });
    expect(resolveWeekDisplay(3, undefined)).toEqual({ displayWeek: 3, isStale: false });
  });

  it("shows the resolved response's own week, not the input, once a response exists", () => {
    // The ordinary, settled case: requested and resolved agree.
    expect(resolveWeekDisplay(5, 5)).toEqual({ displayWeek: 5, isStale: false });
  });

  it("flags staleness structurally when the owner has requested a NEW week but the resolved response is still the OLD one -- the exact pending-race window", () => {
    // Owner was on week 2 (resolved), then moved WeekControl to week 3;
    // the week-3 fetch has not resolved yet, so `result`/`actions` here is
    // still real week-2 data. The displayed week must be the DATA's week
    // (2, matching the body still on screen), not the input (3) -- and the
    // mismatch must be flagged so the page can show an explicit pending
    // indicator instead of silently claiming week 3.
    const display = resolveWeekDisplay(3, 2);
    expect(display.displayWeek).toBe(2);
    expect(display.isStale).toBe(true);
  });

  it("clears staleness the instant the new week's response actually lands", () => {
    const display = resolveWeekDisplay(3, 3);
    expect(display).toEqual({ displayWeek: 3, isStale: false });
  });
});

describe("formatClock", () => {
  it("renders a missing timestamp honestly instead of an empty string", () => {
    expect(formatClock(null)).toBe("unavailable");
    expect(formatClock(undefined)).toBe("unavailable");
  });
  it("falls back to the raw string for an unparseable timestamp rather than throwing", () => {
    expect(formatClock("not-a-real-date")).toBe("not-a-real-date");
  });
  it("formats a real ISO timestamp without throwing", () => {
    expect(formatClock("2026-09-10T18:30:00Z")).not.toBe("unavailable");
  });
});

/**
 * Full Cycle V1, Worker 4 (Section 3C): the season-level projection basis
 * caption. Data-age/basis labeling only -- no engine value, ranking, or
 * `marginal_roster_utility_v2` computation is touched by either function
 * under test here.
 */
describe("resolveSeasonProjectionBasisCaption", () => {
  it("names the real admission date when one is known", () => {
    const caption = resolveSeasonProjectionBasisCaption("2026-09-08");
    expect(caption).toContain("2026-09-08");
    expect(caption).toContain("not reduced for games already played");
  });

  it("degrades honestly (no fabricated date) when the admission date is missing", () => {
    expect(resolveSeasonProjectionBasisCaption(null)).toBe(
      "Season-level values reflect NWR's governed season model; admission date unavailable.",
    );
    expect(resolveSeasonProjectionBasisCaption(undefined)).toBe(
      "Season-level values reflect NWR's governed season model; admission date unavailable.",
    );
    expect(resolveSeasonProjectionBasisCaption("")).toBe(
      "Season-level values reflect NWR's governed season model; admission date unavailable.",
    );
  });
});

/**
 * Weekly Home's "NWR Actions" list previously labeled every action card
 * (including WAIVER/TRADE, which are season-ranking-driven, not weekly-
 * provider-driven) with the SAME weekly-provider freshness note -- a real
 * basis mismatch this function fixes by routing WAIVER/TRADE to the season
 * caption instead.
 */
describe("resolveHomeActionFreshness", () => {
  const weeklyNote = "Sleeper · updated Sep 16, 3:00 PM";
  const seasonDate = "2026-09-08";

  it("keeps the weekly provider note for START_SIT and START_SIT_CLOSE_CALL (genuinely weekly-sourced)", () => {
    expect(resolveHomeActionFreshness("START_SIT", weeklyNote, seasonDate)).toBe(weeklyNote);
    expect(resolveHomeActionFreshness("START_SIT_CLOSE_CALL", weeklyNote, seasonDate)).toBe(weeklyNote);
  });

  it("keeps the weekly provider note for STREAMER (its own separate FantasyPros ECR source, unchanged by this fix)", () => {
    expect(resolveHomeActionFreshness("STREAMER", weeklyNote, seasonDate)).toBe(weeklyNote);
  });

  it("routes WAIVER and TRADE to the season admission date instead of the weekly note -- the real basis mismatch this fixes", () => {
    expect(resolveHomeActionFreshness("WAIVER", weeklyNote, seasonDate)).toBe(
      "NWR season ranking · admitted 2026-09-08",
    );
    expect(resolveHomeActionFreshness("TRADE", weeklyNote, seasonDate)).toBe(
      "NWR season ranking · admitted 2026-09-08",
    );
  });

  it("falls back to the weekly note for WAIVER/TRADE only when the season admission date is itself unavailable, rather than showing a blank caption", () => {
    expect(resolveHomeActionFreshness("WAIVER", weeklyNote, null)).toBe(weeklyNote);
    expect(resolveHomeActionFreshness("TRADE", weeklyNote, undefined)).toBe(weeklyNote);
  });
});

/**
 * NWR Full Cycle V1 (Worker 7): "Unresolved roster Sleeper IDs: 3451, NE"
 * investigation -- both real entries turned out to be a real Sleeper K and
 * DST whose position has zero rows in NWR's governed ranking by design, not
 * a genuine identity failure. This renders the backend's new per-id label/
 * reason when present, and honestly degrades (no fabricated reason) for any
 * older/cached response that only carries the raw id list.
 */
describe("describeUnmatchedRosterPlayers", () => {
  it("returns an empty list when nothing is unmatched", () => {
    expect(describeUnmatchedRosterPlayers([], [])).toEqual([]);
    expect(describeUnmatchedRosterPlayers([], undefined)).toEqual([]);
  });

  it("renders label + reason from the backend-supplied detail when present", () => {
    const described = describeUnmatchedRosterPlayers(
      ["3451", "NE"],
      [
        { sleeperId: "3451", label: "Ka'imi Fairbairn (K)", reason: "Outside NWR's ranked model -- K/DST are not part of the governed ranking.", category: "OUT_OF_RANKED_MODEL_SCOPE" },
        { sleeperId: "NE", label: "NE D/ST (DST)", reason: "Outside NWR's ranked model -- K/DST are not part of the governed ranking.", category: "OUT_OF_RANKED_MODEL_SCOPE" },
      ],
    );
    expect(described).toEqual([
      "Ka'imi Fairbairn (K) -- Outside NWR's ranked model -- K/DST are not part of the governed ranking.",
      "NE D/ST (DST) -- Outside NWR's ranked model -- K/DST are not part of the governed ranking.",
    ]);
  });

  it("honestly falls back to a raw-id line (no fabricated reason) when the detail field is absent", () => {
    expect(describeUnmatchedRosterPlayers(["3451", "NE"], undefined)).toEqual([
      "Sleeper id 3451 -- reason unavailable",
      "Sleeper id NE -- reason unavailable",
    ]);
  });

  it("falls back per-id when the detail array is present but shorter than the id list (defensive, should not happen in practice)", () => {
    const described = describeUnmatchedRosterPlayers(["3451", "NE"], []);
    expect(described).toEqual([
      "Sleeper id 3451 -- reason unavailable",
      "Sleeper id NE -- reason unavailable",
    ]);
  });
});
