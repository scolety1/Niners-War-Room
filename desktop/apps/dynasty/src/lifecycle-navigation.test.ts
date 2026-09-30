import { describe, expect, it } from "vitest";

import { buildDynastyNavigation } from "./DynastyApp";

describe("Dynasty lifecycle navigation", () => {
  it("uses the in-season hierarchy without Draft Cockpit", () => {
    const groups = buildDynastyNavigation("REGULAR_SEASON");
    expect(groups.map((group) => group.label)).toEqual([
      "Home", "Team", "Trades", "Assets", "System",
    ]);
    const items = groups.flatMap((group) => group.items);
    expect(items.map((item) => item.label)).not.toContain("Draft Cockpit");
    expect(items.every((item) => !item.shortcut)).toBe(true);
  });

  it("promotes rookie and draft tools outside the season", () => {
    const labels = buildDynastyNavigation("ROOKIE_PRE_DRAFT")
      .flatMap((group) => group.items.map((item) => item.label));
    expect(labels).toContain("Draft Cockpit");
    expect(labels).toContain("Rookie Review");
  });
});
