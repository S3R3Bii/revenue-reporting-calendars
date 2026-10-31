# Fiscal labels versus calendar labels in a reported-revenue forecast

31 October 2026 UTC. Fixed before inspecting revenue values or running comparisons. The raw bodies have already been captured: only structure, company identity and metadata coverage have been inspected. The three-company convenience cohort and source transport are fixed in PROTOCOL.md and SOURCE_TRANSPORT.md.

## Decision, target and source meaning

Does pooling by the known fiscal-quarter label improve a one-fiscal-year-ahead forecast of a reported quarterly revenue amount over pooling by the prior period's calendar quarter? Compare simple, auditable pooled-growth forecasts with last year's same-quarter revenue and a pooled-growth intercept.

Use exactly us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax, unit USD, from the captured Apple, Microsoft and Walmart Company Facts files. Do not substitute another concept, unit or company if coverage is poor. The API contains standardized whole-entity facts; it does not expose every taxonomy-version detail. The target is the reported concept as currently reconstructed by this source, not harmonized economic revenue or audited financial truth.

All raw JSON, labels/descriptions, submission contact fields and corporate prose remain private. Public projections retain only necessary numeric/period/filing facts, source controls and original results.

## Complete source and filing accounts

Preserve every entry in the fixed concept/USD arrays, including duplicates, missing or invalid fields and observations outside the modeling window. Independently reconcile all native source hashes, CIKs, entry counts and financial-filing metadata arrays. Numeric parsing uses Decimal/Fraction, not binary float; missing or nonfinite values are never zero.

Use captured recent and listed historical Submissions arrays to associate each fact accession with form, filing day and exact reported reportDate. Check equal array lengths and complete controls. Exact repeated metadata rows may share a record with multiplicity and source-file provenance; conflicting metadata for an accession makes it unavailable. Preserve all duplicate and exclusion accounts. Do not infer original dissemination from the current capture timestamp.

## Quarterly observation construction

Keep only original form 10-Q facts whose source form and filed day match unique Submissions metadata. Amendments, annual reports and other forms remain in the complete source accounts but are excluded from quarterly targets. Match fact end exactly to that filing's reportDate, so a filing's fiscal focus is applied only to its own current report interval, never to comparative periods.

Require a valid start/end interval of 61-121 inclusive days, using the SEC's approximate quarterly duration convention of 91 days plus/minus 30 as an authored gate, not an exact fiscal-calendar certificate. Require fp in Q1/Q2/Q3, a known integer fiscal-year focus, and a finite strictly positive USD value. No synthetic fourth-quarter residual is created from annual-minus-year-to-date values. Reported nonpositive or unavailable values remain explicit and outside percentage-loss calculations.

A complete economic context is CIK/concept/unit/accession/start/end. Exact repeated entries with equal numeric value and consistent filing/fiscal metadata may be collapsed with multiplicity retained; conflicting values make that context unavailable. For a CIK/fiscal-year/fiscal-quarter slot require one actual report end. Conflicting report ends make the slot unavailable. Where multiple original accessions describe the same slot/end, choose the earliest filed day then accession under a declared deterministic rule, retaining every candidate and exclusion.

Restrict quarterly observations to report ends from 2018-01-01 through 2026-06-30 inclusive. Retain every company/fiscal-year/quarter slot and every reason a source entry is not an eligible observation. Values will be visible during reconciliation; this is source informed, not blinded.

## One-year forecast pair and availability contract

For each eligible target quarter pair the same company and fiscal quarter in the immediately preceding fiscal-year focus. Require the difference between period ends to be 335-395 days, an authored one-year tolerance of 365 plus/minus 30. Preserve unavailable pairs; do not choose an alternative prior quarter.

The forecast origin is the prior quarter's filed day plus one calendar day. Inputs are the prior reported revenue, the prior filing's known fiscal quarter and the calendar quarter of its actual prior report end. Neither the future target end nor future filing focus is an input. The target is the next fiscal year's same reported quarterly concept. This assumes persistence of that reporting slot; no exact future filing schedule is predicted.

A growth label is target/prior minus 1. It becomes usable for fitting on its target filed day plus one day. Every fitting label must have that availability day strictly before the forecast origin. This is a conservative filing-day reconstruction using current source metadata and accession-bound facts. It is not a verified immutable production point-in-time dataset; source revisions, extraction error and unavailable original dissemination evidence remain limitations.

## Fixed company and temporal separation

Training companies: Apple and Microsoft. Walmart growth labels are never used in fitting, smoothing selection, preprocessing or validation; its own prior reported amount and known period label can serve as forecast inputs.

