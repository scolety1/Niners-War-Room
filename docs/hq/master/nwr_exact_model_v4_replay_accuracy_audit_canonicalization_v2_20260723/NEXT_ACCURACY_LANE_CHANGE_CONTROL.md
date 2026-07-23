# Next accuracy lane change control

The exact next accuracy lane is:

Recover original historical checkpoint, final-score, and exact-rank receipts
with immutable as-of manifests.

This lane is not started by this mission. It requires bounded source admission
and human review before any computation. It must preserve exact player-ID
authority and temporal availability, must not substitute proxy scores, and
must not use current-only or retrospective evidence.

No further proxy tuning, model search, challenger creation, or production
implementation is authorized while missing exact receipts remain the dominant
constraint.
