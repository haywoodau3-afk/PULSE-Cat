# Reviewer 1 comment 6: findings and adjustments

## What was evaluated

The earlier independent yield trajectories evaluate route-dependent remaining pools; their AUC-MAE values do not directly compare predictions on identical substrates. We therefore reused the 20 prespecified common-test splits and three starting pairs per split from comment 1. All 38 Fe(P7)Cl and 26 Fe(CMC-Por)Cl aryl active records have numeric ee and yield fields, labelled exact in the curated ledger. Source scope captions specify isolated yields. These checks do not independently establish every yield value from source documents. Seven Fe(CMC-Por)Cl audit records remained excluded; the excluded sulfonyl 6q censored yield does not enter this analysis.

For each endpoint separately, the existing frozen uncertainty–diversity rule and Ridge model were used with common candidate pools, test sets, starting pairs and budgets (2, 6, 10, 15, 20). Each endpoint used its own measured training labels; ee predictions and sequences from the earlier verified run were reused. Random results average three continuations per pair. Test sets contain six P7 or five CMC aryl substrates. Within each split the metric averages prediction MAEs across five budgets and three starts; the table averages over 20 overlapping splits. Starting-budget scores are necessarily equal across routes. They are not the earlier AUC-MAE values.

| System and endpoint | Source-order MAE | Uncertainty–diversity MAE | Random MAE | Splits favouring uncertainty–diversity over source / random |
|---|---:|---:|---:|---:|
| Fe(P7)Cl yield | 21.11 | 18.28 | 20.85 | 17/20 / 17/20 |
| Fe(P7)Cl ee | 16.72 | 13.88 | 14.25 | 17/20 / 12/20 |
| Fe(CMC-Por)Cl aryl yield | 24.38 | 24.99 | 24.76 | 8/20 / 6/20 |
| Fe(CMC-Por)Cl aryl ee | 15.70 | 14.27 | 15.33 | 11/20 / 14/20 |

Errors are percentage points. P7 yield source-minus-acquisition split differences range from −3.70 to 15.19; CMC yield from −5.90 to 7.64. Overlapping splits are not independent datasets; differences are descriptive, not general significance tests. This analysis shows both improved P7 yield prediction and mixed/slightly worse CMC yield prediction. It does not establish universal failure, nor broad utility for yield.

## Diagnostics and interpretation

The score is 0.40 novelty + 0.40 uncertainty + 0.20 family coverage. Code defines uncertainty as 0.5 times normalized novelty plus 0.5 times normalized disagreement among Ridge, Elastic Net and Tanimoto-kNN. Therefore, apart from normalization edge cases, the nominal rule effectively contains 0.60 novelty, 0.20 model disagreement and 0.20 coverage. This is a demonstrated property of the implemented rule: its uncertainty component is not a calibrated yield-error probability, and a high score need not identify a substrate that improves held-out yield prediction. It is a plausible algorithmic contributor, **not demonstrated to cause** the CMC difference.

At budget 6, the yield- and ee-trained uncertainty–diversity selections share on average 2.52 of four newly acquired substrates in P7 and 2.98 of four in CMC. This shows partial overlap despite different endpoint labels, but neither proves that structural novelty caused the yield result nor isolates the disagreement term. In CMC the candidate pool contains only 21 training candidates per split; overlap near budget 20 is mechanically inflated, so it is not interpreted as independent evidence.

Yield spans 21–99% (median 93.5%; IQR 72–97%) for P7 and 30–99% (median 75.5%; IQR 63.5–87.75%) for CMC. Descriptive Spearman correlations of ee magnitude with yield are 0.40 and 0.47, respectively, in the curated active populations. These summaries do not establish why one endpoint is more predictable; 38 and 26 reported outcomes cannot resolve a chemical mechanism. Isolated yield may be influenced by productive conversion, competing pathways, and isolation, but those components were not measured here. No diagnostic demonstrates which chemical factor dominates, and no calibrated held-out uncertainty analysis or mechanistic experiment is available. No policy or weight is selected after seeing these data.

Per-budget held-out yield MAE, source / uncertainty–diversity / random: P7 at budget 6 is 20.08 / 15.00 / 19.46, and at 20 is 17.78 / 16.83 / 18.39; CMC at budget 6 is 25.01 / 23.62 / 23.65, and at 20 is 21.50 / 21.97 / 21.83. These patterns illustrate dependence on budget and starting/test set, not a trajectory-wide mechanistic explanation.

## Validation and system changes

`yield_common_test.py` and `results/` contain yield predictions, selection paths, selected score components, split summaries, seeds and source hashes. `validate_and_diagnose.py` independently checked all 16,500 yield prediction errors, 600 selection sequences and 2,160 score rows, verified matching source/random paths across endpoints, and refitted 1,650 Ridge predictions; details are in `validation_report.txt`. Source data and production code were not changed. Source outcome provenance is retained in the original ledgers; the new code does not establish independently verified source outcomes. Before submission include these new results and the corrected comment-5 metadata in the released data package.

Writing was updated to report both outcomes, expose the novelty overlap and distinguish hypotheses from observations. The discussion and conclusions no longer imply a consistent yield benefit. The revised SI specifies split design, all key numbers, diagnostics and limitations.
