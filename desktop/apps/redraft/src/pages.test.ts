import { describe, expect, it } from "vitest";

import { rankingSearchRows } from "./pages";

describe("ranking search depth", () => {
  it("searches the full filtered universe even when the visible board is capped", () => {
    const rows = Array.from({ length: 608 }, (_, index) => index + 1);

    expect(rankingSearchRows(rows, "100", "")).toHaveLength(100);
    expect(rankingSearchRows(rows, "100", "Brock Purdy")).toHaveLength(608);
  });
});
