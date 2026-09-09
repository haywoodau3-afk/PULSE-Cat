# Stage 2p substrate-scope progression workflow

## Decision record

Stage 2p is the active representation and data contract for the iron part of
the project. Stage 3 is not a required next stage. Stage 2pp and the original
Stage 3 feature-development plan are retained as historical experiments and
negative controls.

The central rule is to grow the experimental scope one whole substrate at a
time and refit the model after every addition. Pose-level records, computed
features, or unreported reactions never count as extra labelled substrates.

## What is being learned

The workflow supports the two currently available percentage outcomes:

- `ee_percent`
- `isolated_yield_percent`

Each substrate has one experimental label per target when measured. Missing
outcomes remain missing. A prediction-only substrate is never assigned a
synthetic zero or negative label and is never used to fit a model.

The workflow is intended for a fixed catalyst/condition domain. The current
runs are:

- P7: `fe-p7-cl`, the JACS thermal system.
- cmcpor: `cmcpor-fecl`, the cmcpor rerun domain.

These domains are analysed separately; their labels are not pooled.

## Feature contract

The default matrix is `rdkit_morgan_stage2p`:

1. Fifteen RDKit molecular descriptors: size, molecular weight, logP, TPSA,
   charge, fraction CSP3, rotatable bonds, ring counts, hydrogen-bond counts,
   heteroatom count, spiro count, and chiral-centre count.
2. A radius-2, 1024-bit Morgan fingerprint for structural similarity and
   Tanimoto nearest-neighbour prediction.
3. Numeric Stage 2p feature blocks flattened by stable field name. These are
   representation features only; they are not additional observations.

If a future scope has no Stage 2p block, use `rdkit_morgan`. If only some
records have Stage 2p features, missing feature values are explicit zeroes and
the manifest records feature availability. The Stage 2p block must be
computed without using the experimental outcome.

## Sequential acquisition design

The initial labelled seed contains two substrates selected by a central-plus-
diverse rule. The model is then refit at labelled-scope sizes 2, 3, 4, and
each subsequent whole-substrate prefix.

Five routes are evaluated:

- `diversity_first`: maximise Morgan novelty while maintaining family
  coverage.
- `uncertainty_diversity`: combine structural novelty, model disagreement,
  and family coverage. This is the recommended default route.
- `performance_first`: prioritise predicted performance, with uncertainty and
  novelty guardrails. This is a challenge route, not the sole basis for scope
  expansion.
- `historical_order`: reproduce the source order as a non-optimised control.
- `random`: 500 randomized whole-substrate routes, used to estimate the
  chance-performance distribution. Every replicate is evaluated at every
  labelled prefix, and the displayed random curve is the mean MAE across
  independent random starting pairs and subsequent random permutations.

The default route should be chosen using the median learning-curve area under
MAE across the declared targets and domains, with `n90` as a secondary
diagnostic. This prevents selecting a route merely because it wins one early
milestone. A route is not considered informative if it only improves a
single hand-picked substrate or if its advantage disappears against the
randomized distribution.

## Audit and late-stage policy

The audit set is fixed before fitting. It is excluded from the active learning
pool and is not used to choose the route.

For CMC-Por primary aryl analysis, pass `--family-id angew-aryl-c-h-amination`
and provide the seven aryl audit IDs explicitly. The 17 sulfonyl records are a
separate pathway control and must not remain in the active aryl pool.

- For a labelled historical scope without a separate prospective pool, use a
  predeclared family-stratified holdout. The implementation takes the last
  source-order fraction within each family, which is reproducible and avoids
  manually selecting favourable outcomes.
- For P7, the five late-stage skipped substrates (`1ap`, `1aq`, `1as`, `1at`,
  `1au`) are locked prediction-only records. Their labels remain unknown.
  Their predictions are written separately and are not included in learning
  curves or reference metrics.
- For cmcpor, no separate unlabelled pool is available, so a 20% per-family
  retrospective audit tranche is used. It contains 11 records across the two
  declared source families.

For future papers, the preferred prospective audit panel should be locked
before seeing outcomes and should include chemically near, chemically novel,
high-uncertainty, and predicted-low-performance candidates. The panel should
be tested experimentally, including failures.

## Models and safeguards

The primary model is low-capacity standardized Ridge regression (`alpha=10`).
Elastic Net (`alpha=0.1`, `l1_ratio=0.15`) and Tanimoto-weighted k-nearest
neighbours are challengers. All percentage predictions are bounded to
0--100%, which is both a physical outcome constraint and a diagnostic against
unstable early fits in a high-dimensional Stage 2p matrix.

The randomized route uses Ridge and Tanimoto kNN for all 500 replicates to keep
the stress test tractable. Elastic Net remains in deterministic-route and
leave-one-out reference comparisons; this policy is recorded in each manifest.

## Metrics

Every run writes:

- `learning-curve.csv`: route, replicate, labelled count, model, MAE, RMSE,
  and rank correlation on the remaining active substrates.
