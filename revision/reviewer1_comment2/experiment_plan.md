# Reviewer 1, comment 2: acquisition-weight sensitivity plan

## Reviewer comment

> The uncertainty-diversity acquisition weights (0.40/0.40/0.20) are presented as a fixed rule without justification for the specific values. No sensitivity analysis is performed to show how the results change when these weights are varied, nor is there evidence that this particular combination is optimal or even reasonable for the studied systems.

## Objective and scope

Assess how the retrospective learning results change when the three top-level weights are varied. Provide an honest rationale for the weights as a fixed heuristic and clarify that the analysis does not establish an optimal policy. Keep the production analysis unchanged; implement weight overrides only in a revision-local wrapper.

## Implementation detail to make explicit

In `scripts/scope_progression.py`, the normalized diversity score is `D`, family coverage is `C`, and the uncertainty score is `U = 0.5 D + 0.5 Q`, where `Q` is normalized model disagreement (the standard deviation of the Ridge, Elastic Net, and Tanimoto-kNN predictions). The reported score is therefore

`S = wD D + wU U + wC C`.

At the reported weights `(wD, wU, wC) = (0.40, 0.40, 0.20)`, this expands to `S = 0.60 D + 0.20 Q + 0.20 C`. Thus, the three named top-level weights are not independent contributions: the uncertainty component already contains diversity. Verify this executable definition before writing the final manuscript wording. Report this structure plainly so that readers can interpret the sensitivity results correctly.

## Prespecified computational analysis

1. Reuse the 20 outer held-out splits and three matched initial pairs per split already recorded for the R1.1 common-test experiment. This keeps the test records and starts identical across weight combinations. Use 38 active Fe(P7)Cl records with six held out per split. For Fe(CMC-Por)Cl, use its 26 active aryl records, with five held out and 21 remaining as candidates per split. The seven locked audit records (2y, 2z, 4a, 4b, 4c, 4d, 4e) are a separate cohort, not members of these 26 active records; they remain outside all candidate, fitting, and test sets.
2. Evaluate the complete coarse simplex grid with weights in increments of 0.20: all non-negative `(wD, wU, wC)` triplets that sum to 1.00. This gives 21 combinations and includes `(0.40, 0.40, 0.20)` exactly. Do not add a post hoc fine grid.
3. For each split, initial pair, and grid point, vary only the three outer coefficients. Keep the recorded representation, component definitions and normalization, candidate-pool rules, model settings, training-only standardization, Ridge held-out scoring, prediction bounds, label budgets (2, 6, 10, 15, 20), and source-order tie-breaking fixed. Start every weight combination from the same pair; never allow held-out outcomes into training or acquisition.
4. For each trajectory, average the held-out Ridge MAE over the five label budgets. Average the three initial-pair scores within each split, then summarize across the 20 splits. For every grid point report mean MAE, median and IQR of split-level MAE, paired difference from the default-weight result, number of splits in which the default has lower MAE, and the default combination's rank among the 21 settings. Also report sequence overlap with the default route as a descriptive measure of how weights change selections.
5. Show the complete grid, not only its best-performing setting. Do not use these outcomes to choose a new weight or call the best grid point optimal. Any resampling interval is conditional on the fixed observed records and overlapping split-generation scheme; avoid significance or new-substrate population claims. State if small differences in rank are unstable or one split strongly affects a mean.
6. Validate that the wrapper reproduces the original default-weight selection sequence and predictions for the recorded common-test trajectories. Reconstruct aggregate metrics independently from the saved per-substrate predictions. Preserve seeds, split/pair IDs, versions, and input/code hashes. Keep the locked CMC audit records out of every candidate, fitting, and test set.

## Planned writing changes after results

- **Methods:** state the fixed heuristic rationale without implying a theoretical derivation or prior optimization; provide the exact operational component definitions and expanded effective equation. Describe the 21-point simplex sensitivity protocol and common held-out scoring.
- **Results:** report how held-out MAE changes across all weight combinations, where the default ranks and how consistently it compares with alternatives. Include negative, mixed, and influential-split findings. Do not announce a newly selected optimum.
- **Supporting Information:** add the full 21-combination results for each catalyst, a compact plot of the simplex, data/provenance, and the conditional nature of the comparison.
- **Limitations/conclusion:** state that weights are heuristic and system-specific, retrospective results do not identify a universal or optimal policy, and prospective calibration remains needed.
- **Reviewer response:** explain the rationale and the grid results directly, including the effective weighting overlap in `U`.

## Planned artifacts

- This plan, written before running the sensitivity analysis.
- A revision-local script, raw split/trajectory/prediction outputs, validation checks, and a concise results note under `revision/reviewer1_comment2/`.
- A point-by-point response draft and separate highlighted revised manuscript/SI DOCX files in this comment folder.

## Status

Plan recorded before implementation. A pre-run source-data check corrected the Fe(CMC-Por)Cl count: its 26 active records and seven locked audit records are disjoint. The first CMC invocation stopped at a count assertion before any sensitivity trajectories or outcomes were calculated. The successful analysis used the 26 active records and 21 candidates per five-record holdout. Both catalyst grids are complete; the default setting was validated against the prior project scoring and R1.1 common-test outputs. Results, validation, and document changes are recorded in `weight_sensitivity_results.md`, `validation_report.md`, and the separate revised DOCX copies.
