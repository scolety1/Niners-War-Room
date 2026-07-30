# Real-path mutation contract

Each mutation invokes an actual target/model, walk-forward, gate, detached
board, Team Window, Player Compare, or Trading Lab research-render contract.
Success requires the altered computed behavior to raise
`ResearchContractViolation`. Mutation identifiers and source substrings are not
detectors. The before/after table records the function/path, expected failure,
actual failure, evidence artifact, and sensitivity result for all 20 mutations.
Any surviving mutation fails generation and tests.
