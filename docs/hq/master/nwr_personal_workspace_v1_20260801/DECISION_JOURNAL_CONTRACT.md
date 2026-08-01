# Decision Journal contract

Each prospective receipt has an immutable decision ID, decision type, asset-ID
set, per-asset decision-time source snapshot, rationale, and creation timestamp.
Status, follow-up, retrospective note, expected outcome, and confidence may be
updated without rewriting the original assets or source snapshot. Archive is
non-destructive; permanent deletion requires prior archive and explicit
confirmation.

The journal records what the user considered or did externally. It does not
claim a correct decision, market profit/loss, recommendation, or fabricated
outcome.
