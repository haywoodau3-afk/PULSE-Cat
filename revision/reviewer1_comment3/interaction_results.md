# Reviewer 1 comment 3: factorial interaction results

The experiment used the prespecified common-test design. Positive source-minus-acquisition differences favour acquisition. The interaction is the ordering benefit with structure-only features minus the ordering benefit with the full Stage 2p block. All values are ee percentage points. The two datasets and overlapping splits limit inference.

| Domain | Structure + source | Structure + acquire | Pose + source | Pose + acquire |
|---|---:|---:|---:|---:|
| Fe(P7)Cl | 11.34 | 12.07 | 16.72 | 13.88 |
| Fe(CMC-Por)Cl | 9.62 | 10.77 | 15.70 | 14.27 |

The combined pose-plus-acquisition cell did not outperform structure plus source order or structure plus acquisition in either catalyst on average. It did outperform pose plus source order on average. The ordering benefit changes with the representation, but the observations do not establish a population-level interaction. The pose block is all 248 Stage 2p fields and the model is Ridge; this differs from the selected-feature Elastic Net representation benchmark.

## Full comparison summaries

### Fe(P7)Cl

| Measure | Mean | Median | IQR | Positive/negative splits |
|---|---:|---:|---:|---:|
| structure_historical_order | 11.34 | 10.04 | 8.47 to 13.25 | 20/0 |
| structure_uncertainty_diversity | 12.07 | 11.47 | 9.77 to 13.69 | 20/0 |
| structure_random | 10.87 | 10.59 | 8.66 to 12.63 | 20/0 |
| pose_historical_order | 16.72 | 16.12 | 13.98 to 20.81 | 20/0 |
| pose_uncertainty_diversity | 13.88 | 13.63 | 11.85 to 16.20 | 20/0 |
| pose_random | 14.25 | 14.02 | 11.88 to 16.32 | 20/0 |
| ordering_benefit_structure | -0.73 | -0.75 | -2.49 to 1.26 | 7/13 |
| ordering_benefit_pose | 2.85 | 2.28 | 0.21 to 5.34 | 17/3 |
| interaction_structure_minus_pose | -3.58 | -3.14 | -5.05 to -1.73 | 2/18 |
| combined_vs_structure_baseline | -2.53 | -1.86 | -5.01 to -0.94 | 3/17 |
| combined_vs_structure_acquire | -1.80 | -1.91 | -2.90 to 0.02 | 5/15 |
| combined_vs_pose_source | 2.85 | 2.28 | 0.21 to 5.34 | 17/3 |
| random_benefit_structure | -1.20 | -0.95 | -1.92 to -0.40 | 4/16 |
| random_benefit_pose | 0.37 | 0.50 | -1.17 to 1.19 | 12/8 |

### Fe(CMC-Por)Cl

| Measure | Mean | Median | IQR | Positive/negative splits |
|---|---:|---:|---:|---:|
| structure_historical_order | 9.62 | 9.11 | 8.23 to 10.99 | 20/0 |
| structure_uncertainty_diversity | 10.77 | 10.31 | 9.25 to 12.90 | 20/0 |
| structure_random | 10.21 | 9.99 | 7.98 to 11.61 | 20/0 |
| pose_historical_order | 15.70 | 15.38 | 11.30 to 18.47 | 20/0 |
| pose_uncertainty_diversity | 14.27 | 14.41 | 11.99 to 17.79 | 20/0 |
| pose_random | 15.33 | 16.13 | 12.22 to 18.94 | 20/0 |
| ordering_benefit_structure | -1.15 | -1.01 | -2.02 to -0.56 | 3/17 |
| ordering_benefit_pose | 1.43 | 0.54 | -0.80 to 1.99 | 11/9 |
| interaction_structure_minus_pose | -2.58 | -1.42 | -3.31 to 0.02 | 6/14 |
| combined_vs_structure_baseline | -4.64 | -5.01 | -7.14 to -2.03 | 1/19 |
| combined_vs_structure_acquire | -3.49 | -3.67 | -4.94 to -1.31 | 2/18 |
| combined_vs_pose_source | 1.43 | 0.54 | -0.80 to 1.99 | 11/9 |
| random_benefit_structure | -0.56 | -0.34 | -1.51 to 0.35 | 7/13 |
| random_benefit_pose | 1.06 | 0.27 | -0.02 to 2.37 | 14/6 |

## Checks and limitations

All prediction errors and split summaries were reconstructed from 33,000 held-out prediction rows. Test membership was checked, and 297 structure-only predictions were independently reproduced using a separate Ridge pipeline. Three pose acquisition trajectories per domain were rerun and matched the saved predictions. Pose cell aggregate scores matched the existing validated R1.1 records. The original active records all had nonzero Stage 2p rows; structure-only features were verified as an exact subset of the full matrix. See validation_report.txt and split_results.csv for details.

No significance test or independent dataset claim is made. The zero-filling behavior of the source feature loader is relevant to datasets with missing features; no active records in this analysis lacked the Stage 2p record or had an all-zero Stage 2p row. Random continuation averages three fixed runs per pair. Findings apply to the tested splits, budgets, acquisition implementation, Ridge and ee; selected-feature representations, other estimators, yields and prospective performance are not evaluated here.
