import { describe, expect, it } from "vitest";

import { stableSortRows } from "./table-sort";

describe("stableSortRows", () => {
  const rows = [
    { id: "ten", value: 10 },
    { id: "missing-a", value: null },
    { id: "two-a", value: 2 },
    { id: "two-b", value: 2 },
    { id: "missing-b", value: undefined },
  ];

  it("sorts numbers numerically, keeps ties stable, and puts missing values last", () => {
    expect(stableSortRows(rows, (row) => row.value, "number", "ascending").map((row) => row.id)).toEqual([
      "two-a",
      "two-b",
      "ten",
      "missing-a",
      "missing-b",
    ]);
  });

  it("keeps missing values last when descending", () => {
    expect(stableSortRows(rows, (row) => row.value, "number", "descending").map((row) => row.id)).toEqual([
      "ten",
      "two-a",
      "two-b",
      "missing-a",
      "missing-b",
    ]);
  });

  it("uses owner-friendly natural text sorting", () => {
    const textRows = [
      { id: "wr-10", value: "WR10" },
      { id: "missing", value: "" },
      { id: "wr-2", value: "WR2" },
    ];
    expect(stableSortRows(textRows, (row) => row.value, "text", "ascending").map((row) => row.id)).toEqual([
      "wr-2",
      "wr-10",
      "missing",
    ]);
  });
});
