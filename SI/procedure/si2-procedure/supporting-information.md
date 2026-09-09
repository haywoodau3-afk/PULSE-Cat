# Supporting information draft

**Scope.** This draft supports the retrospective computational manuscript for
the Fe(P7)Cl (P7) and CMC-Por-FeCl (CMC-Por) systems. It covers the curated
reaction records, structure and pose representations, independent and
progressive learning analyses, reciprocal guarded transfer, and the
prediction-only substrate-generation branch. Large XYZ coordinate caches are
intentionally excluded at this stage; the compact pose-derived feature and SVG
artifacts remain referenced.

## S1. Study design and data boundaries

The study uses two independently curated iron-porphyrin domains under their
respective fixed reaction conditions. P7 contains 41 retained records (39
progression records and 38 usable ee labels after the documented exclusions).
CMC-Por contains 50 records: 33 aryl records in the primary transfer domain and
17 sulfonyl records retained as a pathway control. The reciprocal aryl transfer
analysis has 13 canonical substrate pairs; overlapping canonical compounds are
excluded from cold-start transfer fits.

All reported outcomes are retrospective and label-masked. Generated
substrates have predicted values only. No generated ee/yield value, supplier
availability, route feasibility, safety assessment, or prospective laboratory
result is included in this SI.

## S2. Representations and feature versions

The frozen representation ladder is:

| Arm | Contents | Role |
|---|---|---|
| B0 | Training-fold mean | No-feature reference |
| B1 | Six chemist-readable RDKit scalars | Minimal 2D baseline |
| B2 | Fifteen RDKit scalars | Descriptor baseline |
| B3 | B2 + 128-bit radius-2 Morgan | Reduced fingerprint |
| B4 | B2 + 256-bit radius-2 Morgan | Dimension-matched 2D control |
| B5 | B2 + 1,024-bit radius-2 Morgan | Full 2D reference |
| P0 | 248-column Stage 2p pose block | Pose-only diagnostic |
| P1 | B1 + P0 | Minimal 2D plus pose |
| P2 | B5 + raw P0 | Legacy pose diagnostic |
| P3 | B5 + compact 44-feature C1 geometry | Compact pose upgrade |
| P4 | B5 + C1 + 16-feature catalyst-interaction C2 block | Transfer-specific pose tier |

Stage 2p features are substrate-only, reaction-axis anchored, and derived from
UFF-ranked pose ensembles. Stage 2pp adds persistent atomic-occupancy and
reaction-corridor flexibility summaries (655 columns). Occupancy fields are
geometric summaries, not electron density.

## S3. Independent and progressive learning curves

Figure S1 shows the independent P7 and CMC-Por aryl progression curves for the
five route policies (historical order, uncertainty + diversity, diversity
first, performance first, and a 500-replicate random control). Figure S2 holds
the uncertainty + diversity route fixed and compares Ridge, Elastic Net, and
Tanimoto-kNN estimators. Figure S4 shows the reciprocal progressive transfer
curves for B5, P3, and P4.

![Figure S1. Independent progressive learning curves](supporting-information/figures/si_fig1_independent_learning_curves.svg)

![Figure S2. Independent estimator variants](supporting-information/figures/si_fig2_model_variant_curves.svg)

![Figure S3. Guarded transfer across representation versions](supporting-information/figures/si_fig3_representation_version_bars.svg)

![Figure S4. Reciprocal progressive transfer curves](supporting-information/figures/si_fig4_progressive_transfer_curves.svg)

The historical-versus-AI route summary reports the best uncertainty–diversity
route as lower mean prefix MAE than historical order in both domains (P7:
21.672 versus 9.684 ee points; CMC-Por aryl: 13.155 versus 8.787). These are
retrospective learning-efficiency results, not evidence that the generator
improves experimental enantioselectivity.

The complete experiment inventory, frozen feature-arm definitions, reciprocal
representation progression, independent estimator progression, and held-out
model comparison are consolidated in
[`si_model_progression_tables.md`](supporting-information/tables/si_model_progression_tables.md).
The corresponding machine-readable tables are
[`si_experiment_inventory.csv`](supporting-information/tables/si_experiment_inventory.csv),
[`si_feature_arm_definitions.csv`](supporting-information/tables/si_feature_arm_definitions.csv),
[`si_representation_progression_ee.csv`](supporting-information/tables/si_representation_progression_ee.csv),
[`si_independent_progressive_model_metrics.csv`](supporting-information/tables/si_independent_progressive_model_metrics.csv),
and [`si_holdout_model_comparison_ee.csv`](supporting-information/tables/si_holdout_model_comparison_ee.csv).

## S4. Pose overlays and compact geometry artifacts

