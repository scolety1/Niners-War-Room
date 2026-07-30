# Rollback Plan

The repair is isolated in two ordered commits: one implementation commit and one
documentation commit. If rollback is required after canonical adoption, revert
the documentation commit first and the implementation commit second using
ordinary non-force commits on canonical HQ.

Rollback returns Trading Lab wiring to the prior selector source; it does not
touch Finished V1, Outcome V3, frozen artifacts, active-pack data, user state,
providers, CFBD, or scheduled tasks. Because the old behavior is known to expose
only 66 players, rollback should be used only for a confirmed regression and
should be followed by a targeted source-authority repair.
