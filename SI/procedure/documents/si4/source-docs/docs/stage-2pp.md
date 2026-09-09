# Stage 2″: Persistent Atomic Occupancy and Reaction-Corridor Flexibility

## Status

Implemented and benchmarked on 2026-08-06. The representation is retained as an experimental branch; it does not replace Stage 2p or Stage 2-alt.

## Purpose

Stage 2″ tests whether persistent, hard-rule atomic occupancy fields and reaction-corridor flexibility features improve unsigned ee prediction beyond Stage 2-alt and the existing Stage 2p prototype. It uses the current 200 retained poses per substrate and does not expand the geometry cache beyond its present 8,200-pose scale.

Stage 2″ does not calculate or claim electron density. Its fields are geometric occupancies constructed from XYZ atom coordinates and fixed atomic sizes.

## Cohort and target

- Keep the complete 41-substrate, 8,200-pose geometry cache.
- Fit and score ee models on the canonical 39 model-ready records and their 7,800 poses.
- Exclude achiral `1an` and unresolved-ee `1ad` from ee fitting and scoring.
- Predict unsigned `ee_percent`; absolute configuration is outside this experiment.
- Keep all poses of a substrate in the same outer split.

## Stage 1 boundary

Stage 1 remains a fixed 5,000-attempt sampler per substrate. It uses deterministic RDKit ETKDGv3 embedding, substrate-only UFF cleanup, virtual assembly against the frozen catalyst, and fixed label-blind validity checks.

From the Valid Pose Pool, Stage 1 persists exactly 200 poses per substrate:

- `top_100`: the 100 lowest-UFF valid, clash-screened poses;
- `bottom_100`: the 100 highest-UFF valid, clash-screened poses;
- `all_200`: both strata together.

The names describe relative UFF ranking, not reaction energy or thermodynamic populations. Stage 2″ does not persist the other embedding attempts and does not change the current XYZ retention scale.

## Duplicate sampling and weights

Within each retained 100-pose stratum, poses are grouped using a label-blind quantized geometry fingerprint containing reaction geometry and pairwise heavy-atom distances. The quantization rule is fixed without consulting ee labels and recorded in the manifest.

Every retained pose contributes. Every geometry cluster receives equal total weight within its stratum, and poses inside a cluster divide that cluster's weight equally. Top and bottom strata receive equal total weight in `all_200`. UFF score and rank remain diagnostic covariates; Stage 2″ does not use Boltzmann weighting.

## Activation site and transferred hydrogen

The activation carbon is selected from substrate connectivity by the fixed rule that closes the five-membered amination ring. It is not learned from ee and is not selected from the observed product.

For an activation carbon bearing two hydrogens, the nearer hydrogen to the nitrene N supplies the primary directed N→H corridor for each pose. Stage 2″ also retains both N···H distances, their gap, the approach-angle gap, and the weighted frequency with which each mapped hydrogen is preferred.

## Atomic occupancy fields

Each atom contributes a smooth Gaussian kernel scaled by a fixed, versioned van der Waals-radius table. Kernel widths, grid extents, and resolution are hard rules and are never learned from reaction labels.

Model fields exclude fixed catalyst atoms. The nitrene N and reactive C/H coordinates define the anchors. Channels are total heavy atoms, carbon, heteroatoms, halogens, hydrogen, and explicit reactive C/transferred-H markers.

Fields use azimuth-free cylindrical coordinates: axial position `z` and perpendicular distance `rho`. For every substrate and channel, persist:

- nitrene-centered top-100, bottom-100, and all-200 fields;
- activation-site-centered top-100, bottom-100, and all-200 fields;
- directed N→H and H→N fields for all three strata;
- top-minus-bottom difference fields;
- one-dimensional axial and radial profiles.

Fields are normalized by stratum weight. Shape channels are additionally normalized by heavy-atom count; molecular size remains a separate scalar descriptor.

## Commonality, contrast, and flexibility

Within each stratum, Stage 2″ measures consensus occupancy, variance, entropy, cluster structure, and split-half stability. Between top and bottom strata, it measures signed difference fields, Wasserstein distance, Jensen-Shannon divergence, energy distance, and continuous UFF-rank correlations.

