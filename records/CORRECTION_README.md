# Corrected project and manuscript working set

This folder contains the corrected working manuscript, supporting information, and analysis archive following discovery of an atom-index error in nitrene-anchored pose-feature generation. The corrected results now form the basis of the manuscript and SI in this folder. This is an author-review package, not the final journal submission release.

## Error and correction

Some code assumed molecular atom index 0 was the nitrene nitrogen. For valid suffix-style nitrene SMILES, atom 0 can be carbon; assembly can also reorder atoms. In those cases, the code could anchor geometry descriptors to the wrong atom and select the wrong nearby hydrogen. The corrected pipeline identifies the actual nitrene in the assembled molecule before calculating the dependent features. Source structures, experimental ee/yield outcomes, and archived pose coordinates remain unchanged.

## Corrected findings represented in the manuscript and SI

- Feature records changed for 12/38 previously comparable Fe(P7)Cl records and 30/50 Fe(CMC-Por)Cl records. Corrected P7 coverage now contains 40 records: 38 with ee and two additional yield-only records (1ad and 1an).
- The corrected P7 Elastic Net structure-plus-pose MAE is 7.979 versus 12.612 for structure-only in target-held-out validation, and 8.538 versus 10.406 in family-held-out validation. Family-level results remain heterogeneous.
- Corrected shared-start, common-test, weight-sensitivity, factorial, endpoint, substrate-class, and active-learning baseline analyses are recorded in the correction archive and its analysis-run subfolders.
- The independent acquisition progression was rerun with 500 random continuations per endpoint. Its corrected tables and plots are in SI Tables S9–S12 and Figures S5–S6. The separate dedicated mean-prefix route replay uses three random continuations and is a different metric.
- The corrected Stage 1-v2/Stage 2-v2/Stage 3a seed pilot and corrected nested-family CREST/GFN2-xTB ablations are included in the manuscript/SI working set. The seed pilot does not show an improvement from Stage 1-v2 pose filtering or the reference/shell block. CREST/xTB point estimates favour added features, but all paired substrate-bootstrap intervals include zero.
- The corrected Stage 2p + Stage 3b-only family-held-out model generated extreme predictions under its selected low-regularisation setting. It is retained for audit and explicitly marked unstable, without a performance estimate.
- The complete corrected scan of all 13 shared aryl identities ranks 1i/2r first by Jensen–Shannon divergence (0.030961 bits; total variation 0.171882; Bhattacharyya overlap 0.978082). These computed descriptor fields are not conformer populations or mechanistic evidence.

## Remaining steps and limits

The revised manuscript and SI have been reconciled to the corrected outputs retained in this archive. The coordinate inputs needed to independently reconstruct the corrected pose-derived features are included under `corrected_project/input_snapshots/pose_coordinates/`; see its README and SHA-256 manifest. The source-tree audit distinguishes these corrected sources from earlier frozen SI package snapshots. The point-by-point response remains a working draft for author review. The original historical run tree is incomplete for exact bitwise reconstruction of every earlier pose-derived result; those outputs are retained as historical provenance and are not the basis of the corrected claims. The journal's final repository deposit and author approval of the response remain to be completed.

See `UPDATE_PLAN.md`, `ERROR_IMPACT_ANALYSIS.md`, `SOURCE_TREE_AUDIT.md`, `point_by_point_response_corrected_working.md`, and `FULL_PACKAGE_MANIFEST.json`.
