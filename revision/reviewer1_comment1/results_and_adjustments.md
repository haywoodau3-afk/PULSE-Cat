# Reviewer 1 comment 1: results and planned manuscript adjustments

## Reviewer concern and interpretation

The reviewer asks whether the 55.3% and 33.2% reductions are stable under alternative initial substrate pairs and how uncertainty affects their interpretation. The author confirmed that the results must be reported faithfully, even if they weaken the claims. An initial substrate pair is distinct from a pseudorandom seed and from the project's separate 12-substrate Seed Set.

## Reproduction of archived comparisons

With the current workspace inputs and code, the recorded Ridge MAE at every nonempty prefix and the complete selection sequence matched the archive for both reported-order and uncertainty–diversity routes in both systems. Mean-prefix values were 21.6721835 versus 9.6839904 for Fe(P7)Cl and 13.1548784 versus 8.7868169 for Fe(CMC-Por)Cl. The routes began with different pairs: 1a/1b versus 1a/1am, and 2aa/2ab versus 2b/2ac, respectively. This numerical reproduction is not proof of the original environment or bitwise reproduction of every archived output.

Detailed checks: [Fe(P7)Cl](results/p7/reproduction_check.csv) and [Fe(CMC-Por)Cl](results/cmcpor/reproduction_check.csv).

## New shared-start analysis

For each catalyst, 50 distinct unordered initial pairs were sampled uniformly without replacement using documented pseudorandom seeds (20261105 and 20261106). Each pair was shared by uncertainty–diversity and source-order continuation; the random comparator is the mean of three independently seeded random continuations from that same pair. The active ee populations were 38 and 26 substrates. Ridge mean-prefix MAE was averaged across nonempty remaining-pool prefixes 2–37 and 2–25, respectively, using the existing representation, score, preprocessing, model settings, and prediction bounds. Positive paired differences below mean the comparator had a larger error than uncertainty–diversity.

| Catalyst | Comparator | Mean paired difference (ee points) | Conditional 95% bootstrap interval for mean | Pairs favouring uncertainty–diversity |
|---|---|---:|---:|---:|
| Fe(P7)Cl | Source-order continuation | 6.14 | 5.41 to 6.88 | 50/50 |
| Fe(P7)Cl | Mean of 3 random continuations | 0.50 | 0.15 to 0.86 | 31/50 |
| Fe(CMC-Por)Cl | Source-order continuation | 1.66 | 1.27 to 2.04 | 45/50 |
| Fe(CMC-Por)Cl | Mean of 3 random continuations | 2.62 | 2.13 to 3.11 | 47/50 |

The intervals resample the 50 whole-pair differences 10,000 times and describe the estimated mean over the sampled starting-pair distribution conditional on these fixed data and protocol. They are approximate Monte Carlo intervals, not intervals for the original individual 55.3%/33.2% reductions, and they do not quantify sampling uncertainty over substrates, chemistry, experimental measurements, or new catalyst systems. Initial pairs are sampled without replacement from finite sets; simple resampling does not apply a finite-population correction. The per-pair 2.5th–97.5th percentile spreads and full values are in the summaries and pair-result files.

Each route is evaluated on its own evolving unrevealed pool; equal budgets and a common starting pair do not give a common test set after routes diverge. Random results are the average of only three random continuations per pair. Fe(P7)Cl's result against random is particularly variable; no claim of uniform superiority is justified. No formal hypothesis test or significance claim is made.

Results and reproducibility: [Fe(P7)Cl summary](results/p7/summary.json), [Fe(P7)Cl pairs](results/p7/pair_results.csv), [Fe(P7)Cl curves](results/p7/learning_curves.csv), [Fe(CMC-Por)Cl summary](results/cmcpor/summary.json), [Fe(CMC-Por)Cl pairs](results/cmcpor/pair_results.csv), [Fe(CMC-Por)Cl curves](results/cmcpor/learning_curves.csv), [paired-difference figure](results/shared_start_sensitivity.png), and [learning-curve figure](results/shared_start_learning_curves.png). The pair files, replay code, seeds, input hashes, and package versions are preserved in the results folder and script metadata.

## Prespecified common-test-set check

The seven previously locked Fe(CMC-Por)Cl audit records have ee labels. For the same 50 pairs, Ridge prediction error was evaluated on these same seven records at 6, 13, and 20 active labels, and the three MAEs were averaged within each route and pair. The mean source-order-minus-uncertainty–diversity difference was **−0.40 ee points**, with a conditional pair-bootstrap 95% interval of **−1.02 to 0.20**; uncertainty–diversity had lower mean audit MAE for **27 of 50** pairs. This small fixed-set check does not establish a reliable held-out advantage. Its interval is conditional on the same seven records and 50 pair-sampling protocol and is not an interval over independently sampled future compounds or catalysts.

The Fe(P7)Cl late-stage records do not have experimental ee labels, so they cannot be used as a labelled common test set. The CMC audit set was previously designated as locked, but it has been examined in existing work; it should not be described as a fresh prospective external validation.

The [audit summary](results/cmcpor/fixed_audit_summary.json), [paired scores](results/cmcpor/fixed_audit_pair_results.csv), and [individual predictions](results/cmcpor/fixed_audit_predictions.csv) are retained. All 300 budget-level audit MAEs were independently recalculated from the 2,100 substrate-level predictions.

## System and writing adjustments

- A scoped [replay wrapper](initial_pair_replay.py) accepts common initial pairs while using the existing selection and prediction functions; original code and archived outputs remain intact. A [separate audit script](secondary_fixed_audit.py) evaluates the seven locked CMC records. The [plotting script](plot_initial_pairs.py) produces the shared-start figure.
- The original code suppresses Elastic Net convergence warnings. The analysis reproduces that policy for comparability; it does not establish that every fit converged.
- In the manuscript, qualify the original percentages as two recorded trajectory comparisons, add the shared-start results, report the mixed fixed-audit result, and qualify the abstract, conclusion, and limitations.
- In the SI, add the experimental design, conditional interval definition, a compact results table and two figures, fixed-audit caveat, and data provenance. Preserve the original archived comparison and distinguish it from the new replay.
- A reviewer response should explain the two analyses and acknowledge that the new intervals do not quantify uncertainty for the original single-trajectory percentages or for new catalysts.

## Verification

The two active populations contain the expected 38 and 26 ee-labelled records, and all 64 active IDs have Stage-2p feature records. For each system, the 50 pairs were distinct; all 250 runs had complete, matching budget sequences, consistent starting-pair Ridge MAEs, and independently recalculated pair summaries. These checks validate the recorded computations, not chemical generalisability.

## Further common-test-set analysis

The [prespecified repeated-holdout analysis](common_test_plan.md) and [results](common_test_results.md) extend the check to both active datasets. The results are mixed, especially for Fe(CMC-Por)Cl; the two original percentages are still single-trajectory descriptive results. The earlier seven-record CMC audit remains separate from these new 20-split experiments.
