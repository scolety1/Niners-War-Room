# Niners Roster Decision Trial Run

Audit artifact: `C:\Dev\niners-war-room\local_exports\niners_roster_decision_trial_run.csv`

## What Changed In This Pass

- Patched an action-label threshold issue in `command_board_service`: active stats-first keeper scores now use the post-projection-fix scale, so a player around 70+ keep priority with low cut risk can show as `keep` instead of being mislabeled as bubble.
- Patched a section-placement issue: rows labeled `bubble` now appear in Bubble Players instead of Bench/Stash when their cut risk/keep priority support bubble treatment.
- No player values or formula weights were changed. Rankings remain review-only.

## Roster Classifications

| player | class | model rec | keep | cut risk | model value | confidence | reason |
|---|---|---|---:|---:|---:|---:|---|
| Brian Thomas | likely hold | keep | 72.92 | 22.77 | 75.78 | 75.5 | receipts support current bucket |
| Luther Burden | forced-release candidate | shop/release | 38.69 | 49.9 | 50.23 | 36.0 | league-rank top-five rule plus lowest top-five keep priority; confidence issue |
| Jakobi Meyers | bubble | bubble | 63.2 | 33.78 | 65.5 | 77.5 | source gap: no independent projection; source gap: production freshness |
| De'Von Achane | bubble | bubble | 63.38 | 32.79 | 66.13 | 75.5 | source gap: no independent projection; source gap: production freshness; lifecycle: young bridge prior active |
| Jerry Jeudy | bubble | bubble | 62.38 | 32.39 | 64.33 | 77.5 | source gap: no independent projection; source gap: production freshness |
| Brandon Aiyuk | bubble | bubble | 64.83 | 28.57 | 67.2 | 77.5 | source gap: no independent projection; source gap: production freshness |
| Luke McCaffrey | shop | shop | 30.35 | 54.52 | 36.2 | 75.5 | source gap: no independent projection; source gap: production freshness; lifecycle: young bridge prior active; formula behavior: cut risk exceeds keep threshold |
| Ricky Pearsall | shop | shop | 42.41 | 54.51 | 49.84 | 75.5 | source gap: no independent projection; source gap: production freshness; lifecycle: young bridge prior active; formula behavior: cut risk exceeds keep threshold |
| Jalen Coker | shop | shop | 38.6 | 54.22 | 44.43 | 75.5 | source gap: no independent projection; source gap: production freshness; lifecycle: young bridge prior active; formula behavior: cut risk exceeds keep threshold |
| Jayden Higgins | shop | shop | 39.02 | 49.69 | 50.51 | 36.0 | confidence issue; lifecycle: young bridge prior active; formula behavior: cut risk exceeds keep threshold |
| Quentin Johnston | shop | shop | 43.97 | 48.23 | 50.49 | 75.5 | source gap: no independent projection; source gap: production freshness; lifecycle: young bridge prior active; formula behavior: cut risk exceeds keep threshold |
| Lamar Jackson | shop | shop | 41.54 | 46.62 | 54.68 | 77.5 | source gap: no independent projection; source gap: production freshness; formula behavior: cut risk exceeds keep threshold |
| David Montgomery | shop | shop | 51.09 | 45.84 | 53.88 | 77.5 | source gap: no independent projection; source gap: production freshness; formula behavior: cut risk exceeds keep threshold |
| Wan'Dale Robinson | shop | shop | 53.21 | 45.58 | 55.43 | 77.5 | source gap: no independent projection; source gap: production freshness; formula behavior: cut risk exceeds keep threshold |
| Romeo Doubs | shop | shop | 48.81 | 43.3 | 55.17 | 77.5 | source gap: no independent projection; source gap: production freshness; formula behavior: cut risk exceeds keep threshold |
| Kaleb Johnson | shop | shop | 54.43 | 42.99 | 58.43 | 36.0 | confidence issue; lifecycle: young bridge prior active; formula behavior: cut risk exceeds keep threshold |
| Chase Brown | shop | shop | 52.91 | 41.81 | 54.39 | 75.5 | source gap: no independent projection; source gap: production freshness; lifecycle: young bridge prior active; formula behavior: cut risk exceeds keep threshold |
| Xavier Worthy | shop | shop | 54.27 | 41.53 | 62.02 | 75.5 | source gap: no independent projection; source gap: production freshness; lifecycle: young bridge prior active; formula behavior: cut risk exceeds keep threshold |
| Devin Singletary | shop | shop | 52.76 | 40.85 | 53.47 | 77.5 | source gap: no independent projection; source gap: production freshness; formula behavior: cut risk exceeds keep threshold |
| Brenton Strange | cut/release candidate | drop | 16.11 | 66.12 | 27.51 | 75.5 | source gap: no independent projection; source gap: production freshness; lifecycle: young bridge prior active; formula behavior: cut risk exceeds keep threshold |
| Oronde Gadsden | cut/release candidate | drop | 11.62 | 65.19 | 26.26 | 38.5 | confidence issue; formula behavior: cut risk exceeds keep threshold |
| Daniel Jones | cut/release candidate | drop | 18.99 | 58.16 | 34.91 | 77.5 | source gap: no independent projection; source gap: production freshness; formula behavior: cut risk exceeds keep threshold |
| T.J. Hockenson | cut/release candidate | drop | 31.11 | 57.57 | 43.46 | 77.5 | source gap: no independent projection; source gap: production freshness; formula behavior: cut risk exceeds keep threshold |
| Jake Ferguson | cut/release candidate | drop | 26.8 | 56.86 | 38.34 | 77.5 | source gap: no independent projection; source gap: production freshness; formula behavior: cut risk exceeds keep threshold |

## Main Takeaways

- There are no ?obvious hold? labels I would call final because the app is still review-only and every active preview row is missing a true independent projection source.
- Brian Thomas is the cleanest likely hold on the current model: he has the highest Niners model value and low cut risk, with the young-player bridge and production/target drivers aligned.
- Luther Burden is the current forced-release candidate by rule-layer pain: he is in the league-rank top five and is the least painful top-five release, but his confidence is low, so the action should be reviewed rather than treated as final truth.
- De'Von Achane, Brandon Aiyuk, Jakobi Meyers, and Jerry Jeudy are now properly shown as bubble review rows rather than hidden in Bench/Stash.
- Lamar Jackson being a shop row is formula behavior, not an identity bug: 1QB/3-point passing TD suppression makes non-replacement advantage the key question.
- TE rows are heavily suppressed by no-TE-premium logic; Brenton Strange, Oronde Gadsden, Hockenson, and Ferguson remain cut/release candidates in this model until better role/projection evidence says otherwise.

## Remaining Trust Limits

- Independent projection/opportunity data is still missing; local baseline projections are now explicitly neutralized.
- Production freshness is still a review gap because player stats lag newer role/injury/depth sources.
- Low-confidence young players such as Luther Burden, Jayden Higgins, Kaleb Johnson, and Oronde Gadsden need receipt review before real decisions.
