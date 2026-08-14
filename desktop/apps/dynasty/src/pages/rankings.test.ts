import { describe, expect, it } from "vitest";
import type { AssetOption } from "@nwr/contracts";
import { assetExplorerRows } from "./rankings";

const rows: AssetOption[] = [
  { assetId: "player:puka", name: "Puka Nacua", assetType: "Current Player", position: "WR", team: "LAR", rank: 1, authority: "Finished V1", blocked: false, selectable: true, searchable: true, draftEligible: false, modelScoreEligible: true, evidenceBlocked: false, scoreStatus: "Score available", identityStatus: "Exact governed identity", playerId: "puka", draftRound: null, overallPick: null, refreshAvailable: false },
  { assetId: "rookie:love", name: "Jeremiyah Love", assetType: "Rookie Review", position: "RB", team: "ARI", rank: 1, authority: "2026 Rookie Review", blocked: false, selectable: true, searchable: true, draftEligible: true, modelScoreEligible: true, evidenceBlocked: false, scoreStatus: "Rookie Review score available", identityStatus: "Exact governed identity", playerId: "love", draftRound: 1, overallPick: 1, refreshAvailable: false },
  { assetId: "blocked-rookie:dezhaun-stribling", name: "De'Zhaun Stribling", assetType: "Blocked Rookie", position: "WR", team: "SF", rank: null, authority: "UNSCORED_MANUAL_REVIEW", blocked: false, selectable: true, searchable: true, draftEligible: true, modelScoreEligible: false, evidenceBlocked: true, scoreStatus: "No admitted Rookie Review score — manual review required", identityStatus: "EXACT_GOVERNED_IDENTITY", playerId: "00-0041035", draftRound: 2, overallPick: 33, refreshAvailable: true },
  { assetId: "pick:2028:2nd", name: "2028 2nd", assetType: "Future Pick", position: "PICK", team: "Owner not encoded", rank: null, authority: "Governed future-pick structure", blocked: false, selectable: true, searchable: true, draftEligible: false, modelScoreEligible: false, evidenceBlocked: false, scoreStatus: "No common model score", identityStatus: "", playerId: "", draftRound: null, overallPick: null, refreshAvailable: false },
];

describe("assetExplorerRows", () => {
  it("searches across the full governed registry", () => {
    expect(assetExplorerRows(rows, "2028", "All", "All").map((row) => row.assetId)).toEqual(["pick:2028:2nd"]);
    expect(assetExplorerRows(rows, "rookie review", "All", "All").map((row) => row.assetId)).toEqual(["rookie:love", "blocked-rookie:dezhaun-stribling"]);
    expect(assetExplorerRows(rows, "Dezhaun", "All", "All").map((row) => row.assetId)).toEqual(["blocked-rookie:dezhaun-stribling"]);
    expect(assetExplorerRows(rows, "Stribling", "All", "All").map((row) => row.assetId)).toEqual(["blocked-rookie:dezhaun-stribling"]);
  });

  it("filters source type and evidence state without dropping blocked assets by default", () => {
    expect(assetExplorerRows(rows, "", "Rookie Review", "All").map((row) => row.assetId)).toEqual(["rookie:love"]);
    expect(assetExplorerRows(rows, "", "All", "Manual review").map((row) => row.assetId)).toEqual(["blocked-rookie:dezhaun-stribling"]);
    expect(assetExplorerRows(rows, "", "All", "All")).toHaveLength(4);
  });
});
