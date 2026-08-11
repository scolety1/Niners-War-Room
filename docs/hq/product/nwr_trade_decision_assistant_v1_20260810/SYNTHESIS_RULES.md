# Synthesis Rules

Synthesis counts named ordinal dimension directions. It never sums ranks, scores, DP values,
rookie ranks, or picks.

- Inadequate coverage or predominantly blocked evidence returns `INSUFFICIENT_EVIDENCE`.
- Opposing strong dimensions return `COUNTER` or `TOO_CLOSE`.
- Clear multi-dimensional agreement with limited contradiction can produce an accept/reject
  state.
- A preferred side is reported separately from action and confidence.
- The trace lists which named dimensions support each side and explicitly states that no
  package score is used.

Market DP totals exist only in the separate negotiation adapter and cannot enter synthesis.

