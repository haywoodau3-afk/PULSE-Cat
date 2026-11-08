# Reviewer 1 comment 4: plan for family-held-out limitation

## Agreed interpretation

The reviewer requests a fuller discussion of the smaller 10.3% pose improvement when entire substrate families are held out, and the implications for catalyst-scope development. The 31.9% target-held-out and 10.3% family-held-out estimates use different training/test splits; their difference alone does not establish a statistically significant degradation or support universal claims about all new chemistry. Substrate family holdout is distinct from a new catalyst family or reaction class.

## Prespecified evidence check and analysis

1. Locate the archived paired prediction files and split definitions underlying the published Elastic Net target- and family-held-out comparisons. Check model, endpoint, feature arm, cohort IDs, observations, train/validation/test membership, and confirm that recalculated pooled substrate MAEs reproduce 12.612/8.583 and 10.406/9.334. Stop and report a discrepancy rather than substitute a different benchmark.
2. Join the family-held-out predictions by held-out substrate and family, verify matching outcomes and split memberships, and recompute absolute errors from the observed and predicted values. Report per-family sample size, structure-only and pose MAE, and paired difference (structure-only minus pose). Include all families, family-balanced mean (equal weight per family), the original substrate-weighted pooled result, number of families and substrates favouring pose, and the largest-family contribution. Summarise results excluding the largest family only as a descriptive sensitivity check; do not reinterpret it as independent validation or an unbiased estimate of future performance.
3. Avoid formal significance claims or new population confidence intervals based on overlapping training sets and small, imbalanced families. The model selections and predictions are archived retrospective outputs, not new prospective experiments. Do not infer that 10.3% implies no useful information or establish that the differences between validation protocols are statistically significant.
4. Save a revision-local analysis script, input hashes, paired predictions, full per-family table, summary and verification. Amend the manuscript abstract, family-held-out discussion, limitations and conclusion as appropriate; add detailed accounting in the SI; retain prior changes from R1.3, highlight modifications, and draft a point-by-point response. Explicitly discuss relevance for new substrate families, unknown generalisation to new catalytic families, limited number and imbalance of chemical groups, and the need for independent and prospective checks. Render and review the revised documents.

## Status

Recorded before calculating the family-level statistics or modifying the documents. Interpretation confirmed by the user.

Completed: the archived predictions were reconciled and the family-level diagnostic, independent verification, reviewer response draft, and cumulative highlighted manuscript and SI copies are recorded in this folder. The complete 17-family table appears in SI Section S11. No model refitting or system change was needed.
