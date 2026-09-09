# Algorithm specifications

This document is the compact, implementation-facing specification for the
released analyses. The executable source remains authoritative; this file
makes the choices discoverable in one place.

## Features and preprocessing

- B1 uses six RDKit scalars; B2 uses 15 RDKit descriptors; B3/B4/B5 append
  radius-2 Morgan fingerprints of 128/256/1,024 bits.
- The primary B5 fingerprint has `includeChirality=False`. Stage 2p contains
  248 pose features; P3 adds a 44-feature compact C1 block; P4 adds C1 plus a
  16-feature catalyst-interaction C2 block.
- Numeric scaling, constant-feature removal, and model selection are fitted
  only on the training partition of each split. Predictions are clipped to
  0–100 percent.
- A substrate is the prediction and validation unit. Its conformers and poses
  never become separate labelled rows.

## Metrics and residuals

For observed values `y_i` and predictions `p_i`,

```text
residual_i = y_i - p_i
MAE  = mean(|residual_i|)
RMSE = sqrt(mean(residual_i^2))
R²   = 1 - sum(residual_i^2) / sum((y_i - mean(y))^2)
```

MAE and RMSE are in percentage points for ee/yield. Positive residual bias is
underprediction. A zero-variance observed target makes R² undefined rather
than zero.

The complete structure-only rerun uses one target-holdout per modelable P7
substrate. Within each split, 29 records are training, eight are validation,
and one is the held-out target. The family-held-out analysis holds out all
members of one family; train/validation counts therefore vary with family
size.

## Uncertainty, novelty, and coverage

For a candidate `x` and selected set `S`, using radius-2 Morgan fingerprints:

```text
novelty(x) = 1 - max(Tanimoto(Morgan(x), Morgan(s)) for s in S)
```

For family `f`, with `c_f` already-selected members:

```text
coverage_raw(x) = 1 / (1 + c_f)
```

Every score component is min–max normalized over the current candidate set:

```text
minmax(v) = (v - min(v)) / (max(v) - min(v))
```

If `max(v) == min(v)`, the normalized component is all zeros. An empty
selected set is handled by the initial seed procedure, not by assigning an
arbitrary novelty value.

Model disagreement is the standard deviation across the available Ridge,
Elastic Net, and Tanimoto-kNN predictions. In the progressive route,

```text
uncertainty = 0.5 * minmax(novelty) + 0.5 * minmax(model_disagreement)
```

The deterministic route scores are:

```text
diversity_first       = 0.8 novelty + 0.2 coverage
uncertainty_diversity = 0.4 novelty + 0.4 uncertainty + 0.2 coverage
performance_first     = 0.5 predicted_performance
                         + 0.3 uncertainty + 0.2 novelty
```

The sealed-panel score uses model/source disagreement in the implementation
and is:

```text
panel_score = 0.4 disagreement + 0.4 minmax(novelty) + 0.2 coverage
```

Generator likelihood is not a decisive panel term.

## Seeds, nearest neighbors, and tie-breaking

- The initial progressive seed is two whole substrates. Historical order uses
  the first two source-order records. Random routes sample two without
  replacement. For model-guided routes, the central seed minimizes mean
  Morgan/Tanimoto distance to every other active substrate; `numpy.argmin`
  selects the first input-order member on an exact tie. The second seed
  maximizes distance from the central seed; exact ties select the lower input
  index.
- Tanimoto-kNN uses the released Morgan fingerprint matrix, the five most
  similar training members (or all members when fewer than five exist), and
  weights each neighbor by `similarity + 1e-6`. It is a challenger model, not
  the primary estimator.
- Model-guided acquisition maximizes `(score, -source_order)`.
- Historical order minimizes source order.
- Sealed-panel sorting is `(-panel_score, canonical_smiles)`.
- Random routes use
  `random.Random(seed + replicate*1009 + route_seed + target_seed)` and sample
  without replacement. Primary random summaries use 500 replicates.

## Transfer weights and negative-transfer safeguards

The reciprocal transfer directions are P7 → CMC-Por aryl and CMC-Por → P7.
Canonical overlaps are removed from cold-start source training and retained as
paired diagnostics. Experts are target-only, source-domain, pooled/domain-
indicator, coefficient-regularized, residual-correction, and guarded-ensemble
variants as declared in the PPTL contract.

At the first scored post-seed reveal, the declared PPTL contract assigns target
weight 0.5 and distributes the remaining 0.5 over the source/pooled experts.
The current `GuardedEnsemble` implementation in `code/scripts/pptl/core.py`
initializes four experts as `[target_only, p7, cmcpor, combined]` with weights
`[0.5, 1/6, 1/6, 1/6]`. It updates normalized weights as

```text
eta = sqrt(2 log(number_of_experts) / (scored + 1))
raw_i = initial_i * exp(-eta * cumulative_absolute_error_i / 100)
```

For fewer than five scored reveals, each non-target raw weight is capped at
`0.5 * raw_target / number_of_source_experts`. From five reveals onward, an
expert is zeroed when its cumulative absolute-error difference from the target
expert exceeds `0.01 * scored`, equivalent to an average gap greater than one
ee percentage point. Shadow predictions remain in the output. EE and yield
histories are separate.

The contract also declares a 10% relative family-negative-transfer threshold,
but that relative condition is not implemented in `GuardedEnsemble`'s expert
suppression branch; it is a reporting/gate threshold in the current contract.
This implementation/contract distinction must be resolved or disclosed before
the SI claims a fully identical relative safeguard.

## Bootstrap and confidence intervals

The 38-substrate held-out benchmark uses 20,000 row-level bootstrap draws with
seed `20260731` and percentile intervals for aggregate MAE and RMSE. Route and
scaffold bootstrap artifacts record their own replicate counts and seeds in
the JSON output. Paired route/scaffold resampling preserves the matched
substrate or scaffold unit. Recalculation uses the released prediction rows
and the bootstrap scripts under `code/scripts/pptl/`.

## Learning-curve AUC and `n90`

For median MAE `m(n)` at the actual stored prefix grid `n`,

```text
AUC(MAE) = sum_i (n[i+1] - n[i]) * (m(n[i]) + m(n[i+1])) / 2
```

There is no extrapolation beyond the last scored prefix. Define

```text
threshold90 = baseline_mae - 0.90 * (baseline_mae - full_pool_loo_mae)
```

`n90` is the first stored prefix whose median MAE is no greater than
`threshold90`; if the threshold is never reached it is recorded as null/not
reached. The route JSON files retain the prefix rows and summary values.

## Candidate applicability and filters

The frozen applicability criterion is the maximum Morgan/Tanimoto similarity
to the reference set, with `max_morgan_tanimoto <= 0.35` meaning in-domain.
Contract validity is a separate chemistry grammar/filter decision. Candidate
counts must therefore be reported as contract-valid, in-domain, and their
intersection—not collapsed into one number.
