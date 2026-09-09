# Stage 2p: Reaction-Axis Substrate Representation

## Purpose

Stage 2p tests whether a catalyst-stripped, nitrene-anchored representation of substrate folding and directed C–H attack geometry improves prediction of the numeric ee magnitude beyond the canonical Stage 2-alt representation.

The primary cohort is the existing 40-substrate Stage 2-alt cohort. The target remains unsigned `ee_percent`; Stage 2p does not predict absolute product configuration because configuration labels are not available consistently in the current records.

## Pose population

Each substrate contributes the 200 retained Stage 1 poses:

- `top_100`: 100 lowest UFF pose-score poses;
- `bottom_100`: 100 highest UFF pose-score chemically valid poses;
- `all_200`: all retained poses.

Poses are equally weighted within each stratum. UFF score is retained as a rank for correlation diagnostics, not treated as a thermodynamic energy.

## Geometry

Catalyst atoms are excluded from density fields. The substrate-bound nitrene N is retained as a reaction-center point, and the Stage 1-selected transferred H is retained per pose. The reported product-forming C–H site is used; unreported competing sites are outside this Stage 2p experiment.

The coordinate system is azimuth-free. The forward axis is N→H and the reverse axis is H→N. Geometry is encoded with smooth radial responses, radial quantiles, low-order Legendre/spherical-harmonic invariants through order 4, and directed axial/cylindrical descriptors. Handedness-dependent quantities are represented by mirror-invariant norms; chemically directed N↔H contrasts remain signed.

## Feature blocks

The compact Stage 2p block is limited to 250 features per substrate and includes:

- nitrene-centered and transferred-H-centered fields;
- normalized all-heavy-atom, carbon, heteroatom, aromatic, halogen, and transferred-H channels;
- N→H and H→N directed projections;
- directional symmetry and antisymmetry terms;
- top-versus-bottom Wasserstein and Jensen–Shannon relationships;
- pose-descriptor energy distances and UFF-rank Spearman relationships.

Rendered five-view SVG diagnostics and intermediate per-pose fields are generated inside a temporary directory and deleted after feature extraction. Only numerical features, provenance, predictions, metrics, and ablation summaries persist.

Each feature row also stores a separate non-model diagnostic block with bootstrap mean confidence-widths and split-half Wasserstein stability for representative nitrene, transferred-H, and directed-axis descriptors.

## Model comparison

The primary four-way comparison is:

1. Stage 2 pose-summary;
2. canonical Stage 2-alt;
3. Stage 2p geometry alone;
4. Stage 2-alt plus Stage 2p.

Component ablations are evaluated on the rigorous nested track. The compatibility track reproduces the recorded Stage 2-alt grid-selection protocol. The rigorous track uses outer leave-one-out validation with inner leave-one-out Elastic Net hyperparameter selection, fold-local constant filtering and scaling, and the same alpha/l1-ratio grid.

The primary practical gate is at least a 1 ee-point MAE improvement over Stage 2-alt, with a paired bootstrap 95% interval supporting a lower MAE and no material RMSE or within-20%-ee degradation. Pose-ensemble stability remains diagnostic-only for this first comparison.

## Family-held-out validation

The strict generalization check uses outer leave-one-family-out folds across 18
curated substrate families. Elastic Net hyperparameters are selected inside
each outer training set by an inner leave-one-family-out procedure; the held-
out family is never used for feature filtering, scaling, or model selection.

Using the current 40-substrate cohort, the pooled MAE results are:

| Feature set | MAE | RMSE | R2 | Macro family MAE | Within 15 ee points |
| --- | ---: | ---: | ---: | ---: | ---: |
| Stage 2 pose-summary | 16.4012 | 24.5459 | -0.1139 | 16.8057 | 25/40 |
| Stage 2-alt | 14.4329 | 22.2276 | 0.0866 | 15.0330 | 25/40 |
| Stage 2p geometry | 15.2249 | 22.4659 | 0.0669 | 16.8786 | 26/40 |
| Stage 2-alt + Stage 2p | 15.1428 | 23.0586 | 0.0170 | 15.5278 | 27/40 |

The family-held-out result therefore does not support Stage 2p as an overall
replacement for Stage 2-alt. The recurrent difficult families are thioether
linker, nitrogen heteroaryl, alkyl aryl-chain, and fused sulfur heteroaryl.
The current cohort contains several singleton families, so family-level MAE
should be interpreted as a diagnostic rather than a stable population estimate.

## Publication-readiness benchmark

The legacy comparisons above remain reproducible diagnostics. The publication
baseline is evaluated by `scripts/stage2p_publication_benchmark.py`, which has a
stricter evidence contract:

- only checked ee labels from the fixed `fe-p7-cl` catalyst domain are admitted;
  `1z` is excluded before feature generation because it belongs to `fe-p2-cl`,
  while `1ad` and `1an` remain auditable exclusions for unresolved or
  non-applicable ee;
- temperature and condition-set identity are encoded as explicit features;
- outer leave-one-family-out folds contain inner leave-one-family-out model
  selection, with feature masking and scaling fit on the training partition;
- Elastic Net is the locked incumbent and Ridge, median, and chemical nearest
  neighbour are required challengers;
- train-only nearest-neighbour applicability thresholds produce explicit
  `in_domain` or `abstain_ood` decisions;
- split-conformal absolute-residual intervals replace the former signed
  residual addition, and coverage is reported at nominal 80% and 95% levels;
- ee and isolated-yield predictions are joined into a conservative action rule:
  advance only when the lower 80% interval clears both 80 ee and 50% yield.

The current run contains 38 fixed-catalyst ee records. Its incumbent results are
MAE 9.627 ee, RMSE 12.991 ee, 25/38 within ±10 ee, 28/38 within ±15 ee,
32/38 within ±20 ee, 0.875 precision at the ≥80 ee threshold, 0.816 nominal
80% interval coverage, and 0.974 nominal 95% interval coverage. These are
stronger and more honest diagnostics than the legacy table, but the readiness
report remains `not_ready`: absolute product configurations, a locked
prospective panel, and a connected cross-catalyst bridge matrix are still
required before making signed-stereochemical, late-stage, or catalyst-design
claims.

Artifacts:

- Reproduction script: `scripts/stage2p_publication_benchmark.py`
- Benchmark report: `data/jacs_2025/stage2/reports/stage2p-publication-benchmark.json`
- ee predictions: `data/jacs_2025/stage2/reports/stage2p-publication-predictions.csv`
- yield predictions: `data/jacs_2025/stage2/reports/stage2p-publication-yield-predictions.csv`
- readiness report: `data/jacs_2025/stage2/reports/stage2p-publication-readiness.md`

Artifacts:

- Family-held-out metrics: `data/jacs_2025/stage2/modeling/stage2p-family-heldout-metrics.json`
- Family-held-out predictions: `data/jacs_2025/stage2/modeling/stage2p-family-heldout-predictions.csv`
- Reproduction script: `scripts/stage2p_family_heldout.py`

## Artifacts

- Features: `data/jacs_2025/stage2/features/stage2p-features.jsonl`
- Feature manifest: `data/jacs_2025/stage2/features/stage2p-manifest.json`
- Metrics: `data/jacs_2025/stage2/modeling/stage2p-model-metrics.json`
- Predictions: `data/jacs_2025/stage2/modeling/stage2p-predictions.csv`
- Feature trends: `data/jacs_2025/stage2/modeling/stage2p-trends.csv`
- Reproduction script: `scripts/stage2p_representation.py`
