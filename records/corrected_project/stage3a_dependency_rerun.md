# Corrected Stage 1-v2 / Stage 2-v2 / Stage 3a and CREST reruns

## Stage 1-v2 seed pilot

The Stage 1-v2 selector depends on corrected Stage 2 pose-interaction values and corrected Stage 3a reference geometry. The historical selected-pose set was therefore not carried forward. The new selection is `stage3a_model_comparison_corrected/stage1-v2-pose-selection-corrected.jsonl`; the old selection remains preserved separately.

- Selection coverage: 600 poses across 12 substrate seed sets, 50 selected per set.
- Agreement with archived selection: 452/600 pose identities retained; 148 changed across 4/12 substrate sets.
- Corrected ee model cohort: 11 records. The 12-substrate selection audit and 11-record ee model cohort are distinct and are reported separately.
- Corrected MAE, ee points: Stage 2 seed baseline 6.775; Stage 2-v2 selected-pose model 15.201; graph-only Stage 3a-alt 6.886; Stage 3a reference/shell 13.201.

The old 12-record result, including the Stage 3a shell MAE of 21.208 versus 22.019, is superseded. In this small retrospective pilot, the selected-pose and reference/shell features did not improve the Stage 2 seed baseline. This is not evidence that these feature classes are generally inferior.

## Corrected nested-family Stage 2p / Stage 3a-alt / Stage 3b comparison

The corrected Stage 2p feature rows were joined to graph-only Stage 3a-alt and existing Stage 3b BDE features for the 38 ee-labelled Fe(P7)Cl records. The four model arms are in `stage3a_alt_family/stage3a-alt-plus-stage2p-family-heldout-corrected.json` with per-substrate predictions in the adjacent CSV.

| Feature arm | MAE | RMSE | R² | Interpretation |
|---|---:|---:|---:|---|
| Corrected Stage 2p geometry | 9.801 | 14.150 | 0.187 | Corrected baseline |
| + Stage 3a-alt | 9.834 | 13.998 | 0.204 | Similar MAE; no clear gain |
| + Stage 3b BDE only | Not reported | Not reported | Not reported | Numerically unstable out-of-family predictions; e.g. approximately −66 million ee points for 1l |
| + Stage 3a-alt + Stage 3b | 9.653 | 13.371 | 0.274 | Descriptive improvement on this fixed retrospective cohort |

The Stage 2p + Stage 3b-only arm selects low regularisation for an outer held-out family and extrapolates catastrophically for halogen-containing members 1l and 1m. Its output is retained for audit but is not a meaningful performance estimate. The other rows are still small-sample nested-family evaluations, not independent prospective validation.

## Corrected CREST/GFN2-xTB nested-family comparison

The same corrected Stage 2p base matrix was used with the archived substrate-only CREST geometry and GFN2-xTB feature blocks. The analysis retains the original nested leave-one-family-out Elastic Net procedure. Results and hashes are in `crest_family/corrected_metrics.json`; predictions are in `crest_family/corrected_predictions.csv`; the reproducible builder is `rebuild_crest_family.py`.

| Feature arm | Columns | MAE | RMSE | R² |
|---|---:|---:|---:|---:|
| Corrected Stage 2p geometry | 248 | 9.801 | 14.150 | 0.187 |
| + CREST geometry | 258 | 9.348 | 13.745 | 0.233 |
| + dense GFN2-xTB electronics | 261 | 8.325 | 11.531 | 0.460 |
| + CREST geometry + GFN2-xTB | 271 | 9.007 | 13.486 | 0.261 |

Paired 20,000-draw substrate-bootstrap improvements (baseline absolute error minus augmented absolute error) are:

| Augmentation | Mean improvement | 95% percentile interval | Bootstrap fraction above zero |
|---|---:|---:|---:|
| CREST geometry | 0.453 | [−0.206, 1.568] | 0.779 |
| GFN2-xTB electronics | 1.476 | [−0.234, 3.380] | 0.952 |
| Combined | 0.794 | [−0.518, 2.266] | 0.876 |

All intervals include zero, and the bootstrap resamples substrates rather than chemical families. The point estimates favour the additions, but the analysis does not establish a reliable family-generalisation improvement. The CREST search retained one unique minimum per substrate, so its probability fields contain no ensemble diversity.
