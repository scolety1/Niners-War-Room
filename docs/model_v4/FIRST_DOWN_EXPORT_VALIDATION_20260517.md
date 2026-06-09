# First-Down Export Validation - 2026-05-17

This report validates the manually collected rushing/receiving first-down CSV exports before Model v4 can use them as direct evidence.

## Summary

| Season | Type | Clean Rows | Total 1D | Status | Warnings |
|---:|---|---:|---:|---|---|
| 2024 | receiving | 275 | 5777 | usable_after_cleanup | repeated_header_lines=1;basic_stat_mismatches_vs_rotowire_existing=14;not_found_in_existing_rotowire_basic=4 |
| 2025 | receiving | 300 | 4595 | usable_after_cleanup | exact_duplicate_rows_removed=50;basic_stat_mismatches_vs_rotowire_existing=21;not_found_in_existing_rotowire_basic=6 |
| 2024 | rushing | 125 | 3329 | usable_after_header_inference | missing_header_in_raw_export_expected_header_inferred;basic_stat_mismatches_vs_rotowire_existing=2;not_found_in_existing_rotowire_basic=2 |
| 2025 | rushing | 225 | 3619 | usable_after_cleanup | basic_stat_mismatches_vs_rotowire_existing=8;not_found_in_existing_rotowire_basic=5 |

## Findings

- The files contain direct rushing/receiving first-down fields and are useful for replacing current estimated first-down evidence after intake mapping.
- Raw exports were preserved under `local_exports/model_v4/raw_user_exports/rotowire_manual/<season>/first_downs/`.
- These files do not include team or position, so the intake must join by normalized player name against existing RotoWire season stat identity and flag ambiguous names.
- `Rushing - 2024.csv` has no header row. The expected rushing header can be inferred, but the raw file should remain unchanged.
- `Receiving - 2024.csv` has one repeated header row inside the body.
- `Receiving - 2025.csv` has exact duplicate rows caused by the source page/export behavior; exact duplicates can be removed safely during processing.

## 2024 Receiving

- Header present: `True`
- Repeated header lines: `1`
- Exact duplicate rows removed: `0`
- Duplicate player rows with different stats: `0`
- Numeric issues: `0`
- Existing RotoWire basic comparison: checked `271`, missing `4`, mismatches `14`
- Mismatch examples: Davante Adams (Rec:85.0 vs REC:18.0; Yds:1063.0 vs YDS:209.0; TD:8.0 vs TD:1.0; Tgts:141.0 vs TAR:27.0); Elijah Moore (Tgts:102.0 vs TAR:101.0); DeAndre Hopkins (Rec:56.0 vs REC:15.0; Yds:610.0 vs YDS:173.0; TD:5.0 vs TD:1.0; Tgts:80.0 vs TAR:21.0); Jahmyr Gibbs (Yds:517.0 vs YDS:497.0; TD:4.0 vs TD:3.0; 20+:6.0 vs 20+:5.0); Amari Cooper (Rec:44.0 vs REC:24.0; Yds:547.0 vs YDS:250.0; TD:4.0 vs TD:2.0; Tgts:85.0 vs TAR:53.0); Zach Charbonnet (Yds:340.0 vs YDS:308.0; 20+:4.0 vs 20+:3.0); Darius Slayton (Tgts:71.0 vs TAR:70.0); Diontae Johnson (Rec:33.0 vs REC:1.0; Yds:375.0 vs YDS:6.0; TD:3.0 vs TD:0.0; Tgts:67.0 vs TAR:5.0)
- Missing examples: Kenneth Walker III; Josh Palmer; Calvin Austin III; John Metchie III

Top first-down rows after cleanup:

| Player | First Downs | Volume | Yards | TD |
|---|---:|---:|---:|---:|
| Ja'Marr Chase | 75 | 175 targets / 127 rec | 1708 | 17 |
| Amon-Ra St. Brown | 71 | 141 targets / 115 rec | 1263 | 12 |
| Drake London | 67 | 158 targets / 100 rec | 1271 | 9 |
| Trey McBride | 63 | 147 targets / 111 rec | 1146 | 2 |
| Justin Jefferson | 62 | 154 targets / 103 rec | 1533 | 10 |
| Brock Bowers | 61 | 153 targets / 112 rec | 1194 | 5 |
| Garrett Wilson | 60 | 154 targets / 101 rec | 1104 | 7 |
| Jerry Jeudy | 57 | 145 targets / 90 rec | 1229 | 4 |
| Courtland Sutton | 57 | 135 targets / 81 rec | 1081 | 8 |
| Terry McLaurin | 56 | 117 targets / 82 rec | 1096 | 13 |

## 2025 Receiving

- Header present: `True`
- Repeated header lines: `0`
- Exact duplicate rows removed: `50`
- Duplicate player rows with different stats: `0`
- Numeric issues: `0`
- Existing RotoWire basic comparison: checked `294`, missing `6`, mismatches `21`
- Mismatch examples: Jaxon Smith-Njigba (Tgts:163.0 vs TAR:162.0); Chris Olave (Tgts:156.0 vs TAR:155.0); Juwan Johnson (Tgts:102.0 vs TAR:103.0); Jakobi Meyers (Rec:75.0 vs REC:33.0; Yds:835.0 vs YDS:352.0; TD:3.0 vs TD:0.0; Tgts:110.0 vs TAR:49.0); Jameson Williams (Tgts:102.0 vs TAR:100.0); Rashid Shaheed (Rec:59.0 vs REC:15.0; Yds:687.0 vs YDS:188.0; TD:2.0 vs TD:0.0; Tgts:92.0 vs TAR:26.0); Adonai Mitchell (Rec:33.0 vs REC:9.0; Yds:453.0 vs YDS:152.0; TD:2.0 vs TD:0.0; Tgts:74.0 vs TAR:16.0); Tyler Lockett (Rec:32.0 vs REC:10.0; Yds:291.0 vs YDS:70.0; TD:1.0 vs TD:0.0; Tgts:55.0 vs TAR:21.0)
- Missing examples: John Metchie III; Calvin Austin III; Kenneth Walker III; Josh Palmer; Audric Estimé; Scott Miller

