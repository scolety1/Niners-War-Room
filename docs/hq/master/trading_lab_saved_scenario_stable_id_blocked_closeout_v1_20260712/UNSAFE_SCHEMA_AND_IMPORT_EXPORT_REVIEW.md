# Unsafe Schema and Import/Export Review

## Schema result

The rejected store schema is version integer `1` with namespace
`trading_lab_saved_manual_scenarios_v1`. Its validator admits selected-asset strings when they
begin with `player:` or `pick_context:`. It validates the prefix, length, collection bounds, and
duplicates, but does not prove an authoritative stable asset identity.

This makes both `scenarios[].selected_assets.give` and
`scenarios[].selected_assets.get` unsafe. Composite rank/name/position/team tokens can pass the
allowlist, be written to the store, and later be applied to session state.

## Import/export result

Export serializes the validated store verbatim, including the prohibited composite asset
tokens. Import validates and accepts the same tokens by prefix and can replace the local store
after confirmation. Consequently, both exported and imported content can contain prohibited
display/source facts.

The 1 MiB bound, exact-key validation, unsupported-version rejection, preview, confirmation,
atomic replacement, backup validation, and corrupt-file quarantine are useful secondary
mechanics. They do not make the identity payload admissible.

## Runtime namespace evidence

The rejected service would have used:

- default root: `C:\NWR_SHARED_DATA\trading_lab_saved_manual_scenarios_v1`;
- environment override: `NWR_TRADING_LAB_SCENARIO_STATE_ROOT`;
- latest file: `scenario_store.json`;
- child folders: `backups/` and `corrupt/`.

Fresh validation found no tracked runtime store or namespace path in HQ, found the default root
absent on the validating host, and found no environment override set. No runtime cleanup or
production migration is required.

## Final disposition

Schema version `1` is rejected and noncanonical. No migration is authorized, because the
implementation was never pushed. A future implementation must begin only after the reentry gate
passes and must receive a new, separately reviewed schema and privacy decision.
