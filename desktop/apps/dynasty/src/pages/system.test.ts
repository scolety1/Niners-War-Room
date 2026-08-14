import type { DynastyBootstrap } from "@nwr/contracts";
import { describe, expect, it } from "vitest";

import { draftCockpitRookieRows } from "./system";

function fixture(): Pick<DynastyBootstrap, "rookies" | "rookieReadiness"> {
  const rookies = Array.from({ length: 80 }, (_, index) => ({
    assetId: index === 79 ? "blocked-rookie:dezhaun-stribling" : `rookie:${index}`,
    player: index === 79 ? "De'Zhaun Stribling" : `Rookie ${index}`,
    rank: index === 79 ? null : index + 1,
    reviewScore: index === 79 ? null : 80 - index,
    draftable: true,
    selectable: true,
  })) as DynastyBootstrap["rookies"];
  return {
    rookies,
    rookieReadiness: {
      draftableAssetIds: rookies.map((row) => row.assetId),
    } as DynastyBootstrap["rookieReadiness"],
  };
}

describe("draftCockpitRookieRows", () => {
  it("uses the reconciled 80-asset pool and retains Stribling as unscored", () => {
    const rows = draftCockpitRookieRows(fixture());
    const stribling = rows.find((row) => row.assetId === "blocked-rookie:dezhaun-stribling");

    expect(rows).toHaveLength(80);
    expect(stribling?.rank).toBeNull();
    expect(stribling?.reviewScore).toBeNull();
  });

  it("does not silently re-add an asset rejected by the readiness gate", () => {
    const data = fixture();
    data.rookieReadiness.draftableAssetIds = data.rookieReadiness.draftableAssetIds.filter(
      (assetId) => assetId !== "blocked-rookie:dezhaun-stribling",
    );

    expect(draftCockpitRookieRows(data)).toHaveLength(79);
  });
});
