import { describe, expect, it } from "vitest";

import type { WaiverFaabContext } from "@nwr/contracts";
import { hasTrustworthyFaabBudget } from "./improve-team-explain";

function context(overrides: Partial<WaiverFaabContext> = {}): WaiverFaabContext {
  return {
    isFaabLeague: true,
    budgetMode: "LIVE",
    totalBudgetDollars: 100,
    remainingBudgetDollars: 63,
    weeksRemaining: 10,
    weeksRemainingSource: "LIVE",
    waiverPosition: 4,
    source: "SLEEPER_LIVE",
    scenario: null,
    ...overrides,
  };
}

describe("FAAB remaining-budget honesty", () => {
  it("rejects a FAAB context that knows the league type but not the real remaining balance", () => {
    expect(hasTrustworthyFaabBudget(context({ remainingBudgetDollars: null }))).toBe(false);
    expect(hasTrustworthyFaabBudget(context({ totalBudgetDollars: null }))).toBe(false);
    expect(hasTrustworthyFaabBudget(context({ weeksRemaining: null }))).toBe(false);
  });

  it("accepts a complete live balance without inventing a $100 fallback", () => {
    expect(hasTrustworthyFaabBudget(context({ totalBudgetDollars: 250, remainingBudgetDollars: 41 }))).toBe(true);
  });

  it("accepts only an explicitly echoed scenario when the response is scenario-priced", () => {
    expect(hasTrustworthyFaabBudget(context({ budgetMode: "SCENARIO", scenario: null }))).toBe(false);
    expect(hasTrustworthyFaabBudget(context({
      budgetMode: "SCENARIO",
      scenario: { remainingBudgetDollars: 20, totalBudgetDollars: 50, weeksRemaining: 4 },
      remainingBudgetDollars: 20,
      totalBudgetDollars: 50,
    }))).toBe(true);
    expect(hasTrustworthyFaabBudget(context({
      budgetMode: "SCENARIO",
      scenario: { remainingBudgetDollars: 20, totalBudgetDollars: 50, weeksRemaining: 4 },
      remainingBudgetDollars: null,
    }))).toBe(false);
  });
});
