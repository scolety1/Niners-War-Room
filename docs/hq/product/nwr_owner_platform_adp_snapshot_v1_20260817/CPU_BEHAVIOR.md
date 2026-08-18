# CPU behavior

CPU selection math is unchanged. Only the market snapshot input changes. Source labels are explicit:

- Auto: `CPU_MARKET_ADP_OWNER_AUTO_SLEEPER`, `_ESPN`, `_CONSENSUS`, or `_FANTASYPROS`.
- Manual: `CPU_MARKET_ADP_OWNER_SLEEPER`, `_ESPN`, `_CONSENSUS`, or `_FANTASYPROS`.
- Fallbacks: `CPU_MARKET_ADP_FFC`, then `DISCLOSED_NWR_ORDER_FALLBACK`.
