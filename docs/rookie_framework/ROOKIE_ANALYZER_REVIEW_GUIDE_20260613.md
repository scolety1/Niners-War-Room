# Rookie Analyzer Review Guide - 2026-06-13

## Review Flow

Use the analyzer from highest-leverage decisions to lowest-leverage decisions:

1. Confirm `1.03` remains trade-down/manual-review only.
2. Review `1.04` premium rows and their visible warnings.
3. Review Round 2 RB/WR rows and survival/evidence questions.
4. Review 5.04 dart/stash rows.
5. Ignore blocked and unavailable rows unless new source-safe evidence arrives.

## Premium Review

For `1.04`, focus on:

- unresolved injury notes;
- route/separation/press/YAC concerns;
- target-earning and first-down evidence;
- RB pass protection, contact, fumble, and goal-line context;
- source-limited or quarantined warning context.

Draft only if the `draft_only_if` condition is true and warnings are acceptable.

Do not draft if the `do_not_draft_if` condition is true.

## Round 2 Review

Round 2 rows are not clean ready. Use them to ask:

- Does the RB have enough survival evidence?
- Does the WR have enough role and target-earning evidence?
- Is any TE/QB exception actually supported?
- Are the remaining gaps acceptable at the pick?

If a row is `manual_review_required`, hold it until Tim answers the named question.

## 5.04 Review

At 5.04, prefer:

- asymmetric darts;
- clear role-path stashes;
- source-limited profiles with a specific upside case;
- falling players whose warnings are understood.

Avoid:

- generic low-upside profiles;
- profiles with no role path;
- blocked rows;
- unavailable rows;
- TE/QB exceptions without a clear usage path.

## Emergency Stop Rules

Stop if:

- `emergency_stop_signal` starts with `yes`;
- injury review is unresolved;
- the row depends only on soft secondary charting;
- a source conflict affects the production case;
- warnings would need to be hidden;
- `1.03` would need to be forced open;
- market/rank/projection/trade context would be needed to justify the pick.

## What The Analyzer Cannot Do

The analyzer cannot:

- approve production implementation;
- replace production rankings;
- create private scores;
- create probabilities;
- create bands;
- wire app or Streamlit display;
- use veteran outcome heads;
- clear source conflicts automatically;
- remove manual-review flags without Tim's review.

## Recommended Use

Use the analyzer as a checklist and context surface. Treat it as a structured way to ask better draft questions, not as a final answer machine.
