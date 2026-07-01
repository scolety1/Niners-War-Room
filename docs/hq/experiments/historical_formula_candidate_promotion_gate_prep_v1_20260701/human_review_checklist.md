# Human Review Checklist

- [ ] Inspect all severe regression rows with `error_delta > 20`.
- [ ] Inspect elite-QB regression rows.
- [ ] Decide whether bucket/cutline movement is acceptable.
- [ ] Decide whether MAE improvement is worth possible Top-N tradeoffs.
- [ ] Confirm the formula remains interpretable.
- [ ] Confirm no candidate output should be consumed by NWR runtime.
- [ ] Choose one next action: shadow-review prep, more evidence, or reject.
