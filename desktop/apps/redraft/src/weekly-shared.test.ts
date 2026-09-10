import { describe, expect, it } from "vitest";

import { ACTION_CATEGORY_LABEL, ACTION_CATEGORY_LINK, formatClock, statusTone } from "./weekly-shared";

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
