# NWR PDF Free Agent Pool Integration - 2026-06-22

## Verdict

GREEN with YELLOW data caveats.

`C:\Users\codex-agent\Downloads\LVE Rosters 061326.pdf` page 3 was parsed as the verified league Free Agents source for this draft. The parsed players are integrated into the Live Draft Room and Player Compare as a draftable overlay only. This does not mutate Frozen Final Draft Board V1, Final Board Rank, Dynasty Rank, latest_candidate, latest_approved, or the pinned snapshot.

## Source

- Source PDF: `C:\Users\codex-agent\Downloads\LVE Rosters 061326.pdf`
- Parsed page: page 3
- Source section: `Free Agents`
- Raw extract: `docs/hq/parallel_lanes/overnight_accuracy_max_20260622/free_agent_pdf_page3_raw_extract.csv`
- Cleaned pool: `docs/hq/parallel_lanes/overnight_accuracy_max_20260622/free_agent_pdf_page3_draftable_pool.csv`

## Counts

- Free-agent rows extracted: 77
- Included by default: 63 QB/RB/WR/TE
- Hidden by default: 14 K/DST
- Frozen board rows remain unchanged: 66
- Expanded loaded pool rows: 143

## Key Player Parse Proof

The cleaned pool includes Tyreek Hill, Dallas Goedert, Juwan Johnson, Tua Tagovailoa, Jaylen Wright, Isaac Guerendo, Darnell Mooney, Rashod Bateman, Bryce Young, Anthony Richardson, Austin Ekeler, Marquise Brown, Cedric Tillman, Jerome Ford, Justice Hill, Ben Sinnott, Michael Mayer, Geno Smith, Marcus Mariota, Mac Jones, and Noah Gray.

## App Integration

Live Draft Room now loads Frozen Final Draft Board V1 plus the PDF page-3 free-agent overlay. PDF-only free agents show `Not on frozen board` for Final Board Rank and `PDF Free Agent / Draftable` as Source. K/DST rows remain in the parsed audit but are hidden by default in the app. The Live Draft Room includes toggles for `Show PDF free agents` and `Show K/DST`.

Player Compare now uses the same expanded draftable pool so PDF free agents can be selected. Missing candidate/model fields display as `Not enough information`.

## Validation Proof

- Focused pytest: 34 passed.
- Ruff on touched app/service/test files: PASS.
- `git diff --check`: PASS.
- Browser smoke: `/live-draft-room`, `/rankings`, `/player-compare`, `/mock-draft`, and `/trading-lab` opened with no page-not-found dialog.
- Live Draft Room browser proof: source caption showed `Frozen rows: 66`, `PDF FAs: 77`, `Draftable rows: 143`; `Show PDF free agents` was checked; `Show K/DST` was unchecked; ADP display-only warning was visible.
- Pick workflow browser proof: assigning the selected player to 1.01 changed Drafted from 0 to 1 and advanced Current pick to 1.02; Undo restored Drafted to 0 and Current pick to 1.01.
- PDF free-agent workflow proof: service-level assignment using the same Live Draft Room workflow functions assigned Tyreek Hill to 1.01, advanced the current pick to 2, hid Tyreek from available rows, and Undo restored him.

## ADP / Price Context

Sleeper ADP remains display-only and YELLOW source-risk. The app recalculates available-pool ADP rank/range over the expanded draftable pool where display-only ADP exists. PDF overall rank and PDF position rank are retained only as audit/display source context and are not used as model inputs.

## Candidate Model Impact

No source-truth rank was changed. PDF free agents receive candidate values only where an internal full-dynasty or tuned-candidate value exists. If no internal value is available, Candidate Value and Candidate Rank show `Not enough information`, while the player remains draftable/selectable.

## Remaining Caveats

- Most PDF-only free agents did not match the approved 240-row full dynasty board or the current Tuned V2 66-row overlay.
- ADP is display-only candidate context from a YELLOW undocumented Sleeper endpoint.
- The PDF team field is preserved as extracted; conflicting current team metadata is not silently substituted.
- This is a draftable overlay, not a Frozen Final Draft Board V1 mutation.
