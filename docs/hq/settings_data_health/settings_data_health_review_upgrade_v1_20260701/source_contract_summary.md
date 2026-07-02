# Source Contract Summary

Current merged Source Contract V1 remains the controlling review-only feature boundary:

- Allowed review-only features: `18`
- Null-fenced optional features: `4`
- Blocked feature families: `11`
- Current-only context remains blocked for historical feature use.
- Market, vendor, projection, ADP, and rank fields remain blocked as source truth unless a separate gate approves otherwise.

Null-fenced fields must preserve missingness. Missing values must remain null or `Not enough information` unless source semantics prove explicit zero.
