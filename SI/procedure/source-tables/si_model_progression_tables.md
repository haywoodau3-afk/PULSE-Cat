# SI model and experiment progression tables

These tables are reshaped from persisted, label-masked artifacts. Lower MAE/AUC-MAE is better; a negative MAE delta indicates improvement versus the stated reference. The reciprocal ladder uses Ridge target-only and guarded prefix replay; the independent estimator table retains Ridge, Elastic Net, and Tanimoto-kNN separately.

## Table S1. Experiment inventory

| ID | Experiment | Question | Cohort / direction | Target | Features / models | Evaluation / control | Persisted output | Interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E1 | Domain curation and lock | Are the two iron-porphyrin systems independently defined and auditable? | P7 (41 records); CMC-Por (50 records; 33 aryl + 17 sulfonyl) | ee and isolated yield | Curated SMILES, reaction metadata, Stage 2 pose records | Record-level exclusions; 13 canonical aryl overlaps reconciled | data/jacs_2025/stage2/curated-reaction-records.jsonl; data/expansion/catalyst_rerun/cmcpor/stage2-records.jsonl | Frozen input domains; not a universal catalyst model |
| E2 | 2D representation ladder | How does prediction change from minimal RDKit descriptors to Morgan fingerprints? | CMC-Por → P7 and P7 → CMC-Por aryl | ee | B0–B5; Ridge primary | Target-only and guarded prefix replay; canonical overlaps excluded from transfer | data/expansion/pptl/bidirectional-ee-2d-matrix.json | B5 is the frozen 2D reference; B3–B5 show fingerprint sensitivity |
| E3 | Pose representation ladder | Does pose information add predictive signal beyond structure? | CMC-Por → P7 and P7 → CMC-Por aryl | ee | P0–P4; Ridge primary | Pose-only, raw-pose, compact C1, and catalyst-aware C2 tiers | data/expansion/pptl/bidirectional-ee-pose-matrix.json; data/expansion/pptl/matrix-ee-b5-p3-p4.json | P3/P4 are conditional transfer tiers; universal superiority gate unresolved |
| E4 | Independent progressive learning curves | How quickly does error fall as labelled substrates are added? | P7 and CMC-Por aryl independently | ee and isolated yield | RDKit + 1,024-bit Morgan + raw Stage 2p; Ridge primary | Historical, uncertainty–diversity, diversity-first, performance-first, and 500-route random policies | data/jacs_2025/scope_progression/; data/expansion/catalyst_rerun/cmcpor_aryl_scope_progression/ | Retrospective learning-efficiency experiment |
| E5 | Estimator variants | Is the progressive result robust to estimator choice? | P7 and CMC-Por aryl | ee and isolated yield | Ridge, Elastic Net, Tanimoto-kNN | Same feature set and acquisition routes; AUC-MAE and n90 recorded | learning-curve-summary.csv; scope-progression-manifest.json | Estimator-dependent curves are reported separately |
| E6 | Independent held-out benchmark | Do pose-aware models improve held-out substrate prediction? | P7 target-holdout and family-holdout | ee | Structure-only vs structure + pose; Ridge, Elastic Net, LightGBM, Gaussian Process | Nested/structured holdouts with bootstrap intervals | data/jacs_2025/stage2/reports/*structure*ee-model-benchmark.json | Pose gain is model/split dependent; report intervals |
| E7 | Pose upgrade and controls | Can compact/catalyst-aware pose features retain B5 signal and avoid dimension artifacts? | Reciprocal P7/CMC-Por aryl | ee and isolated yield | B5, P2, P3, P4 | Equal-dimensional random and substrate-permuted compact-pose controls; paired bootstrap | data/expansion/pptl/pose-upgrade-ee.json; data/expansion/pptl/pose-controls-ee.json | P3/P4 are mechanistic/conditional tiers, not universal wins |
| E8 | Guarded transfer and convergence | Can source-domain knowledge be used without negative transfer? | Bidirectional P7 ↔ CMC-Por | ee and isolated yield | B5/P3/P4 guarded ensembles | Prequential source weighting, AUC-MAE, n90, scaffold bootstrap | data/expansion/pptl/matrix-ee-b5-p3-p4.json; data/expansion/pptl/routes/; data/expansion/pptl/scaffold/ | Guarding improves matched error directionally; 10% AUC gate unresolved |
| E9 | Prediction-only substrate generation | Can the frozen workflow propose candidates for scope expansion? | P7/CMC-Por-informed candidate panel | Predicted ee/yield only | SMILES-RNN + PromptSMILES; deterministic enumeration comparator | Contract validation, applicability-domain funnel, sealed proposal panel | data/expansion/pptl/raw-production.jsonl; funnel-production-ad.csv; sealed-prospective-panel.csv | No experimental outcome, availability, safety, or feasibility claim |

## Table S2. Frozen feature-arm definitions

| Arm | Family | Definition | Features | Role | Pose dependency | Status |
| --- | --- | --- | --- | --- | --- | --- |
| B0 | reference | Training-fold mean (no features) | 0 | No-feature reference | none | diagnostic |
| B1 | RDKit descriptors | Six chemist-readable RDKit descriptors | 6 | Minimal 2D baseline | none | frozen |
| B2 | RDKit descriptors | Fifteen RDKit descriptors | 15 | Descriptor baseline | none | frozen |
| B3 | RDKit + Morgan | B2 + 128-bit radius-2 Morgan fingerprint | 143 | Reduced fingerprint | none | frozen |
| B4 | RDKit + Morgan | B2 + 256-bit radius-2 Morgan fingerprint | 271 | Dimension-matched 2D control | none | frozen |
| B5 | RDKit + Morgan | B2 + 1,024-bit radius-2 Morgan fingerprint | 1039 | Full 2D reference | none | primary 2D reference |
| P0 | pose-only | Stage 2p pose block | 248 | Pose-only diagnostic | Stage 2p required | diagnostic |
| P1 | RDKit + pose | B1 + Stage 2p pose block | 254 | Minimal 2D plus pose | Stage 2p required | diagnostic |
| P2 | RDKit + Morgan + pose | B5 + raw Stage 2p pose block | 1287 | Legacy raw-pose diagnostic | Stage 2p required | diagnostic |
| P3 | RDKit + Morgan + compact pose | B5 + compact C1 geometry block | 1083 | Compact pose upgrade | Stage 2p required | conditional transfer tier |
| P4 | RDKit + Morgan + catalyst-aware pose | B5 + C1 geometry + 16-feature C2 catalyst interaction block | 1099 | Transfer-specific pose tier | Stage 2p and catalyst features required | conditional transfer tier |

## Table S3. Reciprocal EE representation progression

| Arm | Direction | Features | Target records | Scored n | Target-only MAE | Target-only AUC-MAE | Guarded MAE | Δ MAE vs prior | % vs B1 | Guarded − target-only |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B1 | cmcpor_to_p7_aryl | 6 | 40 | 37 | 12.895 | 470.723 | 12.802 | NA | 0.000 | -0.092 |
| B2 | cmcpor_to_p7_aryl | 15 | 40 | 37 | 12.714 | 466.054 | 12.529 | -0.180 | 1.398 | -0.185 |
| B3 | cmcpor_to_p7_aryl | 143 | 40 | 37 | 11.941 | 436.753 | 11.612 | -0.773 | 7.392 | -0.329 |
| B4 | cmcpor_to_p7_aryl | 271 | 40 | 37 | 12.165 | 435.505 | 11.964 | 0.224 | 5.656 | -0.201 |
| B5 | cmcpor_to_p7_aryl | 1039 | 40 | 37 | 11.815 | 424.292 | 11.654 | -0.350 | 8.370 | -0.162 |
| P0 | cmcpor_to_p7_aryl | 248 | 40 | 37 | 19.317 | 695.948 | 16.528 | 7.501 | -49.803 | -2.789 |
| P1 | cmcpor_to_p7_aryl | 254 | 40 | 37 | 19.355 | 697.280 | 16.425 | 0.039 | -50.103 | -2.930 |
| P2 | cmcpor_to_p7_aryl | 1287 | 40 | 37 | 16.953 | 606.210 | 14.457 | -2.402 | -31.475 | -2.496 |
| P3 | cmcpor_to_p7_aryl | 1083 | 40 | 37 | 11.276 | 397.809 | 10.973 | -5.677 | 12.555 | -0.303 |
| P4 | cmcpor_to_p7_aryl | 1099 | 40 | 37 | 11.061 | 390.619 | 10.741 | -0.215 | 14.219 | -0.320 |
| B1 | p7_to_cmcpor_aryl | 6 | 33 | 31 | 14.243 | 430.423 | 13.053 | NA | 0.000 | -1.190 |
| B2 | p7_to_cmcpor_aryl | 15 | 33 | 31 | 14.100 | 426.091 | 12.955 | -0.143 | 1.004 | -1.144 |
| B3 | p7_to_cmcpor_aryl | 143 | 33 | 31 | 12.563 | 379.429 | 12.083 | -1.537 | 11.798 | -0.480 |
| B4 | p7_to_cmcpor_aryl | 271 | 33 | 31 | 12.578 | 378.166 | 11.781 | 0.015 | 11.691 | -0.797 |
| B5 | p7_to_cmcpor_aryl | 1039 | 33 | 31 | 12.234 | 372.493 | 11.702 | -0.344 | 14.106 | -0.532 |
| P0 | p7_to_cmcpor_aryl | 248 | 33 | 31 | 18.326 | 551.216 | 15.578 | 6.092 | -28.668 | -2.748 |
| P1 | p7_to_cmcpor_aryl | 254 | 33 | 31 | 20.412 | 612.226 | 18.015 | 2.085 | -43.309 | -2.397 |
| P2 | p7_to_cmcpor_aryl | 1287 | 33 | 31 | 17.659 | 533.867 | 14.239 | -2.752 | -23.987 | -3.420 |
| P3 | p7_to_cmcpor_aryl | 1083 | 33 | 31 | 12.205 | 373.801 | 11.480 | -5.454 | 14.307 | -0.725 |
| P4 | p7_to_cmcpor_aryl | 1099 | 33 | 31 | 12.208 | 373.214 | 11.509 | 0.003 | 14.286 | -0.699 |

## Table S4. Independent progressive estimator metrics

| Domain | Target | Route | Model | Final n | Final-prefix MAE | AUC-MAE | n90 | Reference MAE | Δ vs reference |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P7 | ee_percent | diversity_first | elastic_net | 37 | 4.454 | 343.044 | 4 | 13.238 | -8.785 |
| P7 | ee_percent | diversity_first | ridge | 37 | 3.772 | 391.662 | 24 | 13.238 | -9.466 |
| P7 | ee_percent | diversity_first | tanimoto_knn | 37 | 1.215 | 368.284 | 19 | 13.238 | -12.024 |
| P7 | ee_percent | historical_order | elastic_net | 37 | 8.838 | 741.152 | NA | 13.238 | -4.400 |
| P7 | ee_percent | historical_order | ridge | 37 | 9.719 | 757.662 | NA | 13.238 | -3.519 |
| P7 | ee_percent | historical_order | tanimoto_knn | 37 | 3.969 | 601.044 | 37 | 13.238 | -9.269 |
| P7 | ee_percent | performance_first | elastic_net | 37 | 16.511 | 403.781 | NA | 13.238 | 3.273 |
| P7 | ee_percent | performance_first | ridge | 37 | 18.224 | 403.093 | 7 | 13.238 | 4.986 |
| P7 | ee_percent | performance_first | tanimoto_knn | 37 | 27.543 | 525.131 | NA | 13.238 | 14.304 |
| P7 | ee_percent | random | ridge | 37 | 8.122 | 355.527 | 29 | 13.238 | -5.116 |
| P7 | ee_percent | random | tanimoto_knn | 37 | 8.344 | 337.493 | 27 | 13.238 | -4.894 |
| P7 | ee_percent | uncertainty_diversity | elastic_net | 37 | 4.454 | 325.119 | 16 | 13.238 | -8.785 |
| P7 | ee_percent | uncertainty_diversity | ridge | 37 | 3.772 | 337.181 | 16 | 13.238 | -9.466 |
| P7 | ee_percent | uncertainty_diversity | tanimoto_knn | 37 | 1.215 | 306.116 | 17 | 13.238 | -12.024 |
| P7 | isolated_yield_percent | diversity_first | elastic_net | 38 | 15.999 | 561.248 | 2 | 14.742 | 1.258 |
| P7 | isolated_yield_percent | diversity_first | ridge | 38 | 16.006 | 570.357 | 2 | 14.742 | 1.265 |
| P7 | isolated_yield_percent | diversity_first | tanimoto_knn | 38 | 0.509 | 469.261 | 12 | 14.742 | -14.232 |
| P7 | isolated_yield_percent | historical_order | elastic_net | 38 | 22.180 | 908.899 | 2 | 14.742 | 7.438 |
| P7 | isolated_yield_percent | historical_order | ridge | 38 | 23.917 | 913.166 | 2 | 14.742 | 9.176 |
| P7 | isolated_yield_percent | historical_order | tanimoto_knn | 38 | 16.019 | 633.651 | 37 | 14.742 | 1.278 |
| P7 | isolated_yield_percent | performance_first | elastic_net | 38 | 15.999 | 657.697 | 2 | 14.742 | 1.258 |
| P7 | isolated_yield_percent | performance_first | ridge | 38 | 16.006 | 666.479 | 2 | 14.742 | 1.265 |
| P7 | isolated_yield_percent | performance_first | tanimoto_knn | 38 | 0.509 | 513.326 | 15 | 14.742 | -14.232 |
| P7 | isolated_yield_percent | random | ridge | 38 | 18.447 | 639.424 | 4 | 14.742 | 3.705 |
| P7 | isolated_yield_percent | random | tanimoto_knn | 38 | 13.461 | 484.752 | 26 | 14.742 | -1.281 |
| P7 | isolated_yield_percent | uncertainty_diversity | elastic_net | 38 | 15.999 | 547.182 | 2 | 14.742 | 1.258 |
| P7 | isolated_yield_percent | uncertainty_diversity | ridge | 38 | 16.007 | 554.164 | 2 | 14.742 | 1.265 |
| P7 | isolated_yield_percent | uncertainty_diversity | tanimoto_knn | 38 | 0.509 | 452.942 | 15 | 14.742 | -14.232 |
| CMC-Por aryl | ee_percent | diversity_first | elastic_net | 25 | 4.111 | 217.781 | 13 | 11.580 | -7.469 |
| CMC-Por aryl | ee_percent | diversity_first | ridge | 25 | 4.141 | 221.203 | 14 | 11.580 | -7.439 |
| CMC-Por aryl | ee_percent | diversity_first | tanimoto_knn | 25 | 2.089 | 171.515 | 13 | 11.580 | -9.490 |
| CMC-Por aryl | ee_percent | historical_order | elastic_net | 25 | 5.352 | 292.463 | 12 | 11.580 | -6.228 |
| CMC-Por aryl | ee_percent | historical_order | ridge | 25 | 8.773 | 297.250 | 16 | 11.580 | -2.807 |
| CMC-Por aryl | ee_percent | historical_order | tanimoto_knn | 25 | 1.482 | 238.721 | 7 | 11.580 | -10.098 |
| CMC-Por aryl | ee_percent | performance_first | elastic_net | 25 | 5.352 | 336.989 | 23 | 11.580 | -6.228 |
| CMC-Por aryl | ee_percent | performance_first | ridge | 25 | 8.773 | 331.021 | 23 | 11.580 | -2.807 |
| CMC-Por aryl | ee_percent | performance_first | tanimoto_knn | 25 | 1.482 | 187.666 | 6 | 11.580 | -10.098 |
| CMC-Por aryl | ee_percent | random | ridge | 25 | 10.644 | 274.596 | 19 | 11.580 | -0.935 |
| CMC-Por aryl | ee_percent | random | tanimoto_knn | 25 | 9.781 | 225.759 | 12 | 11.580 | -1.799 |
| CMC-Por aryl | ee_percent | uncertainty_diversity | elastic_net | 25 | 4.111 | 193.940 | 6 | 11.580 | -7.469 |
| CMC-Por aryl | ee_percent | uncertainty_diversity | ridge | 25 | 4.141 | 195.890 | 8 | 11.580 | -7.439 |
| CMC-Por aryl | ee_percent | uncertainty_diversity | tanimoto_knn | 25 | 2.089 | 175.443 | 14 | 11.580 | -9.490 |
| CMC-Por aryl | isolated_yield_percent | diversity_first | elastic_net | 25 | 35.582 | 453.058 | 6 | 15.000 | 20.582 |
| CMC-Por aryl | isolated_yield_percent | diversity_first | ridge | 25 | 35.032 | 467.224 | 6 | 15.000 | 20.032 |
| CMC-Por aryl | isolated_yield_percent | diversity_first | tanimoto_knn | 25 | 26.904 | 354.284 | 2 | 15.000 | 11.904 |
| CMC-Por aryl | isolated_yield_percent | historical_order | elastic_net | 25 | 8.173 | 457.616 | 6 | 15.000 | -6.827 |
| CMC-Por aryl | isolated_yield_percent | historical_order | ridge | 25 | 10.244 | 474.511 | 6 | 15.000 | -4.756 |
| CMC-Por aryl | isolated_yield_percent | historical_order | tanimoto_knn | 25 | 3.045 | 398.990 | 4 | 15.000 | -11.955 |
| CMC-Por aryl | isolated_yield_percent | performance_first | elastic_net | 25 | 8.173 | 613.981 | 9 | 15.000 | -6.827 |
| CMC-Por aryl | isolated_yield_percent | performance_first | ridge | 25 | 10.244 | 616.732 | 9 | 15.000 | -4.756 |
| CMC-Por aryl | isolated_yield_percent | performance_first | tanimoto_knn | 25 | 6.276 | 312.254 | 2 | 15.000 | -8.724 |
| CMC-Por aryl | isolated_yield_percent | random | ridge | 25 | 21.604 | 518.475 | 24 | 15.000 | 6.604 |
| CMC-Por aryl | isolated_yield_percent | random | tanimoto_knn | 25 | 18.131 | 390.508 | 2 | 15.000 | 3.131 |
| CMC-Por aryl | isolated_yield_percent | uncertainty_diversity | elastic_net | 25 | 35.582 | 467.958 | 6 | 15.000 | 20.582 |
| CMC-Por aryl | isolated_yield_percent | uncertainty_diversity | ridge | 25 | 35.032 | 479.375 | 6 | 15.000 | 20.032 |
| CMC-Por aryl | isolated_yield_percent | uncertainty_diversity | tanimoto_knn | 25 | 26.904 | 368.317 | 2 | 15.000 | 11.904 |

## Table S5. Independent held-out EE model comparison

| Cohort | Feature set | Features | Model | n | MAE | MAE CI low | MAE CI high | RMSE | R² | Within 10 | Within 20 | Δ vs structure-only |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P7 target holdout | structure_only | 547 | elastic_net | 38 | 12.612 | 10.192 | 15.491 | 15.183 | 0.064 | 0.474 | 0.763 | NA |
| P7 target holdout | structure_only | 547 | gaussian_process | 38 | 13.631 | 11.215 | 16.636 | 16.154 | -0.060 | 0.237 | 0.842 | NA |
| P7 target holdout | structure_only | 547 | lightgbm | 38 | 10.006 | 7.079 | 13.561 | 14.328 | 0.166 | 0.658 | 0.816 | NA |
| P7 target holdout | structure_only | 547 | ridge_regression | 38 | 10.388 | 8.063 | 13.266 | 13.278 | 0.284 | 0.684 | 0.842 | NA |
| P7 target holdout | structure_pose | 1241 | elastic_net | 38 | 8.583 | 6.251 | 11.433 | 11.932 | 0.422 | 0.711 | 0.868 | -4.030 |
| P7 target holdout | structure_pose | 1241 | gaussian_process | 38 | 13.631 | 11.215 | 16.636 | 16.154 | -0.060 | 0.237 | 0.842 | 0.000 |
| P7 target holdout | structure_pose | 1241 | lightgbm | 38 | 10.088 | 7.203 | 13.534 | 14.246 | 0.176 | 0.658 | 0.816 | 0.082 |
| P7 target holdout | structure_pose | 1241 | ridge_regression | 38 | 9.483 | 6.921 | 12.591 | 13.120 | 0.301 | 0.684 | 0.868 | -0.905 |
| P7 family holdout | structure_only | 547 | elastic_net | 38 | 10.406 | 7.968 | 13.391 | 13.525 | 0.257 | 0.605 | 0.842 | NA |
| P7 family holdout | structure_only | 547 | gaussian_process | 38 | 14.105 | 11.582 | 17.129 | 16.655 | -0.127 | 0.289 | 0.842 | NA |
| P7 family holdout | structure_only | 547 | lightgbm | 38 | 9.869 | 6.643 | 13.709 | 14.915 | 0.096 | 0.684 | 0.789 | NA |
| P7 family holdout | structure_only | 547 | ridge_regression | 38 | 11.828 | 9.368 | 14.617 | 14.495 | 0.147 | 0.474 | 0.842 | NA |
| P7 family holdout | structure_pose | 1241 | elastic_net | 38 | 9.334 | 6.872 | 12.196 | 12.557 | 0.359 | 0.632 | 0.842 | -1.072 |
| P7 family holdout | structure_pose | 1241 | gaussian_process | 38 | 14.105 | 11.582 | 17.129 | 16.655 | -0.127 | 0.289 | 0.842 | -0.000 |
| P7 family holdout | structure_pose | 1241 | lightgbm | 38 | 9.457 | 6.424 | 13.187 | 14.254 | 0.175 | 0.658 | 0.842 | -0.412 |
| P7 family holdout | structure_pose | 1241 | ridge_regression | 38 | 11.914 | 9.071 | 15.135 | 15.321 | 0.047 | 0.553 | 0.789 | 0.086 |

## Reading notes

- Table S3 compares representation arms under the same reciprocal replay. P0/P1 are intentionally diagnostic; P3/P4 preserve the B5 structure baseline and add compact pose information.
- Table S4 uses the independent scope-progression feature set `rdkit_morgan_stage2p` (15 RDKit descriptors + 1,024-bit Morgan + raw Stage 2p pose block). It is not a replacement for the B1–B5/P0–P4 ladder.
- Table S5 is a separate P7 held-out benchmark. Its structure-only arm uses a 512-bit Morgan fingerprint (547 total features), so it should not be conflated with the frozen PPTL B5 1,024-bit arm.
- Pose-related improvements are directional/conditional; the prespecified 10% progressive-AUC superiority gate remains unresolved.
