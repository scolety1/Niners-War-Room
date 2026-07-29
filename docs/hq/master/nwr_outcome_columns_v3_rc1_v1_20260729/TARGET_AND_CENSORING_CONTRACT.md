# Target and censoring contract

For anchor season `t`, the exact target windows are:

- This Year: `t`
- Next Year: `t+1`
- T+2: `t+2`
- Within 3 Years: at least one hit in `t..t+2`
- Within 5 Years: at least one hit in `t..t+4`
- Two Qualifying Seasons Within 3 Years: at least two hits in `t..t+2`

A missing player-season row is unknown, never an automatic miss. Exact-year
negative requires an observed nonqualifying result or explicit terminal
authority. Cumulative positive can resolve before the horizon closes;
cumulative negative requires a complete horizon or terminal authority.
Post-2025 seasons are right-censored.

The admitted Formula Data Mart anchors target season `t` to features from
`t-1`; all 108,852 target rows preserve that offset. The
manifest contains 63,501 field-level labeled
rows. Eleven age-sidecar rows fail their own age/identity admission flags and
therefore retain unknown cohort evidence; their exact-ID Outcome labels are not
discarded or rewritten.
