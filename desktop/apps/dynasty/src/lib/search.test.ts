import { describe, expect, it } from "vitest";

import { matchesPlayerSearch, normalizePlayerSearch } from "./search";

describe("governed asset search normalization", () => {
  it("finds Stribling by exact, partial, apostrophe-free, and curly-apostrophe text", () => {
    const parts = ["De'Zhaun Stribling", "SF", "WR", "00-0041035"];

    expect(matchesPlayerSearch(parts, "De'Zhaun Stribling")).toBe(true);
    expect(matchesPlayerSearch(parts, "Stribling")).toBe(true);
    expect(matchesPlayerSearch(parts, "Dezhaun")).toBe(true);
    expect(matchesPlayerSearch(parts, "De’Zhaun")).toBe(true);
    expect(matchesPlayerSearch(parts, "00-0041035")).toBe(true);
    expect(normalizePlayerSearch("De'Zhaun Stribling")).toBe("dezhaunstribling");
  });
});
