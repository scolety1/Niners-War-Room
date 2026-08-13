import { describe, expect, it } from "vitest";
import type { AssetOption } from "@nwr/contracts";
import { assetExplorerRows } from "./rankings";

const rows: AssetOption[] = [
  { assetId: "player:puka", name: "Puka Nacua", assetType: "Current Player", position: "WR", team: "LAR", rank: 1, authority: "Finished V1", blocked: false },
  { assetId: "rookie:love", name: "Jeremiyah Love", assetType: "Rookie Review", position: "RB", team: "ARI", rank: 1, authority: "2026 Rookie Review", blocked: false },
  { assetId: "pick:2028:2nd", name: "2028 2nd", assetType: "Future Pick", position: "PICK", team: "Owner not encoded", rank: null, authority: "Governed future-pick structure", blocked: true },
];

describe("assetExplorerRows", () => {
  it("searches across the full governed registry", () => {
    expect(assetExplorerRows(rows, "2028", "All", "All").map((row) => row.assetId)).toEqual(["pick:2028:2nd"]);
    expect(assetExplorerRows(rows, "rookie review", "All", "All").map((row) => row.assetId)).toEqual(["rookie:love"]);
  });

  it("filters source type and evidence state without dropping blocked assets by default", () => {
    expect(assetExplorerRows(rows, "", "Rookie Review", "All").map((row) => row.assetId)).toEqual(["rookie:love"]);
    expect(assetExplorerRows(rows, "", "All", "Blocked").map((row) => row.assetId)).toEqual(["pick:2028:2nd"]);
    expect(assetExplorerRows(rows, "", "All", "All")).toHaveLength(3);
  });
});
