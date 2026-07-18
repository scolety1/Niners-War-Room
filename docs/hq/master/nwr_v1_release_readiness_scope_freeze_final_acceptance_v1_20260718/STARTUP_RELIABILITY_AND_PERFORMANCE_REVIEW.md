# Startup, reliability, and performance review

| Area | Observation | Classification |
|---|---|---|
| Cold startup | Server and HTTP 200 within a 2.18 s measured upper bound | Pass |
| Warm/repeat startup | Server start yielded in 2.01 s; full repeat matrix passed | Pass |
| Initial route | Default Draft Cockpit primary surface resolved | Pass |
| Major navigation | 180 endpoint/viewport checks passed | Pass |
| Rerun behavior | No DOM-visible uncaught exception or missing route | Pass |
| Hermetic bootstrap | 0.868 s clean; 0.513 s repeat; deterministic hashes | Pass |
| Receipt inspection | Passive; no receipt created | Pass |
| Rankings/compare/trade/draft | Representative and all-route rendering passed | Pass with governed optional-data caveats |
| Process cleanup | No 8518/8519 listener or candidate app process after shutdown | Pass |
| Deprecation warnings | Frequent Streamlit `use_container_width` warnings | POST_V1_OPTIMIZATION |
| Arrow fallback | Streamlit logs handled pandas/Arrow conversion tracebacks and auto-fixes some mixed object columns | BOUNDED_V1_CAVEAT |
| Rapid-navigation resets | Windows asyncio connection-reset messages appeared during aggressive automated navigation | POST_V1_OPTIMIZATION |
| Long-duration leaks | Not measured beyond bounded smoke | NOT_ENOUGH_INFORMATION |

No governed performance budget exists, so none was invented. Supported surfaces remained responsive and correct despite warning noise. Broad deprecation cleanup, dataframe normalization, and soak testing are post-V1 work unless a supported workflow begins failing.
