import { describe, expect, it } from "vitest";

import { ownerDisplay, ownerFieldLabel, ownerLabel } from "./owner-copy";

describe("Dynasty owner copy", () => {
  it("translates governed confidence states without changing their meaning", () => {
    expect(ownerLabel("capped_review_required")).toBe("Review capped");
    expect(ownerLabel("usable_with_confidence_cap")).toBe("Usable · capped");
    expect(ownerLabel("REVIEW_ONLY_SOURCE_LIMITED")).toBe("Review only · limited source");
  });

  it("suppresses uninformative unassigned values", () => {
    expect(ownerDisplay("Unassigned")).toMatchObject({ label: "—" });
    expect(ownerLabel(null)).toBe("—");
  });

  it("explains frozen research neighborhoods as non-authoritative bands", () => {
    expect(ownerDisplay("Research neighborhood 1")).toEqual({
      label: "Top research band",
      title: "Frozen research grouping only; it does not change NWR rank or trade authority.",
    });
    expect(ownerLabel("RESEARCH_TIER_5")).toBe("Deep research band");
  });

  it("humanizes unknown machine tokens but preserves normal prose", () => {
    expect(ownerLabel("first_round_board_context_review")).toBe("First round board context review");
    expect(ownerLabel("This is already owner copy.")).toBe("This is already owner copy.");
    expect(ownerFieldLabel("nfl_draft_capital")).toBe("NFL draft capital");
  });
});
