# HQ1 Rebuild And Replay Checklist

Use this checklist before claiming that a source, metric, board, formula, ranking, or evidence packet can be rebuilt or replayed.

## Required Inputs

- [ ] Raw source files or frozen source extracts exist.
- [ ] Every raw file has a hash.
- [ ] Every raw file has an acquisition timestamp.
- [ ] Every raw file has source URL/path and acquisition method.
- [ ] Every raw file has row count, column count, and schema recorded.
- [ ] Source version/date is recorded when available.
- [ ] Licensing/use status is recorded.
- [ ] Source status and admission status are recorded.

## Identity And Joins

- [ ] Canonical player identity key is present or mapped.
- [ ] Join keys are documented.
- [ ] Join method is documented.
- [ ] Name-only joins are not treated as approved joins.
- [ ] Collision rows are flagged.
- [ ] Unmatched rows are flagged.
- [ ] Manual review rows are separated from approved joins.
- [ ] Row grain is stable before and after joins.

## Coverage And Missingness

- [ ] Seasons, weeks, teams, positions, and player universes are recorded.
- [ ] Missing rows are counted.
- [ ] Missing fields are counted.
- [ ] Missingness reason is recorded where known.
- [ ] Coverage bias is documented.
- [ ] Thresholds and eligibility filters are documented.
- [ ] Silent zero-fill is not used unless explicitly justified and flagged.

## Transformation And Outputs

- [ ] Transformation steps are documented.
- [ ] Script or command path is recorded if a script is used.
- [ ] Parameters and configuration are recorded.
- [ ] Intermediate output hashes are recorded when practical.
- [ ] Final output hash is recorded.
- [ ] Output row count and schema are recorded.
- [ ] Validation tests are listed.
- [ ] Known blockers are listed.

## Replay Safety

- [ ] Decision-date contract is written.
- [ ] As-of availability is proven or caveated.
- [ ] Current-only data is excluded from historical features.
- [ ] Outcome labels are held out and never used as inputs.
- [ ] Market/ADP/projection/rank/display-only fields are excluded unless explicitly admitted for a defined role.
- [ ] Exact replay is distinguished from partial proxy replay.

## Verdict

Choose one:

- `REBUILD_READY`: All required receipts exist and validation passes.
- `REBUILD_READY_REVIEW_ONLY`: Rebuild can run, but output remains review-only.
- `PARTIAL_REBUILD_WITH_CAVEATS`: Some receipts are missing; blockers are documented.
- `EXACT_REPLAY_BLOCKED`: Upstream receipts or decision-date inputs are missing.
- `NOT_ENOUGH_INFORMATION`: Evidence is insufficient to classify.
