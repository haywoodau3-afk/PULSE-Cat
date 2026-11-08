# Stage 2 Final Report

## Scope

Stage 2 produced model-facing features and baseline diagnostics for the JACS 2025 substrate scope.

- Reaction ledger: 41 records.
- Reaction-center coverage: 41 checked records.
- Feature-ready product-map coverage: 12 seed records.
- Atom-mapped non-seed coverage: 29 records with inferred checked reaction centers and deferred product maps.
- Pose-summary coverage: 41 records.
- Pose-interaction coverage: 8,200 retained poses.
- xTB/BDE features: deferred to Stage 3.

## Label Policy

- `1an` is excluded from ee modelling because the product is achiral.
- `1ad` remains in the ledger but is excluded from ee modelling because the 0% ee label is likely undetermined by a separation problem.
- `1z` remains in the ledger but is excluded from the matched 38-substrate ee cohort so the early benchmarks use the same cohort as the later protocols.
- Yield modelling uses all records with numeric isolated yield.

## Model Summary

| Target | Records | Split | Structure-only best / MAE | Pose-aware best / MAE | Overall best / MAE |
| --- | ---: | --- | --- | --- | --- |
| ee | 38 | target_holdout | lightgbm / 10.006 | elastic_net / 8.583 | structure_pose / elastic_net / 8.583 |
| yield | 41 | target_holdout | lightgbm / 13.105 | lightgbm / 13.963 | structure_only / lightgbm / 13.105 |
| ee | 38 | family_holdout | lightgbm / 9.869 | elastic_net / 9.334 | structure_pose / elastic_net / 9.334 |
| yield | 41 | family_holdout | elastic_net / 13.912 | lightgbm / 12.391 | structure_pose / lightgbm / 12.391 |

## Interpretation

The target-holdout ee benchmark currently favors pose-aware Elastic Net. After excluding `1ad` and aligning the cohort by excluding `1z`, the result should be treated as a provisional Stage 2 baseline rather than a broad chemical generalization claim.

Family-held-out validation is the stricter test. Its metrics should be used to decide how much trust to place in predictions for genuinely new substrate families.

Yield modelling is now available as a parallel baseline, but yield and ee should not be assumed to prefer the same model or feature set.

## Recommended Baselines Going Into Stage 3

- ee target-holdout baseline: structure_pose / elastic_net.
- yield target-holdout baseline: structure_only / lightgbm.
- Treat family-held-out performance as the main risk signal for prospective substrate selection.
- Keep xTB/BDE out of Stage 2; add it in Stage 3 only after deciding which families and residual failures need deeper energetics.

## Remaining Stage 3 Hand-Off

- Complete manual product atom maps for the 29 non-seed records if publication-grade `feature_ready` status is required.
- Add xTB/BDE candidate-site features and calibration.
- Use family-held-out residuals to choose prospective experiments or higher-level calculations.
