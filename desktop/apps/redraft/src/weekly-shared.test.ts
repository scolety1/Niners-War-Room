import { describe, expect, it } from "vitest";

import type { WaiverAddCandidate } from "@nwr/contracts";

import { ACTION_CATEGORY_LABEL, ACTION_CATEGORY_LINK, FAAB_URGENCY_TONE, formatClock, statusTone } from "./weekly-shared";

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
