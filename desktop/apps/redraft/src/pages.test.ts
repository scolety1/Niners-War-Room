import { describe, expect, it } from "vitest";

import { DRAFT_ROOM_ACCEPTANCE_LABELS, rankingSearchRows } from "./pages";

describe("ranking search depth", () => {
  it("searches the full filtered universe even when the visible board is capped", () => {
    const rows = Array.from({ length: 608 }, (_, index) => index + 1);

    expect(rankingSearchRows(rows, "100", "")).toHaveLength(100);
    expect(rankingSearchRows(rows, "100", "Brock Purdy")).toHaveLength(608);
  });
});

describe("Draft Room owner acceptance surface", () => {
  it("keeps the board, roster, timing, log, and ADP boundary visible", () => {
    expect(DRAFT_ROOM_ACCEPTANCE_LABELS).toEqual([
      "Draft board",
      "My Roster",
      "Available player panel",
      "Recent picks",
      "Full draft log",
      "Beat ADP pool",
      "Draft recommendations",
      "Advance to my pick",
      "Refresh FFC ADP",
      "Paste Rankings / ADP",
      "ADP unavailable",
    ]);
  });
});