- `learning-curve-summary.csv`: mean, standard deviation, median, and
  interquartile MAE at each prefix. The random plot uses the mean curve and
  its q25--q75 band; deterministic routes have one replicate.
- `scope-progression-manifest.json`: data provenance, exclusions, feature
  policy, audit IDs, reference metrics, and convergence diagnostics.
- `selection-events.csv`: the substrate selected at each step and the route
  components that caused its selection.
- `audit-predictions.csv`: predictions for the locked labelled audit tranche,
  kept separate from route fitting.
- `audit-metrics.csv`: aggregate MAE, RMSE and rank metrics for the locked audit
  at every declared milestone. Per-substrate predictions and aggregate metrics
  intentionally use separate schemas.
- `late-stage-predictions.csv`: predictions only for unlabelled late-stage
  candidates.

The reference metrics are leave-one-substrate-out diagnostics on the active
labelled pool. `n90` is the first prefix where the median MAE achieves 90% of
the reduction from the intercept baseline to the full-pool leave-one-out
reference. `auc_mae` is the trapezoidal area under the median MAE learning
curve; lower is better.

## Reproduction commands

P7, including the five late-stage prediction-only records:

```bash
./.venv/bin/python scripts/scope_progression.py \
  --records data/jacs_2025/stage2/curated-reaction-records.jsonl \
  --stage2p-features data/jacs_2025/stage2/features/stage2p-features.jsonl \
  --late-stage-records data/jacs_2025/stage3/latestage/latestage-prediction-records.jsonl \
  --output-dir data/jacs_2025/scope_progression \
  --catalyst-id fe-p7-cl \
  --feature-set rdkit_morgan_stage2p \
  --replicates 500 \
  --exclude-ids 1ad
```

cmcpor, with the predeclared 20% family-stratified retrospective audit:

```bash
./.venv/bin/python scripts/scope_progression.py \
  --records data/expansion/catalyst_rerun/cmcpor/stage2-records.jsonl \
  --stage2p-features data/expansion/catalyst_rerun/cmcpor_uff_full/stage2p/features/stage2p-features.jsonl \
  --output-dir data/expansion/catalyst_rerun/cmcpor_uff_full/scope_progression \
  --catalyst-id cmcpor-fecl \
  --family-id angew-aryl-c-h-amination \
  --feature-set rdkit_morgan_stage2p \
  --audit-ids 2y,2z,4a,4b,4c,4d,4e \
  --replicates 500
```

## Completed run interpretation

The completed primary Ridge curves give the following convergence diagnostics.
`n90` is a labelled-substrate count; `—` means the threshold was not reached
within the active pool.

| Domain | Target | Diversity | Uncertainty + diversity | Performance-first | Random | Historical |
|---|---|---:|---:|---:|---:|---:|
| P7 | ee | 24 / 391.7 | 16 / 337.2 | 7 / 403.1 | 29 / 355.5 | — / 757.7 |
| P7 | yield | 2 / 570.4 | 2 / 554.2 | 2 / 666.5 | 4 / 639.4 | 2 / 913.2 |
| cmcpor | ee | 18 / 318.9 | 12 / 307.5 | 8 / 473.1 | 23 / 402.1 | 27 / 579.8 |
| cmcpor | yield | 15 / 524.0 | 11 / 512.5 | — / 828.3 | 34 / 653.8 | 27 / 764.2 |

The paired values are `n90 / auc_mae`; these convergence diagnostics retain
the median curve for robustness, while the random visualization uses the mean
curve requested for route averaging. Random can have a favourable area by
chance, but it is not an actionable acquisition policy. Performance-first can
reach an early threshold, especially for ee, but its larger integrated error
shows why it should remain a challenge route. Uncertainty-plus-diversity is
the best systematic default across the two domains and both targets, with
diversity-first as a useful conservative guardrail.

The P7 active pool contains 39 records, with 38 measured ee labels and 39
measured yields. Its reference MAEs are 8.15 ee and 18.13 yield for Ridge.
The cmcpor run contains 50 records, of which 11 are locked audit records and
39 are active; its reference MAEs are 10.52 ee and 16.63 yield for Ridge.
These are retrospective workflow diagnostics, not prospective validation.

## Future-paper checklist

Before expanding a new catalysis scope:

1. Freeze the catalyst/condition domain, outcome definitions, and substrate
   family labels.
2. Register the complete candidate pool, including skipped and prediction-only
   substrates, before inspecting outcomes.
3. Compute RDKit descriptors, Morgan fingerprints, scaffold IDs, and any
   label-independent Stage 2p-style features for every candidate.
4. Lock a family-balanced audit panel and document source order.
5. Start with two substrates, then grow 2 → 3 → 4 → … by whole-substrate
   acquisition.
6. Run uncertainty-plus-diversity, diversity-first, performance-first,
   historical, and 500-replicate random controls.
7. Select the default route by integrated learning-curve performance and
   route stability, not by the best single point.
8. Report the full curve, audit predictions, applicability-domain distances,
   failures, and all exclusions.
9. Experimentally test the locked prediction-only panel before making a
   generalization claim.
