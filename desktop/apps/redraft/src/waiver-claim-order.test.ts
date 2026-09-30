import { describe, expect, it } from "vitest";

import { moveClaim } from "./improve-team";

describe("ordered waiver claim builder", () => {
  it("moves one claim without losing or duplicating another", () => {
    expect(moveClaim(["A", "B", "C"], 2, 0)).toEqual(["C", "A", "B"]);
    expect(moveClaim(["A", "B", "C"], 0, 1)).toEqual(["B", "A", "C"]);
  });

  it("leaves invalid moves unchanged", () => {
    expect(moveClaim(["A", "B"], -1, 0)).toEqual(["A", "B"]);
    expect(moveClaim(["A", "B"], 0, 4)).toEqual(["A", "B"]);
  });
});
