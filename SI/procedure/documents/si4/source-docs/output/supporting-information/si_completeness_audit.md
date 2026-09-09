# Supporting-information completeness audit

Audit date: 2026-09-04  
Scope: frozen manuscript checkpoints 1–9 for Fe(P7)Cl and CMC-Por-FeCl.

## Audit conclusion

All nine frozen checkpoints have a manuscript description, a consolidated
table or figure where applicable, and file-level supporting data in
`raw-data/`. The raw deposit contains record-level inputs, full learning-curve
rows, model predictions and metrics, pose-derived numerical arrays, transfer
replicates, generator streams, and frozen proposal ledgers—not only the
publication summaries.

The only scientific data layer intentionally absent from the output package is
the XYZ coordinate cache, which was deferred by instruction. Missing product
SMILES for 29 P7 records are a source-data limitation and remain explicit nulls;
they were not imputed. Checkpoint 10 (validation on an unseen third porphyrin)
has no D4-Por labels or geometry and is correctly excluded from the freeze.

## Checkpoint-to-evidence matrix

| Checkpoint | SI detail | Consolidated evidence | Raw-data location | Status / boundary |
|---:|---|---|---|---|
| 1. Two independent iron-porphyrin systems | S1, S5, S6 | Table S1; substrate SMILES table | `raw-data/01_curated_records_and_source_provenance/` | Complete for P7 (41) and CMC-Por (50) |
| 2. RDKit + Morgan representation | S2, S3 | Tables S2–S5; Figures S2–S3 | `raw-data/03_structure_pose_features_and_model_benchmarks/`; `raw-data/05_transfer_learning_and_progressive_routes/` | B0–B5 definitions and results present |
| 3. Pose information | S2, S4 | Tables S2, S3, S5; Figure S5 | `raw-data/03_structure_pose_features_and_model_benchmarks/`; `raw-data/04_pose_density_arrays_and_overlays/` | Stage 2p/2pp features and arrays present; XYZ deferred |
| 4. Structure-versus-pose comparison | S3, S7 | Tables S3 and S5; Figure S3 | `raw-data/03_structure_pose_features_and_model_benchmarks/`; `raw-data/05_transfer_learning_and_progressive_routes/` | Complete; advantage is estimator/split dependent |
| 5. Pose-overlay density | S4 | Pose-overlay index; Figure S5 | `raw-data/04_pose_density_arrays_and_overlays/` | Numerical NPZ arrays and all SVG views included |
| 6. Progressive substrate-feature learning | S3 | Table S4; Figures S1–S2 | `raw-data/02_independent_progressive_learning/` | Full prefix rows, events, features, and policies included |
| 7. Progressive convergence | S3 | Table S4; Figures S1, S2, S4 | `raw-data/02_independent_progressive_learning/`; `raw-data/05_transfer_learning_and_progressive_routes/` | AUC-MAE, n90, routes, and bootstrap data included |
| 8. Gated transfer between systems | S3, S7 | Table S3; Figures S3–S4 | `raw-data/05_transfer_learning_and_progressive_routes/` | Complete for reciprocal P7/CMC-Por; 10% AUC gate unresolved |
| 9. Generative substrate search | S6, S7 | Table S1; sealed proposal panel | `raw-data/06_generative_substrate_search/`; `raw-data/07_proposed_scope_and_frozen_ledgers/` | Complete as prediction-only data; no experimental validation claim |

## Data-detail checklist

| Required item | Location | Audit result |
|---|---|---|
| Experiments performed and interpretation | `tables/si_experiment_inventory.csv` and `.xlsx` | Present (9 experiments/checkpoints) |
| RDKit → Morgan → pose progression | `tables/si_feature_arm_definitions.csv`; `tables/si_representation_progression_ee.csv` | Present (B0–B5, P0–P4; both directions) |
| Independent and progressive model variants | `tables/si_independent_progressive_model_metrics.csv`; raw category 02 | Present (routes, Ridge, Elastic Net, Tanimoto-kNN, random controls) |
| Independent held-out prediction comparison | `tables/si_holdout_model_comparison_ee.csv`; raw category 03 | Present (target/family holdouts and four estimators) |
| Starting and product SMILES | `tables/si_substrate_smiles.csv`; raw category 01 | Present; 29 P7 product mappings explicitly missing in source |
| Learning-curve graphics | `figures/si_fig1*`, `si_fig2*`, `si_fig4*` | Present |
| Representation comparison graphic | `figures/si_fig3*` | Present |
| Pose overlays | `figures/si_fig5*`; `tables/si_pose_overlay_index.csv`; raw category 04 | Present; 91 per-substrate numerical/view records retained |
| Raw generator and comparator outputs | raw category 06 | Present (50,560 + 50,560 rows) |
| Provenance and checksums | `si_data_manifest.json`; `raw-data/raw-data-manifest.{csv,json}` | Present at publication-artifact and file level |

## Known limitations to retain in the manuscript

1. Pose-containing models do not outperform structure-only models for every
   estimator, split, direction, or representation. Claims must remain
   directional and conditional.
2. The progressive and transfer analyses are retrospective and label-masked;
   they are not prospective experimental validation.
3. Generated candidates have predictions only. Availability, synthetic
   feasibility, safety, ee, and yield have not been experimentally verified.
4. D4-Por or another third unseen catalyst system is checkpoint 10 and remains
   outside this package.