Top first-down rows after cleanup:

| Player | First Downs | Volume | Yards | TD |
|---|---:|---:|---:|---:|
| Puka Nacua | 80 | 166 targets / 129 rec | 1715 | 10 |
| Jaxon Smith-Njigba | 79 | 163 targets / 119 rec | 1793 | 10 |
| Ja'Marr Chase | 73 | 185 targets / 125 rec | 1412 | 8 |
| George Pickens | 73 | 137 targets / 93 rec | 1429 | 9 |
| Amon-Ra St. Brown | 71 | 172 targets / 117 rec | 1401 | 11 |
| Trey McBride | 63 | 169 targets / 126 rec | 1239 | 11 |
| Tetairoa McMillan | 55 | 122 targets / 70 rec | 1014 | 7 |
| Chris Olave | 53 | 156 targets / 100 rec | 1163 | 9 |
| Courtland Sutton | 52 | 124 targets / 74 rec | 1017 | 7 |
| Kyle Pitts | 51 | 118 targets / 88 rec | 928 | 5 |

## 2024 Rushing

- Header present: `False`
- Repeated header lines: `0`
- Exact duplicate rows removed: `0`
- Duplicate player rows with different stats: `0`
- Numeric issues: `0`
- Existing RotoWire basic comparison: checked `123`, missing `2`, mismatches `2`
- Mismatch examples: Cam Akers (Att:104.0 vs ATT:40.0; Rush Yds:444.0 vs YDS:147.0; TD:2.0 vs TD:1.0; 20+:2.0 vs 20+:0.0); Khalil Herbert (Att:36.0 vs ATT:8.0; Rush Yds:130.0 vs YDS:16.0)
- Missing examples: Kenneth Walker III; Audric Estimé

Top first-down rows after cleanup:

| Player | First Downs | Volume | Yards | TD |
|---|---:|---:|---:|---:|
| Derrick Henry | 93 | 325 att | 1921 | 16 |
| Kyren Williams | 85 | 316 att | 1299 | 14 |
| Saquon Barkley | 82 | 345 att | 2005 | 13 |
| Bijan Robinson | 82 | 304 att | 1456 | 14 |
| Josh Jacobs | 73 | 301 att | 1329 | 15 |
| Jonathan Taylor | 71 | 303 att | 1431 | 11 |
| Jahmyr Gibbs | 70 | 250 att | 1412 | 16 |
| James Conner | 66 | 236 att | 1094 | 8 |
| Chuba Hubbard | 62 | 250 att | 1195 | 10 |
| Jalen Hurts | 62 | 150 att | 630 | 14 |

## 2025 Rushing

- Header present: `True`
- Repeated header lines: `0`
- Exact duplicate rows removed: `0`
- Duplicate player rows with different stats: `0`
- Numeric issues: `0`
- Existing RotoWire basic comparison: checked `220`, missing `5`, mismatches `8`
- Mismatch examples: Tank Bigsby (Att:63.0 vs ATT:5.0; Rush Yds:356.0 vs YDS:12.0; TD:2.0 vs TD:0.0; 20+:2.0 vs 20+:0.0); Rashid Shaheed (Att:9.0 vs ATT:2.0; Rush Yds:69.0 vs YDS:5.0; 20+:1.0 vs 20+:0.0); Dameon Pierce (Att:14.0 vs ATT:4.0; Rush Yds:36.0 vs YDS:10.0); Trayveon Williams (Att:10.0 vs ATT:3.0; Rush Yds:36.0 vs YDS:-1.0); Joe Flacco (Att:21.0 vs ATT:6.0; Rush Yds:35.0 vs YDS:13.0; TD:1.0 vs TD:0.0); D'Ernest Johnson (Att:14.0 vs ATT:1.0; Rush Yds:25.0 vs YDS:0.0); Tez Johnson (Att:7.0 vs ATT:8.0; Rush Yds:22.0 vs YDS:24.0); DeeJay Dallas (Att:3.0 vs ATT:1.0; Rush Yds:21.0 vs YDS:0.0)
- Missing examples: Kenneth Walker III; Audric Estimé; Nate Carter; Joe Milton III; Luther Burden III

Top first-down rows after cleanup:

| Player | First Downs | Volume | Yards | TD |
|---|---:|---:|---:|---:|
| Jonathan Taylor | 84 | 323 att | 1585 | 18 |
| Derrick Henry | 79 | 307 att | 1595 | 16 |
| Kyren Williams | 74 | 259 att | 1252 | 10 |
| Christian McCaffrey | 70 | 311 att | 1202 | 10 |
| James Cook | 68 | 309 att | 1621 | 12 |
| Javonte Williams | 67 | 252 att | 1201 | 11 |
| Bijan Robinson | 63 | 287 att | 1478 | 7 |
| D'Andre Swift | 62 | 223 att | 1087 | 9 |
| Breece Hall | 57 | 243 att | 1065 | 4 |
| De'Von Achane | 56 | 238 att | 1350 | 8 |
