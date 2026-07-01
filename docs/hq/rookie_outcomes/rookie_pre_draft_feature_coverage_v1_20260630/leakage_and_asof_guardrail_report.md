# Leakage and As-Of Guardrail Report

No feature is experiment-safe now.

Required before future experiment planning:

- prediction anchor;
- point-in-time source snapshot;
- extraction timestamp;
- feature as-of timestamp;
- identity-safe join audit;
- missingness/censoring policy;
- leakage diagnostics;
- label interaction audit;
- row counts by season, position, and feature state;
- blocked-source scan;
- explicit non-activation boundary.

Future NFL production, roster state, depth chart role, injury report, practice status, snap count, activity week, contract context, schedule context, and labels cannot be pre-draft features without a future replay/as-of gate. Missing values remain `Not enough information`, not zero/false/clean/healthy/no-role/low-risk/confirmed UDFA.
