# Reviewer 1 comment 1: repeated common-test-set results

## Objective and design

The prespecified [common-test plan](common_test_plan.md) examines the remaining concern that acquisition routes in the earlier analysis were scored on different unrevealed substrates. For each domain, 20 distinct random outer test sets were drawn from the same active ee-labelled records: six held-out substrates from 38 Fe(P7)Cl records, and five from 26 Fe(CMC-Por)Cl records. The seven previously locked Fe(CMC-Por)Cl audit records were excluded throughout this new analysis.

Within each outer split, three distinct initial pairs were drawn from the remaining candidate substrates. Uncertainty–diversity, source-order continuation, and three random continuations for each pair began with the same two substrates and were scored on the same held-out records. Ridge MAE was evaluated at 2, 6, 10, 15 and 20 active labels, and averaged over budgets. Source-order continuation means choosing the earliest remaining source-order record *after* the shared starting pair; it is not the original archived source-order trajectory.

For each initial pair, the three random-continuation scores were averaged. Scores were then averaged across the three pairs within each outer split. A positive difference below means the comparator had higher held-out MAE than uncertainty–diversity. Seeds were 20261108 and 20261109 for Fe(P7)Cl and Fe(CMC-Por)Cl, respectively.

## Results

| Catalyst | Comparator | Mean paired difference (ee points) | Median difference (IQR) | Splits favouring uncertainty–diversity |
|---|---|---:|---:|---:|
| Fe(P7)Cl | Source-order continuation | 2.85 | 2.28 (0.21 to 5.34) | 17/20 |
| Fe(P7)Cl | Mean of random continuations | 0.37 | 0.50 (−1.17 to 1.19) | 12/20 |
| Fe(CMC-Por)Cl | Source-order continuation | 1.43 | 0.54 (−0.80 to 1.99) | 11/20 |
| Fe(CMC-Por)Cl | Mean of random continuations | 1.06 | 0.27 (−0.02 to 2.37) | 14/20 |

The Fe(CMC-Por)Cl source-order comparison contains one split with a difference of +17.76 ee points; the mean of 1.43 is therefore materially larger than the median of 0.54. It has not been excluded or replaced. Observed source-order paired differences range from −2.45 to 9.28 for Fe(P7)Cl and from −3.08 to 17.76 for Fe(CMC-Por)Cl.

The approximate 95% split-bootstrap intervals for the *mean over the random split and starting-pair scheme*, conditional on these fixed data, were 1.52 to 4.22 and −0.06 to 3.48 ee points for the source-order comparison in Fe(P7)Cl and Fe(CMC-Por)Cl, respectively. For the random comparator, the respective intervals were −0.60 to 1.49 and 0.41 to 1.77. These are Monte Carlo summaries of the specified retrospective split-generation procedure; they are **not** confidence intervals across independent experimental datasets, future substrates, or catalysts. The outer test sets overlap, all fits share the same source datasets, there are only 20 outer splits, and the individual test sets contain only five or six records. No formal statistical-significance or population-generalisation claim is made.

The earlier seven-record Fe(CMC-Por)Cl audit remains a distinct check: it yielded a mean paired source-order-minus-uncertainty–diversity difference of −0.40 ee points and favoured uncertainty–diversity for 27/50 initial pairs. The two evaluations use different test sets, starting-pair schemes and label budgets; neither should be substituted for the original 55.3% and 33.2% single-trajectory values.

## Data and reproducibility

- [Fe(P7)Cl summary](results/common_test/p7/summary.json), [outer splits](results/common_test/p7/outer_splits.csv), [starting pairs](results/common_test/p7/initial_pairs.csv), [split results](results/common_test/p7/split_results.csv), [budget-level runs](results/common_test/p7/runs.csv), and [held-out predictions](results/common_test/p7/predictions.csv).
- [Fe(CMC-Por)Cl summary](results/common_test/cmcpor/summary.json), [outer splits](results/common_test/cmcpor/outer_splits.csv), [starting pairs](results/common_test/cmcpor/initial_pairs.csv), [split results](results/common_test/cmcpor/split_results.csv), [budget-level runs](results/common_test/cmcpor/runs.csv), and [held-out predictions](results/common_test/cmcpor/predictions.csv).
- [Analysis script](common_test_experiment.py), [plotting script](plot_common_test.py), and [split-level figure](results/common_test/common_test_split_differences.png). The output directories also retain full selection-event files, the original-function equivalence checks, software versions and hashes.

## Validation

The new simulator's first split and pair were checked against the original progression function for all three routes: the selection prefix through 20 labels and all saved Ridge test predictions at the five budgets matched exactly. Because Fe(CMC-Por)Cl split 18 had an unusually large effect, all 15 of its trajectories were additionally rerun with the original progression function; every selection prefix and saved prediction matched ([check](results/common_test/cmcpor/outlier_split18_original_function_check.csv)). Across all runs, the held-out records were never selected, the same starting pair was used by each route within a pair, and the previously locked CMC audit IDs never entered the new split candidate or test pools. All 9,000 Fe(P7)Cl and 7,500 Fe(CMC-Por)Cl saved predictions were independently used to reconstruct the reported budget-level and split-level scores. Of the active records, 37/38 Fe(P7)Cl and 26/26 Fe(CMC-Por)Cl substrates appeared in at least one outer test set.

The original code suppresses Elastic Net convergence warnings; this replay preserves the original scoring behaviour, so the absence of warnings does not establish that every fit converged.
