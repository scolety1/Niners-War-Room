# Sparse-History Rule Blockers and Caveats

- Rule overlays are review-only and are not production/model-use.
- The partial-window expected-opportunity rules depend on ffopportunity/NGS windows and cannot support full-history claims.
- Current-only ADP, market data without as-of proof, CFBD/prospect production, SportsDataIO, PFF Elusive Rating, and `nwr_elusive_proxy_review_only` were not used.
- Non-sparse collateral damage is tracked because even sparse-only score changes can displace non-sparse players in season-position ranks.
- The primary success metric is net miss reduction, not Spearman alone.
