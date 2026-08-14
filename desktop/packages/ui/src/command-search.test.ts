import type { CommandItem } from "@nwr/contracts";
import { describe, expect, it } from "vitest";

import { filterCommandItems } from "./components";

const stribling: CommandItem = {
  id: "asset:stribling",
  label: "De'Zhaun Stribling",
  detail: "Manual Review Rookie",
  path: "/players/stribling",
  icon: "players",
  keywords: ["00-0041035", "SF", "WR"],
};

describe("filterCommandItems", () => {
  it.each([
    "De'Zhaun Stribling",
    "Stribling",
    "Dezhaun",
    "De’Zhaun",
    "De Zhaun",
    "00-0041035",
  ])("finds Stribling for %s", (query) => {
    expect(filterCommandItems([stribling], query)).toEqual([stribling]);
  });

  it("preserves result limits and no-match behavior", () => {
    const commands = Array.from({ length: 15 }, (_, index) => ({
      ...stribling,
      id: `command:${index}`,
      label: `Player ${index}`,
    }));

    expect(filterCommandItems(commands, "")).toHaveLength(10);
    expect(filterCommandItems(commands, "player")).toHaveLength(12);
    expect(filterCommandItems(commands, "not-present")).toEqual([]);
  });
});