Training-label report ends: 2019-01-01 through 2021-12-31. Validation targets for Apple/Microsoft: 2022-01-01 through 2023-12-31. For each validation forecast fit only training-company labels in the training window that are available strictly before its origin.

Use 2024 target growth labels as an embargo: they are never used for fitting or selection. Their quarter revenue can be a prior input for later forecasts when already reported. This separation allows all selected validation outcomes to be known before the protected test origins.

Final test targets for all three companies: 2025-01-01 through 2026-06-30. After selection, the fitting pool can include training-company labels through 2023-12-31, still filtered by availability strictly before each origin. Do not incorporate any 2024 or final-test growth label. Every test origin must be strictly after the maximum validation target availability day; fail the gate rather than silently dropping an offending forecast.

Report Apple/Microsoft future-time results and Walmart held-out-company results separately, with every forecast and denominator retained. Require at least three usable training labels for each training company, three validation pairs for each training company, and three test pairs per fixed company. A forecast needs at least three available fitting labels in total. If these minimum source/evaluation gates fail, do not replace a company, move dates or claim a protected forecasting result.

## Baselines, candidate grid and selection

Deterministic candidates:
1. Zero growth: forecast the prior same-fiscal-quarter revenue.
2. Global mean growth: mean available fitting growth across the two training companies.
3. Fiscal pooled growth: group fitting growth by its known prior fiscal-quarter label.
4. Calendar pooled growth: group fitting growth by the calendar quarter of its prior report end.

For the two grouped families, use prior-count strengths a in [0,1,4,16]. Predict growth as(sum group growth + a*global mean)/(group count+a). If a group is unseen, use the global mean even at a=0. The coarse pseudo-count grid spans no shrinkage through substantial pooling for a small cohort; these are authored candidates, not inherited tuned defaults or a global optimum. All fitting calculations and forecasts use exact Fraction arithmetic.

Forecast USD=prior USD*(1+predicted growth). Positive source revenue implies growth greater than-1, so these mean-based forecasts remain positive without clipping. Retain any violated invariant as a failure.

Primary selection loss is macro MAPE: compute mean absolute percentage error within each validation company, then average the two company means. This avoids giving the larger company or denser source coverage automatic dominance. Retain every validation prediction and score for all ten candidates. Select a separately for fiscal and calendar families, with ties resolved by smaller a. Also record the overall validation winner with the fixed tie order zero-growth, global-growth, fiscal candidates in ascending a, then calendar candidates in ascending a.

Commit the selected configuration and validation hashes before the first final-test command. The final test evaluates exactly four forecasters: zero growth, global mean growth, selected fiscal and selected calendar. Do not tune or pick a new winner from test results. A repair after test inspection must be labeled retrospective; it cannot become a new untouched test.

## Metrics and uncertainty limits

Export observation-level predictions, actual USD, prior USD, fiscal and calendar labels, origin/label availability, selected model and fitting-row membership for every validation and final-test case. Independently reconstruct fitting sets, pooled means, selection and losses without the production model functions.

Report MAE in USD, MSE in USD squared, RMSE in USD, and MAPE by company/model and macro across companies. Exact rational sums are retained; RMSE displays use 60-digit Decimal square roots with a declared six-decimal half-even representation. No post-result clipping, weighting or cohort change.

The final window has only two calendar years and three firms, including one company holdout. Preserve each year/company subgroup and paired calendar-versus-fiscal absolute-percentage-loss difference. Report leave-one-company-out and leave-one-year-out macro-loss differences as descriptive dependence checks. Do not claim calibrated confidence intervals, statistical significance or a population-wide winner from so few independent blocks.

## Checks, exercise and release

Commit a freeze of actual source/method/test dependencies before validation comparisons. Use independent native JSON numeric-lexeme/Fraction and SQLite reconstruction, complete source/quarter/pair/availability accounts and meaningful boundary fixtures. Freeze selection before test and preserve every failure.

The runnable exercise returns a qualified fiscal-slot forecast account under the stated source/availability assumptions or abstains for an incomplete period/origin contract. Reject investment advice, source-truth certification, exact future filing dates and arbitrary caller-data certification.

Release requires independent numerical and leakage checks, all source/evaluation minimums, meaningful tests, two isolated saved-data replays, readable source-bound figures and manuscript, privacy scope and exact candidate/main CI/tree/tag/metadata. The manuscript must lead with the actual finite finding, a practical data/modeling implication and material limits. No new-estimator, production-use, adoption, investment-return, causal or realized-savings claim. Separate formal-publication projects including Azure remain private.
