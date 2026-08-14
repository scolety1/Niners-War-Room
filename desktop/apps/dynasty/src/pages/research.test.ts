import type { PlayerDetail } from "@nwr/contracts";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { PlayerDetailBody } from "./research";

const veteran: PlayerDetail = {
  assetId: "current:veteran",
  name: "Veteran Player",
  assetType: "Current Player",
  position: "WR",
  team: "SF",
  rank: null,
  positionRank: "WR1",
  nwrScore: 88.5,
  age: 25.4,
  confidence: "High",
  authority: "Finished V1",
  range: { floor: "WR18", expected: "WR10", ceiling: "WR4", method: "Model", authority: "Finished V1" },
  market: { band: "Hold", gap: null, rank: null, value: null, sourceAsOf: "", status: "" },
  risk: "Stable",
  reasons: [],
  outcomes: [],
  research: {},
  caveats: [],
  playerId: "veteran",
  identityStatus: "EXACT_GOVERNED_IDENTITY",
  officialDraftAssetId: "",
  nflDraftCapital: "",
  draftRound: null,
  overallPick: null,
  draftEligibility: "Not applicable",
  modelScoreEligible: true,
  scoreStatus: "Score available",
  selectable: true,
  refreshAvailable: false,
  rookieIntelligence: null,
};

function render(detail: PlayerDetail): string {
  return renderToStaticMarkup(
    createElement(PlayerDetailBody, {
      detail,
      onCompare: () => undefined,
      onPersonal: () => undefined,
      onTrade: () => undefined,
    }),
  );
}

describe("PlayerDetailBody", () => {
  it("preserves veteran Age and Confidence instead of rookie draft fields", () => {
    const html = render(veteran);

    expect(html).toContain("Age");
    expect(html).toContain("Confidence");
    expect(html).toContain("Lifecycle context");
    expect(html).toContain("Finished V1 authority");
    expect(html).toContain("Market read");
    expect(html).not.toContain("Manual Review");
    expect(html).not.toContain("NFL draft");
    expect(html).not.toContain("Draft status");
    expect(html).not.toContain("Draft &amp; identity");
  });

  it("shows Stribling's exact factual overlay without inventing a score", () => {
    const html = render({
      ...veteran,
      assetId: "blocked-rookie:dezhaun-stribling",
      name: "De'Zhaun Stribling",
      assetType: "Blocked Rookie",
      rank: null,
      nwrScore: null,
      authority: "UNSCORED_MANUAL_REVIEW",
      playerId: "00-0041035",
      officialDraftAssetId: "nflverse-draft:2026:33",
      nflDraftCapital: "NFL Round 2 - Pick 33",
      draftRound: 2,
      overallPick: 33,
      draftEligibility: "Draft eligible",
      modelScoreEligible: false,
      scoreStatus: "No admitted Rookie Review score - manual review required",
      refreshAvailable: true,
      rookieIntelligence: {
        nwrRookieScore: null,
        reviewScore: null,
        rawModelScore: null,
        collegeProduction: "Not enough information",
        marketShare: "Not enough information",
        athleticContext: "NOT_ENOUGH_INFORMATION",
        currentRole: "Active on SF's current roster; not used in Rookie Review score",
        whatNwrLikes: ["Official NFL selection: Round 2, pick 33"],
        whatHoldsBack: ["No admitted Rookie Review score"],
        biggestUncertainty: "Whether a governed rebuild can recover every required input",
        rankScoreExplanation: "No rank because the frozen Rookie Review did not admit a score",
      },
    });

    expect(html).toContain("Manual Review");
    expect(html).toContain("Unavailable");
    expect(html).toContain("NFL draft");
    expect(html).toContain("Draft status");
    expect(html).toContain("Draft &amp; identity");
    expect(html).toContain("00-0041035");
    expect(html).toContain("NFL Round 2 - Pick 33");
    expect(html).not.toContain("disabled=\"\"");
  });
});
