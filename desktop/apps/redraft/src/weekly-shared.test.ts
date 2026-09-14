import { describe, expect, it } from "vitest";

import type { WaiverAddCandidate } from "@nwr/contracts";

import {
  ACTION_CATEGORY_LABEL,
  ACTION_CATEGORY_LINK,
  createStaleResponseGuard,
  FAAB_URGENCY_TONE,
  formatClock,
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
