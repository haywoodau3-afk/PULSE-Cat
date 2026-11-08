# Reviewer 1 comment 7: benchmark findings and adjustments

## Design

Three specified active-learning baselines were compared against the existing uncertainty–diversity (PULSE) route using the same 20 overlapping common-test splits, three initial pairs per split, candidate pools, five budgets (2/6/10/15/20), and held-out ee substrates. The Fe(CMC-Por)Cl cohort is aryl-only and its seven locked audit records were excluded. Prediction error for every route uses the same 1,287-field Ridge model; query by committee (QBC) uses Ridge, Elastic Net and Tanimoto-kNN predictive standard deviation, while expected improvement (EI) and Thompson sampling (TS) use an outcome-standardised Gaussian process on the Morgan/Tanimoto kernel with fixed diagonal noise 0.05. TS uses a correlated joint posterior sample over all candidates, averaged across three seeded runs per pair. The pre-existing PULSE, source-order and random paths/predictions were reused. Three random continuations were averaged. All selection decisions used revealed ee only.

The source-order and random comparators are reproduced from prior revisions. QBC shares the committee disagreement component already present in PULSE's uncertainty term; it is thus also an informative ablation rather than an unrelated committee. EI and TS aim to maximise |ee|, not minimise prediction error, and use a different acquisition surrogate from PULSE; they are assessed on both prediction error and best observed |ee|. This is a comparison of specific fixed implementations, not an exhaustive tuning of any method. An established method name does not imply its implementation is state of the art.

## Common-test prediction results

Mean absolute errors in ee percentage points, averaging five budgets and three starts per split, then 20 splits. Lower is better. PULSE versus QBC counts are 8/20 versus 12/20 in each system; against EI 7/20 versus 13/20 for P7 and 15/20 versus 5/20 for CMC; against TS 11/20 versus 9/20 for P7 and 14/20 versus 6/20 for CMC.

| Acquisition | Fe(P7)Cl | Fe(CMC-Por)Cl aryl |
|---|---:|---:|
| PULSE uncertainty–diversity | 13.88 | 14.27 |
| Query by committee | 13.22 | 13.99 |
| Expected improvement | 13.56 | 15.15 |
| Thompson sampling | 14.27 | 15.65 |
| Source order | 16.72 | 15.70 |
| Random | 14.25 | 15.33 |

For QBC-minus-PULSE the mean/median paired differences are −0.65/−0.55 P7 and −0.27/−0.46 CMC; PULSE has higher mean error than QBC in both. EI-minus-PULSE is −0.32/−0.36 for P7 and +0.89/+0.23 for CMC. TS-minus-PULSE is +0.39/+0.30 and +1.39/+0.81, respectively. These differences are descriptive and vary across overlapping splits, not independent-dataset significance tests. Mean scores include budget 2, at which all routes are identical, and comparisons should not be equated with the original remaining-pool 55.3% and 33.2%.

## Goal-aligned optimisation results

At six labelled substrates, average best observed |ee| (source / PULSE / random / QBC / EI / TS) was 92.83 / 93.53 / 93.41 / 93.48 / 93.38 / 93.65 for P7 and 87.83 / 84.92 / 87.01 / 86.72 / 85.37 / 86.73 for CMC. At 20 labels, values converge near the maximum because a substantial fraction of each small candidate pool has been observed. The figure of merit and ordering can differ from the common-test error ranking. These are retrospective best values in the available pool, not laboratory effort or an unbiased measure of finding unreported chemistry.

## Interpretation and limitations

PULSE is not the best of all compared methods: QBC has lower mean common-test error in both datasets, and EI is lower in P7. The results do not demonstrate PULSE is state of the art or superior to all baselines. Fixed GP kernel/noise, three TS replicates, Ridge-only evaluation, small chemically related reported datasets, shared overlapping splits, and lack of prospective experiments limit inference. PULSE and QBC share committee models and are not independent techniques. The GP is an acquisition surrogate using fingerprint features while final evaluation uses the same Ridge features for all routes; this is a deliberate standardised assessment of selection policies, not a model-to-model contest. Full methods, predictions, seeds, selections, scores, input hashes and software versions are in `results/` and `benchmark.py`; `validation_report.txt` reports independent error checks, 1,650 Ridge prediction refits and independent score/first-decision checks on 60 trajectories, including a separate GP linear solve.

## Adjustments

- Report QBC, EI and TS comparison and their distinct aims in the manuscript and SI, including the unfavourable results and uncertainty.
- Remove or qualify broad superiority/competitive state-of-the-art claims; retain earlier comparisons as the original restricted baselines and metrics.
- Keep original production code/data unchanged, save new scripts and outputs, and include them in the submission data release along with the pending comment 5 corrections.
