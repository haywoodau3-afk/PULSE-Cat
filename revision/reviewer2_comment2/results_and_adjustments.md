# Reviewer 2 comment 2: findings and adjustments

**Status: provisional; not ready for submission or closeout.** The two examples are prepared and the requested interpretation is drafted, but the descriptor error discovered during verification affects earlier analyses and requires complete regeneration and independent review. The manuscript, supporting information, prior reviewer closeouts and companion package must be reconciled before submission. See [critical issue](CRITICAL_FEATURE_ISSUE.md).

## The examples

The source Fe(P7)Cl study reports substrate 1a giving product 2a at 92% ee and 1ah giving 2ah at 50% ee under its 60 °C conditions. The substrates share the aryl azide and initial two-carbon tether; the carbon forming the stereocentre bears phenyl in 1a and ethyl in 1ah. This comparison changes several properties simultaneously and cannot establish a steric or conformational cause of the ee difference.

The figure displays the starting azide in 2D and the lowest-scoring retained UFF iron-bound nitrene assembly in 3D. Both examples use a common frozen catalyst core. Single generated geometries are neither established transition states nor measured conformer populations. Reusable molecular files, SVG drawings, original coordinates, figure and provenance appear in `results/`; `.mol` files can be opened in chemical drawing software, but are not native ChemDraw files. See `example_audit.json` for original source paths and hashes. **Its pose prediction fields preserve archived pre-correction values**, and must not be mistaken for corrected results. Corrected values are in `corrected_example_details.json` and `corrected_pose_elasticnet_predictions.csv`.

## Predictions and descriptor interpretation

| Substrate | Observed ee (%) | Structure-only held-out prediction (%) | Corrected structure-plus-pose held-out prediction (%) | Mean centroid–Fe (Å) | Mean nitrene N–reactive C (Å) |
|---|---:|---:|---:|---:|---:|
| 1a | 92 | 81.0 | 90.2 | 4.515 | 3.460 |
| 1ah | 50 | 73.2 | 58.7 | 3.869 | 3.582 |

Each prediction is from its own target-held-out Elastic Net fit; these two cases are illustrative and not independent validation. The descriptor means are calculated over 200 retained poses, not the single poses shown. The centroid distance is influenced by size and composition. Both descriptors have coefficient zero in both example-specific target-held-out models and family-held-out models, so their differences do not directly contribute to those fitted predictions. Other descriptors can contribute; no mechanistic attribution is established.

## Critical correction and remaining work

The original feature code treated atom index 0 as nitrene nitrogen for certain calculations, but in suffix-style nitrene SMILES index 0 can be carbon. Direct calculation from archived coordinates gives 3.58151 Å for 1ah nitrene-N–reactive-C instead of the archived 2.53855 Å. The shared mapping was corrected in the relevant feature-generation scripts and verified with atom-mapping tests; affected raw archived inputs were preserved. Corrected pose representations were regenerated for both datasets, and several reviewer analyses were re-run. These outputs remain provisional until independently verified, including dependent descriptors and earlier figures, predictions, all analyses and package documentation. The original benchmark also performed global label-blind constant-feature filtering before splitting; manuscript wording was corrected. A training-only filtering check reproduces all 76 corrected held-out Elastic Net predictions with already selected hyperparameters to numerical precision; it does not verify model selection or other estimators.

## Writing and system adjustments

- The provisional manuscript adds a highlighted illustration, predictions, specific descriptor caveats, and a source-aware chemical discussion; the SI documents methods, feature definitions, preprocessing and provenance.
- The source feature code now identifies the actual nitrene atom rather than assuming index 0; a regression test covers the suffix-style case. Corrected output and analysis scripts are retained in this folder.
- Both DOCX files carry a prominent do-not-submit warning. Their original pose-dependent numerical results and previous responses have not all been replaced or validated. The staged companion package carries the same block and has not been represented as a corrected release.
- Before closeout: finish and independently verify all impacted workflows, reconcile manuscript and SI figures/tables and previous reviewer responses, regenerate the release package, render and inspect final documents, then assess whether the figure and response address the reviewer without overstating causal insight.
