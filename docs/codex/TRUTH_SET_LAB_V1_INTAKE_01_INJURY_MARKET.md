# Project Gold Truth Set Lab v1 Intake 01: Injury + Market

Generated: 2026-05-14

## Source Files

- Raw injury file: `local_exports/truth_set_lab/v1/source_raw/injury_truth_set.csv`
- Clean injury preview: `local_exports/truth_set_lab/v1/source_clean/injury.csv`
- Raw trade liquidity file: `local_exports/truth_set_lab/v1/source_raw/trade_liquidity.csv`
- Clean trade liquidity preview: `local_exports/truth_set_lab/v1/source_clean/trade_liquidity.csv`
- Intake summary: `local_exports/truth_set_lab/v1/reports/intake_summary.csv`
- Intake flags: `local_exports/truth_set_lab/v1/reports/intake_flags.csv`

## Intake Summary

| category | rows | missing truth-set players | populated evidence rows | source URL missing | status |
|---|---:|---:|---:|---:|---|
| injury | 40 | 0 | 7 | 33 | incomplete |
| trade_liquidity | 40 | 0 | 5 | 35 | ready for review |

## Findings

- Both files cover all 40 truth-set players.
- The injury file has one malformed CSV row: Justin Jefferson has an extra unparsed field,
  likely from an unquoted comma or URL fragment in notes.
- The injury file has 33 healthy/active rows without source URLs. These are weak context
  only and must not increase model confidence.
- The injury file has 7 sourced injury rows worth reviewing first: T.J. Hockenson,
  Daniel Jones, De'Von Achane, Justin Jefferson, Ja'Marr Chase, Malik Nabers, and
  Kyren Williams.
- The trade liquidity file has only 5 populated market rows: Xavier Worthy,
  Brian Thomas Jr., Ricky Pearsall, Justin Jefferson, and Ja'Marr Chase.
- The 35 blank market rows should leave market edge blank/untrusted for those players.

## Model Use Decision

Do not promote either file into scoring yet.

Use the injury rows as preview evidence only after the malformed Justin Jefferson row is
fixed and unsourced healthy rows are treated as no-evidence, not positive evidence.

Use the trade liquidity rows only as partial market context. The market layer remains
incomplete until most or all 40 truth-set players have comparable market values from the
same source/date/format.
