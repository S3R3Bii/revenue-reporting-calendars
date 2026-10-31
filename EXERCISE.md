# Keep the forecast origin and reported fiscal slot explicit

Run the commands in README.md. Eight fixed requests produce two qualified saved-cohort forecasts, two abstentions and four rejections. Inspect data/requests.json, results/exercise.json and src/exercise.py.

The qualified Walmart requests use its already reported prior amount and period labels. Walmart growth outcomes never enter the training pool. Each response records the exact available fitting labels and qualifies the current-source, filing-day and persistent-slot assumptions.

An unknown fiscal slot and an origin that differs from the saved contract cause abstention. Investment advice, source-truth certification, exact future filing dates and arbitrary caller data are rejected. The interface is an inspectable implementation exercise, not a production finance service.

Explain why the test target's exact end date is an evaluation label rather than an input; why a current filing's fiscal focus cannot identify all comparative facts; and why a label available on the origin day is excluded. For an extension, implement an original-vintage dissemination adapter in a separate module with its own source controls and temporal tests. Preserve the frozen research files and do not retune on this test.
