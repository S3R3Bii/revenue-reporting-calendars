# Source qualification for reported-revenue calendars

31 October 2026 UTC. Independent Study 23. The original forecasting proposal remains unexecuted. This phase qualifies source access and structure; it is not a completed study.

## Fixed source cohort and ordinary access

Use only official SEC public data and its API documentation:
https://www.sec.gov/search-filings/edgar-application-programming-interfaces .

Fix company CIKs to Apple 0000320193, Microsoft 0000789019 and Walmart 0000104169. They are an authored convenience cohort. Earlier declared-agent command-line Company Facts access returned HTTP403. Try an ordinary public browser navigation once per exact endpoint, sequentially. Stop an endpoint on access denial or a security challenge. Do not rotate agents, use proxies, bypass controls, alter browser protections or obtain private exports.

Company Facts endpoints:
- https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json
- https://data.sec.gov/api/xbrl/companyfacts/CIK0000789019.json
- https://data.sec.gov/api/xbrl/companyfacts/CIK0000104169.json

Submissions endpoints:
- https://data.sec.gov/submissions/CIK0000320193.json
- https://data.sec.gov/submissions/CIK0000789019.json
- https://data.sec.gov/submissions/CIK0000104169.json

If a successful Submissions response lists public historical metadata files, at most four listed files per company may be captured when their declared filing range intersects 2018-2026. Use only exact filenames observed in the source response, not guessed URL variants. Keep unrelated submissions metadata private.

## Capture boundary

Save successful native decoded JSON bodies privately with exact URL, request/response times, observed status/content headers, decoded-byte size and SHA-256. Browser capture may read the response body already obtained by ordinary navigation through supported developer tools; it must not change authentication, security settings, browser state or headers. Record decoded-body provenance rather than claiming wire-compressed byte identity.

In this source-qualification phase inspect only content type, valid JSON structure, CIK/entity identity, top-level fields and metadata date-range coverage. Do not print revenue values or expressive labels/descriptions. Capture itself is not model validation, source-truth certification or historical availability evidence.

Before inspecting revenue values or running comparisons, commit a concrete numerical protocol: target concept/unit, exact interval/quarter construction, complete missingness and duplicate handling, source/filing identity, availability assumptions, train/validation/test and company separation where applicable, baseline/candidates/selection rule, all metrics and meaningful independent checks. Follow MODEL_VALIDATION_STANDARD.md. If a faithful forecasting target or prediction-origin contract cannot be established, preserve the original forecast hold and identify an honestly scoped measurement question before any comparison; do not relabel a source-access note as executed research.

## Acceptance and publication

A completed study requires lawful reconciled native source, explicit reporting-period/identity/availability accounts, actual committed methods before comparisons, complete outputs, meaningful fixtures, independent reconstruction, reproducible execution, clear practical use, readable source-bound figures/manuscript, privacy scope and exact candidate/main CI/tree/tag/metadata proof.

Current Company Facts may aggregate multiple filings, units, periods and fiscal focuses. A filing fiscal-year/period label is not automatically the fact's own interval. SEC calendar frames match approximate calendar durations; exact start/end and filing context must remain visible. No model accuracy, safe financial decision, investment return, source truth, scientific novelty, deployment or savings is claimed in this protocol. Formal-publication projects including Azure remain private.