The Stage 2pp overlay index contains all 13 canonical aryl pairs. Each SVG
shows the numerical occupancy fields for the top-UFF and bottom-UFF strata and
their difference in the reaction-centred frame. Figure S5 gives representative
matched overlays for an alkyl-chain pair, a methoxy-substituted pair, and a
fused heteroaryl pair.

![Figure S5. Representative P7/CMC-Por pose overlays](supporting-information/figures/si_fig5_pose_overlay_montage.svg)

The full per-substrate SVG views are listed in
[`si_pose_overlay_index.csv`](supporting-information/tables/si_pose_overlay_index.csv).
The corresponding numerical density arrays (`.npz`) and all XYZ coordinate
caches remain in the data tree but are not copied into this SI draft.

## S5. Starting-material and product SMILES

The machine-readable table
[`si_substrate_smiles.csv`](supporting-information/tables/si_substrate_smiles.csv)
contains all 91 curated P7 and CMC-Por records. It includes the recorded
starting aryl-azide SMILES, free-nitrene SMILES, product SMILES where present,
canonicalized counterparts, reported ee/yield, reaction-centre site, source
location, and the 13-pair canonical-overlap annotation.

Product structures are complete for the 50 CMC-Por records. Twenty-nine P7
records have a null product mapping in the curated source record; these entries
are explicitly marked `missing_in_curated_record` rather than reconstructed or
imputed. The starting-material strings are retained for every record.

## S6. Generated data inventory

| Data product | Contents | Location |
|---|---|---|
| Curated reaction records | 41 P7 + 50 CMC-Por JSONL records | `data/jacs_2025/stage2/curated-reaction-records.jsonl`; `data/expansion/catalyst_rerun/cmcpor/stage2-records.jsonl` |
| Independent learning curves | Per-prefix MAE, RMSE, Spearman summaries and full rows | `data/jacs_2025/scope_progression/`; `data/expansion/catalyst_rerun/cmcpor_aryl_scope_progression/` |
| Pose features | Stage 2p (248 columns; 41 P7 + 50 CMC-Por rows) and Stage 2pp (655 columns; 41 P7 + 50 CMC-Por rows) | `data/jacs_2025/stage2*/features/`; `data/expansion/catalyst_rerun/cmcpor_uff_full/stage2*/features/` |
| Pose density views | 41 P7 and 50 CMC-Por `.npz` arrays with matching SVG views (91 per-substrate views total) | `data/jacs_2025/stage2pp/`; `data/expansion/catalyst_rerun/cmcpor_uff_full/stage2pp/` |
| Representation matrices | B1–B5, P0–P4, and B5/P3/P4 reciprocal transfer results | `data/expansion/pptl/bidirectional-ee-2d-matrix.json`; `data/expansion/pptl/bidirectional-ee-pose-matrix.json`; `data/expansion/pptl/matrix-ee-b5-p3-p4.json` |
| Progressive route replicates | 500-route EE/yield replicates and bootstrap intervals | `data/expansion/pptl/routes/` |
| Historical-versus-AI comparison | Route ranks, prefix MAE, AUC-MAE, and threshold diagnostics | `data/expansion/pptl/historical-vs-ai-progressive-comparison.json` |
| Candidate generation | 50,560 raw strings (10,112 per fixed seed), funnel outputs, and equal-budget enumeration comparator | `data/expansion/pptl/raw-production.jsonl`; `data/expansion/pptl/funnel-production-ad.csv`; `data/expansion/pptl/raw-enumeration.jsonl`; `data/expansion/pptl/funnel-enumeration-ad.csv` |
| Proposal panel | Sealed 8+8 computational proposal panel with predicted ee and no revealed outcomes | `data/expansion/pptl/sealed-prospective-panel.csv`; `data/expansion/pptl/sealed-prospective-panel-lock.json` |

The generator funnel contains 563 contract-valid candidates, of which 483 are
inside the frozen applicability domain. The equal-budget enumeration comparator
contains 18,545 contract-valid candidates, of which 18,350 are inside the
applicability domain. Both candidate pools are prediction-only. The original
requested generator budget was 50,000; the complete 50,560-row persisted output
and the matching 50,560-row deterministic comparator are the frozen records.

## S7. Reproducibility and claim boundary

The SI figures and tables are regenerated with:

```text
.venv/bin/python scripts/pptl/build_supporting_information.py
```

The script reads the frozen artifacts and does not load XYZ files. The
checkpoint scope, lock digest, exclusions, and D4-Por deferral are recorded in
[`checkpoint-1-9-manuscript-freeze.md`](checkpoint-1-9-manuscript-freeze.md).

The safe manuscript interpretation is that uncertainty–diversity ordering
improves retrospective learning efficiency, while pose-containing arms provide
directional and conditional transfer evidence. The prespecified 10% AUC
superiority gate remains unresolved, and no prospective chemistry claim should
be made from the generated panel.
