# Privacy and Rights Review

All 162 local-only absolute paths are replaced by opaque locator IDs. The three restricted records retain only artifact ID, non-reversible locator ID, locality/state/rights/privacy metadata, permitted aggregate row/schema metadata, and a withholding caveat; raw paths, raw hashes, provider content, private IDs, and reversible locator material are excluded. The 19 off-HQ locators retain only the permitted commit and repository-relative object path for audit/no-recreate discovery and are explicitly use-blocked.

No source/use rights were inferred from accessibility, public visibility, cache presence, review history, identity approval, recency, hashes, or prose. Result: `PASS_NO_RIGHTS_OR_PRIVACY_EXPANSION`.
