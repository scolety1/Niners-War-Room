import { describe, expect, it } from "vitest";

import { buildNavigation } from "./RedraftApp";

describe("Redraft lifecycle navigation", () => {
  it("foregrounds in-season destinations and hides draft-only tools", () => {
    const groups = buildNavigation("REGULAR_SEASON");
    expect(groups.map((group) => group.label)).toEqual([
      "Home", "Lineup", "Improve Team", "Trades", "Rankings", "League",
    ]);
    const labels = groups.flatMap((group) => group.items.map((item) => item.label));
    expect(labels).toContain("Waiver Wire");
    expect(labels).toContain("Streamers");
    expect(labels).toContain("Weekly Rankings");
    expect(labels).not.toContain("Draft Room");
    expect(labels).not.toContain("Cheat Sheet");
  });

  it("promotes draft tools during draft season", () => {
    const labels = buildNavigation("DRAFT_APPROACHING")
      .flatMap((group) => group.items.map((item) => item.label));
    expect(labels).toContain("Draft Room");
    expect(labels).toContain("Cheat Sheet");
  });
});
