# Freeze Immutability and No-Mutation Policy

1. Frozen V1 files may never be edited in place.
2. Any correction requires a separately versioned packet; the original V1 remains intact.
3. A correction notice must identify the exact defect, affected rows and hashes, discovery time, authorization, and relationship to V1.
4. A corrected packet may not silently replace the original evaluation artifact.
5. Future outcome evaluation must name the exact freeze version, commit, preregistration hash, baseline hash, and prediction-file hash used.
6. Interim or partial outcomes cannot authorize rewriting predictions, changing eligibility, or modifying the evaluation contract after results are known.
7. New application features may not consume frozen comparators as hidden ranking, sorting, recommendation, trade, or draft logic.
8. Canonical backup or repository relocation is append-only administration and must preserve bytes and hashes.
9. Hash mismatch, duplicate identity, unreasoned invalid score, or unexpected challenger presence is a stop condition.
