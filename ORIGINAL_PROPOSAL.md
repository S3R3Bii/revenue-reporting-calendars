# Revenue forecasting with firm-specific reporting calendars

**State: protocol only. No result or novelty claim yet.**

## Decision

Does fiscal-quarter alignment outperform calendar-quarter pooling when forecasting reported revenue?

## Target data

- [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) — targeted; exact export and rights must be verified.

## Study design

Panel forecasting with filing-time covariates.

Company and future-filing holdouts; amendment embargo; scale-normalized losses.

## Contribution to test

Treat reporting-calendar design as an empirical modeling choice. This is a proposed contribution, not a verified gap in the literature. Prior work must be reviewed before any novelty claim.

## Evidence to retain

- Exact source snapshot, request, retrieval time, observation window, definitions, units and redistribution terms.
- Prespecified splits, baseline, search space, tuning budget, seed and decision metric.
- All candidate results, including failures; final holdout used only after model selection.
- Independent headline recomputation, leakage checks and reviewed figures with units and uncertainty.
- Reproduction command and environment; private LaTeX manuscript written from measured results.

## Skills

forecasting, feature engineering, panel data. The repository must demonstrate these through executed work before they become portfolio claims.