Reaction-corridor flexibility includes distributions of N···H and N···C distances, attack angles, tether torsions, corridor occupancy, and pose motion parallel and perpendicular to the N→H axis. Flexibility is reported for top-100, bottom-100, all-200, and top-minus-bottom relationships.

No high-ee/low-ee aggregate field is constructed before validation. Label-based analysis is limited to held-out predictions or computations made wholly inside an outer training fold.

## Numerical model features

High-resolution numerical occupancy arrays are canonical scientific and visualization artifacts. SVGs are derived from those arrays and are never converted back into features.

Model-facing features use a compact, predeclared set of coarse axial/radial bins, moments, entropy, consensus/variance, top-bottom relationships, corridor occupancy, flexibility, and stability summaries. Stage 2″ does not flatten high-resolution grids, train on SVG pixels, or use an image encoder.

## Sampling diagnostics

Each 100-pose stratum reports convergence at 25, 50, and 100 retained poses, plus deterministic rerun and split-half stability checks. Geometry-only quantization thresholds are locked before the full-cohort model run.

## Artifact contract

Preserve the existing UFF-optimized substrate XYZ, representative input/SDF files, and frozen-core assembly XYZ cache for all 8,200 retained poses. Do not automatically delete or expand that cache.

Add:

- compressed per-substrate numerical occupancy arrays;
- derived SVG views;
- JSON manifests containing rules, checksums, seeds, cluster assignments, weights, and convergence diagnostics;
- compact model matrices, predictions, metrics, and ablations.

The XYZ cache remains local and gitignored. Numerical features, SVGs, manifests, and reports follow the repository's tracked artifact policy. Code and filenames use `stage2pp`; human-facing documentation uses `Stage 2″`.

## Rollout

1. Implement the Stage 2″ artifact contract and deterministic tests.
2. Run a chemically diverse six-substrate pilot including `1ac`.
3. Lock geometry-only kernel, clustering, convergence, and stability rules.
4. Generate Stage 2″ artifacts for all 41 cached substrates.
5. Run the locked model comparison on the canonical 39-record ee cohort.

The pilot verifies clustering, field convergence, deterministic regeneration, artifact integrity, runtime, and incremental storage before full expansion.

## Model comparison

The primary comparison uses identical outer leave-one-family-out folds for the baseline representation and baseline plus Stage 2″. Within each outer held-out-family split, model selection chooses among regularized Ridge, Elastic Net, LightGBM, and Gaussian Process grids using only the non-held-out training/validation data. Predictions are bounded to the physical ee range `[0, 100]`; feature scaling and selection remain inside the training path. The current 39-record run produced 17 outer family splits after the canonical exclusions.

Secondary paired comparisons report each fixed model family for baseline, occupancy only, flexibility only, occupancy plus flexibility, and baseline plus both Stage 2″ blocks. Target-held-out and leave-one-out results are diagnostic only.

## Current result

The official run wrote artifacts under `data/jacs_2025/stage2pp/`. Family-held-out results on the canonical 39-record cohort were:

| Feature set | Model | MAE | RMSE | Within 20 ee points |
| --- | --- | ---: | ---: | ---: |
| Stage 2p | Elastic Net | 12.533 | 18.546 | 34/39 |
| Stage 2p + Stage 2″ | Elastic Net | 21.454 | 29.667 | 25/39 |
| Stage 2-alt | Elastic Net | 14.986 | 20.645 | 30/39 |
| Stage 2-alt + Stage 2″ | Elastic Net | 15.111 | 21.073 | 31/39 |
| Stage 2″ alone | Elastic Net | 16.021 | 21.950 | 28/39 |

The paired Stage 2p → Stage 2″-augmented Elastic Net MAE delta was `+8.921` ee points, with a paired-bootstrap 95% interval of `[+4.749, +13.659]`. The Stage 2-alt → augmented delta was `+0.126` ee points, with interval `[-2.641, +2.738]`. Neither comparison passes the improvement gate.

## Improvement contract

Stage 2″ improves the system only if the primary nested family-held-out MAE is at least 1 ee point lower than the identical baseline cohort and folds, with a paired-bootstrap 95% interval favoring Stage 2″.

RMSE, R², median absolute error, and within-10/15/20-ee counts remain mandatory diagnostics but are not hard adoption gates. All negative results remain reportable artifacts, and a secondary-model win alone does not make Stage 2″ the canonical representation.
