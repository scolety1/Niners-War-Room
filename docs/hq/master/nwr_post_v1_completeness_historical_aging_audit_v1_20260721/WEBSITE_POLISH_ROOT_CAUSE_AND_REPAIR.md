# Website polish root cause and repair

Root cause: the default hidden Streamlit page was a runpy wrapper around the
live Draft Cockpit owner. Route registration was technically valid, but product
orientation and state authority were wrong for a first visit.

Repair: replace only the default wrapper content with a read-only Start Here
surface and rename the default page title to Niners War Room Home. Preserve the
dedicated /draft-cockpit owner and every route alias. Add focused AST and route
contract tests.

No data loader, model, formula, score, rank, identity, source, provider,
persistence service, launcher, Data Health behavior, or security control changed.
Rollback is a single revert of c0b3a136d3fdbb247cd702cbc7b7300676bda859.
