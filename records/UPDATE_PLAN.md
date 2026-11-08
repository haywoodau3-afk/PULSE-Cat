# Correction status and remaining work

Status: corrected results and manuscript/SI updates are complete for the analyses retained in this revision. The point-by-point response remains a working draft for author review; final journal file assembly and public data/code deposit are still pending.

## Completed

1. Replaced the positional atom-index assumption with structural nitrene identification and propagated atom mapping in the affected pose-feature path.
2. Preserved the source experimental outcomes and archived pose coordinates; regenerated the affected pose-derived feature records and downstream prediction/acquisition analyses.
3. Rechecked downstream Stage 1-v2/Stage 2-v2/Stage 3a and CREST/GFN2-xTB analyses. Results that were unstable or not supported were qualified or withdrawn rather than carried forward as positive evidence.
4. Updated the manuscript and SI with the corrected numerical results, separate validation protocols, revised limitations, corrected SI numbering, and corrected figures. The previously reported 55.3% and 33.2% route-specific reductions are identified as superseded; corrected replay values are reported with the metric and its limitations.
5. Reconciled the retained manuscript/SI claims with the corrected analysis records and prepared a package manifest.
6. Bundled the 140 source Stage 1 reports and 28,000 saved assembly XYZ files needed to regenerate the affected pose features; verified all 28,140 archive entries against their SHA-256 manifest.
7. Audited the active and frozen source trees, corrected the additional exploratory pose-probability source, and documented the older SI snapshots that remain historical.

## Remaining steps

1. Authors should review the corrected scientific narrative and point-by-point response, including the disclosure that historical pre-correction output records are incomplete for exact bitwise reconstruction.
2. Assemble the final journal submission files and deposit the corrected data/code archive in the repository required by the journal.

## Reproducibility boundary

The corrected release contains the inputs, scripts, outputs, tables, figures, and manifests used for the revision analyses. The original historical run tree does not contain complete metadata and feature records for bitwise reconstruction of every earlier pose-derived calculation. Archived results using the faulty positional assumption are retained as historical provenance only and are not evidence for the corrected manuscript claims. No prospective experiment or independent validation on a new catalyst family is claimed.

## Stage 1-v2 / Stage 3a corrected rerun findings

- The corrected selector retained 600 poses (12 substrate sets × 50). It shares 452/600 selected pose identities with the archived selection; 148 identities changed across 4/12 substrate sets.
- The corrected ee-labelled model cohort contains 11 records, although the pose-selection audit covers all 12 seed sets. This distinction remains explicit in the SI.
- Corrected seed-pilot MAEs (ee points): Stage 2 seed baseline 6.775; Stage 2-v2 selected-pose model 15.201; graph-only Stage 3a-alt 6.886; Stage 3a reference/shell 13.201. This small pilot does not support an accuracy gain from Stage 1-v2 pose filtering or the reference/shell block.
- The prior 12-record seed comparison and prior Stage 3a shell MAE of 21.208 are superseded. The pilot does not establish that these feature classes are generally inferior.
- The corrected nested-family comparison gives MAE/RMSE/R² of 9.801/14.150/0.187 for Stage 2p geometry; 9.834/13.998/0.204 after adding Stage 3a-alt; and 9.653/13.371/0.274 with both Stage 3a-alt and Stage 3b. The Stage 2p + Stage 3b-only model produced extreme out-of-family predictions under the selected low-regularisation setting; it is marked unstable and no performance estimate is reported.
- Corrected CREST/GFN2-xTB family-held-out MAEs are 9.801 (base), 9.348 (+CREST geometry), 8.325 (+GFN2-xTB electronics), and 9.007 (both). Paired substrate-bootstrap intervals include zero for all three augmentations; these point estimates do not establish reliable improvement.
