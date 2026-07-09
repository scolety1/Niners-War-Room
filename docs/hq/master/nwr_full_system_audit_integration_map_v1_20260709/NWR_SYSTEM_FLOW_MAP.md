# NWR System Flow Map

## Intended Flow

```text
Data sources
  -> source receipts and use gates
  -> identity joins
  -> missingness and leakage/as-of checks
  -> historical labels
  -> historical panels
  -> benchmark datasets
  -> Formula Gauntlet review-only tests
  -> finalist failure review
  -> Master HQ decision
  -> review-only ranking staging
  -> app/UI label review
  -> production integration only if separately approved
```

## Current Flow Breaks

1. Source receipts are not uniformly canonical. Several Data Hygiene packets remain local-only.
2. Exact Model v4 historical receipt chain is missing.
3. Route denominator source is not admitted.
4. Formula Gauntlet readiness/scaffold packets are local-only.
5. Partial replay evidence exists but no approved formula score exists.
6. Rankings integration lacks approved benchmark and source-use gates.

## Working Subflows

### Governance Subflow

HQ1 source receipt standard and parallel lane boundaries are canonical. This is the strongest part of the system.

### Current Board Rebuild Subflow

The current app-visible candidate board can be exactly rebuilt from recovered inputs in a local review lane. This proves current-board reproducibility but not historical accuracy.

### Label / PYF Subflow

Historical labels and PYF baseline are review-ready for component signal tests. PYF must remain the anchor.

### Route Recovery Subflow

The route recovery flow is closed until a provider response, license, or source-admitted public feed appears. Proxies remain proxies.

## Integration Diagnosis

NWR has the pieces of a machine, but the machine is not flowing end-to-end. It needs batch canonicalization of Data Hygiene and Model v4 evidence packets, then a receipt locator/ledger lane, before Formula Gauntlet execution is a rational next step.
