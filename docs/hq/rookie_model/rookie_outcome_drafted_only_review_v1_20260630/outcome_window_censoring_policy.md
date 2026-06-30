# Outcome Window Censoring Policy

- Rookie-year labels cover the player's draft/rookie class season only.
- 2Y labels cover rookie year plus one NFL season.
- 3Y labels require the rookie season through rookie year plus two seasons.
- 5Y labels require the rookie season through rookie year plus four seasons.
- Incomplete or future windows are right-censored and are not failures.
- Missing labels stay `Not enough information`, never `0%`.

Outcome V2 label coverage used here spans 2012-2024, so drafted-player rows
before 2012 are outside available label coverage in this packet. Recent classes
can have incomplete 3Y/5Y windows because the seasons have not happened yet.

Future NFL production after the prediction window cannot be used as an input
feature because it would leak the target. Current rookies and prospects are
not historical training rows; they can only receive review-only status/coverage
language until a later explicit release gate approves app-facing display.
