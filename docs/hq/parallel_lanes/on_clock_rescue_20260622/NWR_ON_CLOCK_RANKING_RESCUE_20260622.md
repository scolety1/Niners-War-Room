# NWR On-Clock Ranking Rescue - 2026-06-22

## Verdict

YELLOW-GREEN: app-facing rescue is safe and draft-useful, but the on-clock layer remains review-only because it is an emergency calibration, not an approved model promotion.

## Root Cause

The prior Live Draft default sorted by Tuned V2 Candidate Rank. That layer improved rookie-veteran comparison, but it still over-discounted elite young QBs in 10-team 1QB and did not make PDF free-agent status/injury/age risk loud enough for Tyreek Hill.

## Drake Maye

Drake Maye was candidate rank 21 because the Tuned V2 layer applied a harsh 10-team 1QB discount to a candidate value of 30.48. The rescue layer keeps the 1QB warning but promotes him to the top decision tier as an elite-young-QB exception.

## Tyreek Hill

Tyreek Hill was candidate rank 13 because the PDF free-agent overlay had a review-only internal value, but his low-confidence PDF/free-agent/current-status risk was not loud enough. The rescue layer demotes him to discount-only and shows a loud warning.

## ADP

ADP remains display-only. The app label now says Startup ADP / Display-Only and adds a Draft Timing Note that it is a weak timing signal for this rookie/free-agent draft.

## Web Sanity Sources Used

- Drake Maye: Patriots profile confirms first-round draft status and 2025 starting workload; NFL profile/news flags his shoulder as not expected to be an issue.
- Chris Olave: ESPN/Pro Football Reference production pages support treating him as a proven young WR anchor.
- Jameson Williams: ESPN profile and public stat pages support keeping him review-visible as an explosive young NFL WR.
- Tyreek Hill: ESPN reporting flags major knee surgery/recovery and release/free-agent uncertainty, supporting a discount-only warning.

These sources were used only as factual sanity checks, not as ranking inputs.

Reference URLs:

- https://www.patriots.com/team/players-roster/drake-maye/
- https://www.nfl.com/players/drake-maye/
- https://www.espn.com/nfl/player/stats/_/id/4361370/chris-olave
- https://www.pro-football-reference.com/players/O/OlavCh00.htm
- https://www.espn.com/nfl/player/_/id/4426388/jameson-williams
- https://www.espn.com/nfl/story/_/id/46703839/dolphins-tyreek-hill-undecided-retirement-injury
- https://www.espn.com/nfl/story/_/id/47948025/miami-dolphins-cut-tyreek-hill-answering-biggest-questions-injury-whats-next

## Files

- `current_bad_output_diagnostic.csv`
- `ON_CLOCK_DRAFT_DECISION_CHEAT_SHEET_20260622.md`
