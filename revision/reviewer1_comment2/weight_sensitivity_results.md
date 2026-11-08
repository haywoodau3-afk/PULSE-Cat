# Reviewer 1, comment 2: weight-sensitivity results

## Analysis completed

The prespecified 21-point simplex grid was evaluated in each catalyst domain using the same 20 common-test splits and three shared initial pairs per split as the R1.1 common-test analysis. Each combination changed only the top-level coefficients on diversity (D), uncertainty (U), and family coverage (C). The Ridge model was scored on the same held-out records at five label budgets, with split-level MAE averaged over budgets and starting pairs.

The CMC-Por active aryl cohort contains 26 records. The seven locked audit records (2y, 2z, 4a, 4b, 4c, 4d, 4e) are a separate cohort; they are disjoint from those 26 and were not eligible for fitting, acquisition, or test. The first CMC invocation stopped at a pre-analysis count assertion and generated no trajectories. The count was corrected from the source records before the successful run.

## Operational score and rationale

Code inspection confirms that the score components are not orthogonal. Diversity is normalized structural novelty `D`; model disagreement is the min-max-normalized standard deviation across Ridge, Elastic Net, and Tanimoto-kNN predictions, `Q`; and operational uncertainty is `U = 0.5D + 0.5Q`. Family coverage is `C`. Therefore:

`S = wD D + wU U + wC C`

and the default `(wD,wU,wC)=(0.40,0.40,0.20)` expands to:

`S = 0.60D + 0.20Q + 0.20C`.

The defensible rationale is deliberately limited: the fixed written score gives equal top-level coefficients to U and D and a smaller nonzero coefficient to family coverage. This is a simple heuristic convention, not a chemical derivation or a claim that the terms contribute independently. The weights were not selected by optimizing held-out results in this analysis.

## Results

| Catalyst | Default mean held-out MAE (ee points) | Default position in grid | Grid range of mean MAE | Lowest observed grid mean | Default lower than lowest-mean setting |
|---|---:|---:|---:|---:|---:|
| Fe(P7)Cl | 13.88 | 11th of 21 | 13.34–15.45 | 13.34 | 9/20 splits |
| Fe(CMC-Por)Cl | 14.27 | tied 10th–11th of 21 | 13.61–15.70 | 13.61 | 6/20 splits |

The lowest P7 grid mean occurred at `(0.00, 0.80, 0.20)` and was 0.53 ee points below the default mean. The lowest CMC-Por grid mean was 0.66 points below the default and tied across five settings with zero direct D coefficient; U still contains half of D, so these settings do not remove the diversity contribution from the operational score. The comparison to each grid minimum is descriptive and has selection optimism because the minimum is chosen from the same 21 retrospective evaluations; it is not evidence that either setting should replace the default.

At the setting with the lowest mean in each dataset, the default had lower MAE in 9/20 P7 splits and 6/20 CMC-Por splits. Across grid settings, the mean selected-set Jaccard overlap at 20 labels with the default ranged from 0.65 to 1.00 for P7 and 0.91 to 1.00 for CMC-Por. Thus, weights changed selections more in P7, while prediction error differences remained modest in mean terms. The full grid and split-level paired differences are retained below.

The default is a middle-ranked, competitive heuristic in both datasets, but the grid does **not** establish it as optimal or uniquely justified. It also shows that alternative weights can give slightly lower retrospective errors. We therefore retain the original coefficients only as a fixed study rule, state the limited rationale and exact effective score, and avoid selecting a replacement using these same held-out records.

## Design, reproducibility, and validation

- [Prespecified plan](experiment_plan.md), recorded before the sensitivity calculations; its CMC cohort count was corrected from source records before the successful CMC run.
- [Sensitivity script](weight_sensitivity.py) and [plotting script](plot_weight_sensitivity.py).
- [P7 summary](results/weight_sensitivity/p7/summary.json), [full 21-setting table](results/weight_sensitivity/p7/weight_summary.csv), [split-level results](results/weight_sensitivity/p7/split_results.csv), [trajectory metrics](results/weight_sensitivity/p7/trajectory_results.csv), [selected sets](results/weight_sensitivity/p7/selected_sets_at_20.csv), and [all held-out predictions](results/weight_sensitivity/p7/heldout_predictions.csv).
- [CMC-Por summary](results/weight_sensitivity/cmcpor/summary.json), [full 21-setting table](results/weight_sensitivity/cmcpor/weight_summary.csv), [split-level results](results/weight_sensitivity/cmcpor/split_results.csv), [trajectory metrics](results/weight_sensitivity/cmcpor/trajectory_results.csv), [selected sets](results/weight_sensitivity/cmcpor/selected_sets_at_20.csv), and [all held-out predictions](results/weight_sensitivity/cmcpor/heldout_predictions.csv).
- [Simplex figure](results/weight_sensitivity/weight_sensitivity_simplex.png) and [independent validation report](validation_report.md).

The wrapper's default component score matched the unchanged project scoring function. For all 60 split/start-pair trajectories in each domain, default-weight selected sequences matched R1.1 exactly; all default held-out Ridge predictions also matched exactly (maximum absolute difference 0). All 69,300 saved predictions were independently used to reconstruct the trajectory, split, and weight-summary MAEs. Held-out IDs matched each pre-recorded test set at every budget. Locked audit IDs were not in the active, candidate, or test records.

The P7 job began before the CMC active-cohort count correction; the correction affected only the CMC assertion, not the P7 path or calculations. A corrected successful CMC run completed after the plan was amended. No project acquisition code or archived source data were changed.

## Limits

The 20 outer splits overlap, the initial pairs and labels come from two fixed retrospective datasets, and the grid is deliberately coarse. Weight ranks and minimum-grid values are descriptive, not independent validation, confidence intervals, significance tests, or estimates for new substrates or catalysts. Elastic Net convergence warnings are suppressed in the underlying code; reproducing its scoring behavior does not prove every fit converged. No prospective experiment was performed.

## Follow-up: comparison with common-test baselines

The 21 settings were compared with the existing source-order and three-continuation random averages on the same 20 splits, starts and budgets. Positive comparator-minus-setting differences favour the setting. For Fe(P7)Cl, all 21 settings had a positive mean difference against source order (range 1.28–3.38 ee points), and 18/21 against random (range −1.20–0.90). For Fe(CMC-Por)Cl, 20/21 settings had a positive mean against source order (range 0.00–2.09); the all-family-coverage setting tied source order on each split. Against random, 20/21 had positive means (range −0.37–1.72). Split-level outcomes vary: counts favouring a setting ranged 13–17 and 0–14 of 20 against source order, and 8–15 and 11–17 against random, for P7 and CMC-Por respectively. These are descriptive averages over overlapping splits from fixed datasets, not significance tests.

Full results are in `results/weight_sensitivity/p7/baseline_comparisons.csv` and `results/weight_sensitivity/cmcpor/baseline_comparisons.csv`; `compare_baselines.py` checks all 20 split IDs and reproduces the default held-out MAEs from the R1.1 records. The saved grid contains common-test predictions at five budgets, not remaining-pool predictions at every prefix, so the original mean-prefix metric cannot be reconstructed from these saved outputs. The common-test results cannot be interpreted as sensitivity of the original 55.3% and 33.2% reductions.
