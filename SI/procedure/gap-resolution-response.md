# Response to remaining supporting-information and reproducibility gaps

## Scope of this response

This document records the evidence already completed and frozen in the working
repository, and separates it from items that still require a release artifact,
an author confirmation, or a small bookkeeping repair. The computational study
is retrospective/prediction-only unless explicitly stated otherwise. No
experimental outcome has been assigned to the generated candidate molecules or
to the sealed 8+8 panel.

The principal frozen identifiers are:

- study: `parallel-progressive-transfer-bidirectional-v1`;
- publication-ledger lock: `pptl-publication-ledger-lock-v1`;
- lock digest: `c2613a95c111f1eba4ed0830c808e211e78c3e867edd65005dd86368dccdef03`;
- ledger lock time: `2026-09-01T05:48:32.192767+00:00`;
- sealed-panel lock: `sealed-prospective-panel-v1`;
- sealed-panel SHA-256: `bb22a10a893e089143f16272b4b4778f7df19fc13be0ea3650619e7636f97e2b`.

The data, code, and report paths cited below are repository-relative paths so
that they can be copied directly into the SI data-availability statement.

## 1. Complete results from the 38-substrate rerun (SI S10–S11)

### Status: completed

The 38-substrate rerun was completed as a structure-only, held-out target
benchmark. The feature matrix contained 547 features: RDKit physicochemical
descriptors plus a 512-bit Morgan fingerprint. The benchmark contained 38
modelable substrates and 38 one-substrate target-holdout splits. For every
split, the target was excluded from fitting; 29 structurally diverse molecules
were used for training and eight for validation. Model selection used the
validation partition, and the held-out target was scored only after model
selection.

The four estimators were Elastic Net, Gaussian process regression, LightGBM,
and Ridge regression. The reported residual is

```text
residual = observed ee − predicted ee
```

so positive bias denotes underprediction and negative bias denotes
overprediction. The bootstrap intervals are 20,000 resamples of the 38
held-out residual records. They are percentile intervals for the aggregate MAE
and RMSE; they are not posterior intervals from the Gaussian-process model.

### 38-substrate target-holdout results

All errors are percentage points of ee. `Within 10` and `Within 20` are counts
of the 38 held-out predictions with absolute error at most 10 or 20 points.
`Max |error|` was calculated from the released row-level prediction table.

| Estimator | MAE | RMSE | R² | Bias | Median abs. error | Max abs. error | Within 10 | Within 20 | Bootstrap MAE 95% interval | Bootstrap RMSE 95% interval |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| Elastic Net | 12.6123 | 15.1827 | 0.0637 | -1.7635 | 10.0608 | 35.6172 | 18/38 (47.37%) | 29/38 (76.32%) | 10.1925–15.4915 | 12.3356–18.3416 |
| Gaussian process | 13.6306 | 16.1537 | -0.0599 | 0.0171 | 11.0690 | 37.5172 | 9/38 (23.68%) | 32/38 (84.21%) | 11.2151–16.6363 | 13.1033–19.6996 |
| LightGBM | 10.0055 | 14.3277 | 0.1661 | 0.4263 | 5.6384 | 38.2101 | 25/38 (65.79%) | 31/38 (81.58%) | 7.0787–13.5613 | 10.8372–18.0551 |
| Ridge | 10.3881 | 13.2785 | 0.2838 | -0.8570 | 7.5377 | 35.6887 | 26/38 (68.42%) | 32/38 (84.21%) | 8.0629–13.2655 | 10.2813–16.6543 |

Additional error-threshold counts from the same row-level tables are:

| Estimator | Within 15 points | Within 20 points | 95th-percentile absolute error |
|---|---:|---:|---:|
| Elastic Net | 27/38 (71.05%) | 29/38 (76.32%) | 28.8551 |
| Gaussian process | 29/38 (76.32%) | 32/38 (84.21%) | 32.2397 |
| LightGBM | 28/38 (73.68%) | 31/38 (81.58%) | 28.6989 |
| Ridge | 29/38 (76.32%) | 32/38 (84.21%) | 26.3158 |

The corresponding family-held-out analysis was also retained. It used the same
547-feature representation but held out all members of each of 17 substrate
families. The detailed family-held-out results are in
`data/jacs_2025/stage2/reports/family-heldout-structure-ee-model-benchmark.json`.
The aggregate values are:

| Estimator | MAE | RMSE | R² | Bias | Median abs. error | Max abs. error | Within 10 | Within 20 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Elastic Net | 10.4060 | 13.5247 | 0.2570 | 0.6688 | 7.0284 | 35.5747 | 23/38 (60.53%) | 32/38 (84.21%) |
| Gaussian process | 14.1048 | 16.6551 | -0.1268 | -0.1966 | 11.5714 | 37.7667 | 11/38 (28.95%) | 32/38 (84.21%) |
| LightGBM | 9.8689 | 14.9150 | 0.0964 | 0.9297 | 4.5647 | 37.9593 | 26/38 (68.42%) | 30/38 (78.95%) |
| Ridge | 11.8285 | 14.4945 | 0.1466 | -2.5592 | 10.4605 | 35.6166 | 18/38 (47.37%) | 32/38 (84.21%) |

The exact per-substrate predictions, split identifiers, validation metrics,
interval columns, residuals, and estimator parameters are deposited in:

- `data/jacs_2025/stage2/reports/full-scope-structure-model-predictions.csv`;
- `data/jacs_2025/stage2/reports/full-scope-structure-model-benchmark.json`;
- `data/jacs_2025/stage2/reports/full-scope-model-comparison.csv`;
- `data/jacs_2025/stage2/reports/family-heldout-structure-ee-model-predictions.csv`;
- `data/jacs_2025/stage2/reports/family-heldout-structure-ee-model-benchmark.json`.

## 2. Exact cohort and split membership (SI S4 and S11)

### Status: completed and machine-readable

The matched 38-substrate cohort is the 41-row P7 ledger after excluding:

- `1z`: zero-curated ee record excluded from the matched benchmark;
- `1ad`: zero-curated/thioether-linker record excluded from the matched benchmark;
- `1an`: achiral/not-applicable record with no usable ee label.

The exact 38 substrate IDs are:

```text
1a, 1b, 1c, 1d, 1e, 1f, 1g, 1h, 1i, 1j, 1k, 1l, 1m, 1n,
1o, 1p, 1q, 1r, 1s, 1t, 1u, 1v, 1w, 1x, 1y, 1aa, 1ab, 1ac,
1ae, 1af, 1ag, 1ah, 1ai, 1aj, 1ak, 1al, 1am, 1ao
```

The 17 family assignments are:

| Family | Substrate IDs | Count |
|---|---|---:|
| alkyl-aryl-chain | `1ah, 1ai` | 2 |
| branched-diaryl-alkyl | `1ao` | 1 |
| carbonyl-alkyl-aryl | `1ae, 1af, 1ag` | 3 |
| carbonyl-heterocycle-fused | `1u` | 1 |
| cycloalkyl-alkyl-aryl | `1aj, 1ak, 1al` | 3 |
| cycloalkyl-aryl | `1am` | 1 |
| diaryl-ethyl-aryl-substituted | `1b`–`1m` | 12 |
| diaryl-ethyl-parent | `1a` | 1 |
| nitrogen-heteroaryl | `1aa, 1ab` | 2 |
| oxygen-heteroaryl | `1o` | 1 |
| oxygen-heteroaryl-fused | `1p, 1q` | 2 |
| oxygen-heterocycle-fused | `1r, 1s, 1t` | 3 |
| polycyclic-aryl | `1n` | 1 |
| silyl-alkyl-aryl | `1ac` | 1 |
| sulfur-heteroaryl | `1v` | 1 |
| sulfur-heteroaryl-fused | `1w, 1x` | 2 |
| sulfur-heterocycle-fused | `1y` | 1 |

The exact target-holdout membership is stored in
`data/jacs_2025/stage2/reports/full-scope-structure-splits.json`. It contains
one split per target ID, with explicit `train_substrate_ids`,
`validation_substrate_ids`, and `target_substrate_id` fields. The target
holdout design is 29 training, 8 validation, and 1 target. The 29 training
members were selected from the remaining records using the deterministic
MaxMin Morgan/Tanimoto diversity procedure; the other eight records became
validation members.

The exact family-heldout membership is stored in
`data/jacs_2025/stage2/reports/family-heldout-ee-splits.json`. Each record
contains the full training, validation, and held-out family ID lists. The
family splits are not all 29+7 because the held-out family size changes the
number of records available for training and validation:

| Held-out family size | Training | Validation | Held-out records |
|---:|---:|---:|---:|
| 1 | 30 | 7 | 30+7+1 = 38 |
| 2 | 29 | 7 | 29+7+2 = 38 |
| 3 | 28 | 7 | 28+7+3 = 38 |
| 12 | 21 | 5 | 21+5+12 = 38 |

Thus, the phrase “29 training + 7 validation” applies to a two-member
held-out family. It is not a universal allocation. The 12-member
`diaryl-ethyl-aryl-substituted` family has 21 training and 5 validation
records; three-member families have 28 and 7; and one-member families have 30
and 7. This arithmetic is now explicit and reconciles the split files with the
38-record cohort.

## 3. Reconciliation of progression and transfer counts (SI S14)

### Status: completed, with populations explicitly separated

The counts refer to different ledgers and should not be combined:

| Population | P7 | CMC-Por | Meaning |
|---|---:|---:|---|
| Full publication ledger | 41 | 50 | All P7 records, or all CMC-Por rerun records. |
| CMC-Por primary aryl pathway | — | 33 | The 33 aryl records; 17 sulfonyl records remain a separate control family. |
| Independent P7 progression input | 39 | — | 41 P7 rows minus `1ad` audit exclusion; includes the independent progression population. |
| Independent P7 usable ee labels | 38 | — | The 39 progression rows minus the achiral/not-applicable `1an` ee record. |
| Independent P7 yield labels | 39 | — | Yield is present for the 39 active progression rows. |
| Independent CMC-Por aryl input | — | 26 | 33 aryl records minus the seven locked audit records `2y, 2z, 4a, 4b, 4c, 4d, 4e`. |
| CMC-Por aryl active ee/yield labels | — | 26/26 | The active aryl progression set; audit records are not silently mixed into it. |
| Matched 38-substrate benchmark | 38 | — | Excludes `1z`, `1ad`, and `1an`; used for the complete structure-only rerun. |

The independent progression manifests are:

- `data/jacs_2025/scope_progression/scope-progression-manifest.json`:
  `active_records=39`, `active_ee_records=38`, `active_yield_records=39`;
- `data/expansion/catalyst_rerun/cmcpor_aryl_scope_progression/scope-progression-manifest.json`:
  `input_records=33`, `active_records=26`, `active_ee_records=26`,
  `active_yield_records=26`.

The P7 independent ee progression therefore has prefixes 2–37: the final
prefix has 37 scored labelled rows because the active progression input has 39
records but only 38 usable ee labels and the progression protocol begins with
a two-substrate seed. The P7 independent yield curve runs through prefix 38.
The CMC-Por aryl ee and yield curves run through prefix 25 in the stored route
comparison because the final prefix is the last prefix at which the route
evaluation has a scored remaining label.

The “37 scored P7 transfer rows” are a separate row count. In
`data/expansion/pptl/matrix-ee-b5-p3-p4.json`, the CMC-Por-to-P7 target-only and
guarded rows are the 37 post-seed scored rows with explicit IDs
`1c,1d,1e,1f,1g,1h,1i,1j,1k,1l,1m,1n,1o,1p,1q,1r,1s,1t,1u,1v,1w,1x,1y,1aa,1ab,1ac,1ad,1ae,1af,1ag,1ah,1ai,1aj,1ak,1al,1am,1ao`. The target ledger count is 40, while the scored transfer rows are the subset retained after the transfer seed, target-label availability, and transfer-specific eligibility filters. The row count is therefore not a claim that the full 38-substrate matched benchmark contains only 37 ee labels.

The reciprocal P7-to-CMC-Por aryl transfer has 33 target ledger rows and 31
scored post-seed rows. Thirteen canonical structures overlap between source
and target. Atom maps were removed before canonical matching; overlapping
structures were excluded from cold-start source training and retained only for
paired diagnostics. The exact 13 pairs are recorded in
`data/expansion/pptl/publication-ledger-lock.json`.

## 4. Identification of the progression snapshots (SI S12 and S14)

### Status: completed for the stored progression and route-comparison artifacts; CBAL-SSE identifier still requires confirmation

The stored analyses are separate by design.

### Snapshot A: independent progression

- Version/manifest: `scope-progression-v1`.
- P7: 39 active records, 38 usable ee labels, 39 yield labels; ee prefix
  range 2–37 and yield prefix range 2–38.
- CMC-Por: 33 aryl input records, 26 active after audit exclusions; ee and
  yield prefix range 2–25 in the stored evaluation.
- Route families: historical order, diversity-first,
  uncertainty-diversity, performance-first, and 500 randomized routes.
- Primary model: Ridge, `alpha=10`; challengers include Elastic Net
  (`alpha=0.1`, `l1_ratio=0.15`) and Tanimoto k-nearest-neighbor.
- Primary data paths:
  `data/jacs_2025/scope_progression/` and
  `data/expansion/catalyst_rerun/cmcpor_aryl_scope_progression/`.

### Snapshot B: dedicated historical-versus-AI route comparison

- Version: `historical-vs-ai-progressive-v1`.
- Model: Ridge only.
- P7: 36 prefixes, n=2 through n=37, target `ee_percent`.
- CMC-Por aryl: 24 prefixes, n=2 through n=25, target `ee_percent`.
- Random control: 500 routes; all other routes are deterministic single
  routes under the frozen acquisition policies.
- Artifact:
  `data/expansion/pptl/historical-vs-ai-progressive-comparison.json`.

The route summaries are:

| Scope | Route | Mean prefix MAE | AUC(MAE) | n90 |
|---|---|---:|---:|---:|
| P7 | uncertainty-diversity | 9.6840 | 348.6237 | 16 |
| P7 | diversity-first | 11.1973 | 403.1044 | 24 |
| P7 | random, 500 routes | 11.2608 | 405.3877 | 29 |
| P7 | performance-first | 11.7156 | 421.7614 | 7 |
| P7 | historical order | 21.6722 | 780.1986 | not reached |
| CMC-Por aryl | uncertainty-diversity | 8.7868 | 210.8836 | 8 |
| CMC-Por aryl | diversity-first | 9.8415 | 236.1962 | 14 |
| CMC-Por aryl | historical order | 13.1549 | 315.7171 | 16 |
| CMC-Por aryl | random, 500 routes | 13.6545 | 327.7071 | 19 |
| CMC-Por aryl | performance-first | 14.5138 | 348.3300 | 23 |

Here, `n90` is the first prefix at which the median MAE reaches a 90%
reduction relative to the intercept baseline and the full-pool leave-one-out
reference. `AUC(MAE)` is the trapezoidal integral of the median MAE curve over
the stored integer prefix grid; lower values are better.

### Snapshot C: reciprocal transfer and CBAL-SSE reference

The reciprocal transfer snapshot is separately identified as
`pptl-bidirectional-matrix-v1` in
`data/expansion/pptl/matrix-ee-b5-p3-p4.json`. It contains the P7 and CMC-Por
aryl transfer directions, three feature arms (B5, P3, P4), source/target
counts, overlap counts, per-prefix rows, and matched paired diagnostics.

The repository search did not find a file or schema identifier literally named
`CBAL-SSE`. The current release therefore does not claim that one of the above
progression snapshots is the CBAL-SSE reference dataset. If CBAL-SSE refers to
an external or separately maintained snapshot, its explicit version ID,
substrate list, pathway composition, prefix range, and source artifact must be
added before that label is used in the SI. The existing
`crossfit-ee-acquisition.json` is a separate five-fold out-of-fold acquisition
dry run, with acquisition prefixes 4, 8, 16, 24, and 32; it should not be
renamed CBAL-SSE without author confirmation.

## 5. Exact acquisition and metric definitions (SI S14)

### Status: completed at implementation level

All route and acquisition decisions operate on whole substrates. The relevant
implementation is in `scripts/scope_progression.py` and
`scripts/pptl/acquisition.py`.

### Structural novelty and family coverage

For a candidate (x) and selected set (S), structural novelty is:

```text
novelty(x) = 1 − max(Tanimoto(Morgan(x), Morgan(s)) for s in S)
```

The Morgan fingerprints use the same fingerprint configuration as the locked
model feature block. Family coverage begins as the raw count-based quantity:

```text
coverage_raw(x) = 1 / (1 + number of already selected members of x's family)
```

The coverage term is min–max normalized over the current candidate set before
it is combined with the other acquisition terms. Empty selected sets are
handled by the route seed logic, not by assigning an arbitrary novelty value.

### Route weights

The stored route weights are:

```text
diversity_first       = 0.8 novelty + 0.2 coverage
uncertainty_diversity = 0.4 novelty + 0.4 uncertainty + 0.2 coverage
performance_first     = 0.5 predicted_performance
                         + 0.3 uncertainty + 0.2 novelty
```

The uncertainty term is the average of two min–max-normalized quantities when
both are available: structural novelty and model disagreement. Model
disagreement is the standard deviation of the available Ridge, Elastic Net,
and kNN predictions. The progressive acquisition implementation additionally
uses the configured predicted performance term and records the feature-arm
predictions used for each selection.

The separate sealed-panel acquisition score is:

```text
panel_score = 0.4 disagreement
              + 0.4 minmax(novelty)
              + 0.2 coverage
```

The sealed panel is then filtered to contract-valid, in-domain candidates,
ranked by predicted ee descending, and tie-broken by canonical SMILES in
ascending lexicographic order. Generator likelihood is not a decisive ranking
term, and no LLM decision is used.

### Tie-breaking and random routes

For model-guided route selection, ties are resolved by earlier source order;
the implementation uses the key `(score, -source_order)` for maximization. The
second seed substrate is the highest-novelty candidate, with earlier input
index as the tie-break. Historical order selects the minimum source order.
The sealed-panel final sort uses `(-score, canonical_smiles)`.

Random routes sample without replacement using the deterministic seed formula:

```text
random.Random(seed + replicate * 1009 + route_seed + target_seed)
```

The primary random-route summaries use 500 replicates.

### AUC and n90

For a route with median MAE values (m_n) at the stored integer prefix sizes
(n), the AUC is computed by trapezoidal integration over the actual prefix
grid:

```text
AUC(MAE) = Σ over adjacent prefixes i
           (n[i+1] − n[i]) × (m[n[i]] + m[n[i+1]]) / 2
```

No extrapolation is used beyond the last scored prefix. The `n90` reference is
the first stored prefix at which the median MAE is no greater than the
intercept-baseline value minus 90% of the baseline-to-full-pool-LOO reduction:

```text
threshold90 = baseline_mae − 0.90 × (baseline_mae − full_pool_loo_mae)
```

If no prefix reaches the threshold, `n90` is recorded as null/not reached.
The exact prefix rows, prefix count, final prefix, AUC, and n90 values are
retained in the route JSON files.

## 6. Matched transfer uncertainty and acceptance-gate evidence (SI S6 and S14)

### Status: directional and matched uncertainty evidence completed; acceptance conclusion remains limited

The guarded transfer protocol uses a whole-substrate unit, source experts,
target-only controls, and domain-aware/pooled controls. The initial source
weight is 0.5, with the source contribution capped at 0.5 total through the
first five scored post-seed reveals. Source transfer is suppressed when its
cumulative MAE is both more than one ee point and more than 10% worse than the
target-only control. Shadow predictions are retained even when the guarded
weight is suppressed.

The frozen feature arms are:

- B5: the baseline transfer arm;
- P3: B5 plus compact Stage 2p pose geometry (C1);
- P4: B5 plus C1 and the 16-feature catalyst-aware interaction block (C2).

The row-level transfer matrix has 37 scored CMC-Por-to-P7 rows and 31 scored
P7-to-CMC-Por aryl rows. The matched canonical-overlap count is 13 and those
structures are paired diagnostics only, not cold-start source training rows.

### Guarded point estimates

| Direction | Arm | Target-only MAE | Guarded MAE | Difference |
|---|---|---:|---:|---:|
| CMC-Por → P7 aryl | B5 | 11.8153 | 11.6538 | -0.1616 |
| CMC-Por → P7 aryl | P3 | 11.2758 | 10.9731 | -0.3027 |
| CMC-Por → P7 aryl | P4 | 11.0612 | 10.7413 | -0.3199 |
| P7 → CMC-Por aryl | B5 | 12.2339 | 11.7016 | -0.5324 |
| P7 → CMC-Por aryl | P3 | 12.2053 | 11.4803 | -0.7251 |
| P7 → CMC-Por aryl | P4 | 12.2083 | 11.5094 | -0.6989 |

### Random-route uncertainty

The 500-route bootstrap distributions report guarded-minus-target changes.
Negative values favor guarded transfer. The intervals are:

| Direction | Arm | MAE change, 95% interval | AUC change, 95% interval |
|---|---|---|---|
| CMC-Por → P7 | B5 | -0.230 [-0.254, -0.205] | -7.505 [-8.331, -6.633] |
| CMC-Por → P7 | P3 | -0.311 [-0.345, -0.279] | -9.803 [-11.007, -8.691] |
| CMC-Por → P7 | P4 | -0.417 [-0.451, -0.382] | -13.838 [-15.057, -12.671] |
| P7 → CMC-Por | B5 | -0.399 [-0.443, -0.356] | -11.344 [-12.627, -10.089] |
| P7 → CMC-Por | P3 | -0.460 [-0.499, -0.421] | -12.266 [-13.399, -11.207] |
| P7 → CMC-Por | P4 | -0.501 [-0.533, -0.466] | -13.453 [-14.366, -12.505] |

### Matched pose-arm paired intervals

For matched route/prefix comparisons against B5, the paired bootstrap results
are:

| Arm and direction | Paired MAE change, 95% interval | Paired AUC change, 95% interval |
|---|---|---|
| P3, CMC-Por → P7 | -0.342 [-0.400, -0.282] | -13.191 [-15.094, -11.303] |
| P3, P7 → CMC-Por | -0.347 [-0.415, -0.280] | -13.373 [-15.191, -11.682] |
| P4, CMC-Por → P7 | -0.489 [-0.550, -0.432] | -19.183 [-21.147, -17.225] |
| P4, P7 → CMC-Por | -0.099 [-0.177, -0.020] | -6.014 [-8.035, -3.933] |

The stored scaffold-bootstrap guarded-minus-target intervals are -2.208
[-4.567, -0.644] for P7 → CMC-Por and -4.596 [-7.848, -1.888] for CMC-Por
→ P7. The complete paired and scaffold results are in
`data/expansion/pptl/routes/`, `data/expansion/pptl/scaffold/`, and
`data/expansion/pptl/paired-pose-ee.json`.

The acceptance gate was intentionally not overstated. The pre-specified gate
required at least 10% early-AUC improvement in both directions, preservation
of the full curve, and no material scaffold/family negative transfer against
the controls. The available directional improvements are consistent with
beneficial transfer, but the stored results do not establish the complete
10%-in-both-directions acceptance claim. The SI should therefore retain the
directional conclusion and state explicitly that the full acceptance gate was
not declared passed.

## 7. Exact Stage 3 feature mapping and CREST cohort join (SI S11 and S13)

### Status: completed for the model matrices and P7 CREST join; CMC-Por CREST remains explicitly incomplete

### CREST calculations and join

CREST was run on the neutral, closed-shell aryl-azide substrate alone; the
porphyrin and Fe–nitrene assembly were not included. The calculation used
CREST 3.0.2 with xTB 6.7.1, GFN2-xTB, ALPB ether, a 30 kcal mol⁻¹ search
window, CREGEN uniqueness filtering, and an independent GFN2 rerank. At most
10 minima were requested. Genetic crossing was disabled for the rigid
one-member cases.

The completed P7 CREST cohort contains 40 records, each with one unique
CREGEN minimum. The join key is `substrate_id`. The 38-substrate model cohort
is the exact intersection of the completed P7 CREST records with the 38
modelled P7 IDs: `1ad` and `1an` have CREST records but are excluded from the
38-model benchmark, while `1z` is absent from the completed CREST cohort and
was already excluded from the matched benchmark. There are no missing CREST
records for the 38 modelled IDs. The four partial CMC-Por CREST directories
(`2o`, `2p`, `2q`, and `2r`) are retained as partial work and are not counted
as completed conformer results.

The CREST source/method record is `SI2/SUPPORTING_INFORMATION_FEATURE_METHODS.md`;
the record-level data are under `SI2/data/crest/` and the corresponding SI3
package paths.

### Stage 3a-alt matrix

The exact Stage 3a-alt matrix is:

`SI2/data/xtb/stage3-features/model-comparison/stage3a-alt-full-scope-training-matrix.csv`

It contains 40 records and 588 columns. The feature columns are the 567-feature
Stage 2 base block plus the 21 stage3a-alt hetero-site competition features:

```text
candidate_site_count
heteroactivated_site_count
max_competitor_binding_site_score
max_competitor_electronic_site_score
max_competitor_mechanism_risk_score
mechanism_risk_site_count
reported_alpha_heteroatom_site
reported_alpha_soft_donor_site
reported_beta_gamma_heteroatom_site
reported_binding_site_score
reported_carbonyl_alpha_site
reported_electronic_site_score
reported_heteroaryl_adjacent_site
reported_is_noncanonical_site
reported_mechanism_risk_score
reported_minus_max_competitor_binding_site_score
reported_minus_max_competitor_electronic_site_score
reported_minus_max_competitor_mechanism_risk_score
reported_nearest_acceptor_graph_distance
reported_nearest_heteroatom_graph_distance
reported_remote_binding_heteroatom_available
```

The base block contains the RDKit physicochemical descriptors, 512 Morgan bits,
candidate-site count/type metadata, reported site atom-map and hydrogen-count
metadata, site-type indicators, ring/rotatable-bond descriptors, and the
reaction-centre/site summary fields. It does not contain Stage 2 pose or CREST
features. The Stage 3a-alt-plus-Stage2p model uses the Stage 2p block and the
stage3a-alt block as separate provenance-tracked blocks; its exact output is
`data/jacs_2025/stage3/model-comparison/stage3a-alt-plus-stage2p-family-heldout-p7-modelable-metrics.json`.

The full-scope stage3a-alt comparison used 40 records, including zero-curated
`1ad` and `1z`, and excluding achiral `1an`. The Stage 2 base had LOO MAE
13.9893, RMSE 23.9270, R² -0.0585, and 30/40 within 15 points. Stage 3a-alt
had LOO MAE 13.4369, RMSE 22.9887, R² 0.0229, and 32/40 within 15 points.
The six unseen prediction rows are retained in the corresponding unseen
reports. These are in-sample/LOO development diagnostics, not external
validation.

### Stage 3a-lite

The pilot worklist contains 12 substrates, 12 constrained optimizations, and
114 candidate-site reference rows. The calculation uses GFN2-xTB/ALPB ether,
a 214-atom frozen core, policy
`stage3a-core-frozen-ligand-restrained-v1`, and force constant 1.0. Features
include final xTB energy, Fe displacement, Fe–N–C angle, N–C/H distances,
N–C–H angle, and core RMSD/displacements.

### Stage 3b intrinsic C–H BDE block

The Stage 3b record file contains 38 rows, one per modelled substrate. The
calculation uses GFN2-xTB/ALPB ether for the neutral substrate and corresponding
doublet carbon radical, with a fixed H-atom reference of
`-0.391629889244` Hartree. The record contains:

```text
absolute_intrinsic_c_h_bde
bde_competition_gap
min_absolute_intrinsic_c_h_bde
within_substrate_bde_rank
candidate_site_count
successful_site_count
failed_site_count
calibration_status = uncalibrated_xtb
```

Site-level successes, failures, and candidate-site identities are retained.
The BDE block is therefore a mechanistic ranking/diagnostic feature, not a
claim of calibrated DFT-quality BDEs.

## 8. Generation-screening breakdown (SI S15)

### Status: principal funnel complete; one 127-row scoring-table discrepancy remains to be repaired or disclosed

The frozen generator run used SMILES-RNN with five seeds
`1101, 2202, 3303, 4404, 5505`. Each seed produced 10,112 persisted rows,
giving 50,560 rows, including the 112-row per-seed overrun. No rows were
post-hoc discarded. The equal-budget deterministic enumeration comparator also
contains 50,560 raw candidates.

The generator funnel is:

| Stage | Count |
|---|---:|
| Raw generator strings | 50,560 |
| Unique canonical structures | 9,184 |
| Contract-valid structures | 563 |
| Contract-valid and in-domain structures | 483 |

The enumeration comparator is:

| Stage | Count |
|---|---:|
| Raw enumeration candidates | 50,560 |
| Unique canonical structures | 25,955 |
| Contract-valid structures | 18,545 |
| Contract-valid and in-domain structures | 18,350 |

The production funnel reasons are recorded in
`data/expansion/pptl/funnel-production.csv` and can overlap because a row can
trigger more than one diagnostic:

| Reason code | Count |
|---|---:|
| conservative ortho two-carbon tether not detected | 48,746 |
| duplicate canonical structure | 41,269 |
| RDKit parse failed | 107 |
| five-member C–N closure not detected | 77 |

The enumeration funnel reasons are:

| Reason code | Count |
|---|---:|
| duplicate canonical structure | 24,605 |
| aryl azide not detected | 14,440 |

Applicability-domain counts are recorded separately from contract validity. The
production AD table has 47,317 in-domain rows and 3,243 out-of-domain or
unscored rows across the full raw table; only 483 rows are both contract-valid
and in-domain. The enumeration AD table has 41,427 in-domain rows and 9,133
out-of-domain/unscored rows; only 18,350 are both contract-valid and in-domain.

The principal generation statistics are:

| Statistic | Generator | Enumeration |
|---|---:|---:|
| Mean pairwise Tanimoto, 500-sample diagnostic | 0.31249 | 0.41197 |
| Mean pairwise distance | 0.68751 | 0.58803 |
| Mean maximum reference similarity | 0.48725 | 0.45724 |
| Novelty proxy | 0.51275 | 0.54276 |
| Mean predicted ee | 56.017 | 75.305 |
| Predicted-ee SD | 7.459 | 6.569 |
| Predicted-ee median | 55.637 | 75.824 |
| Predicted-ee 90th percentile | 64.934 | 83.280 |
| Maximum predicted ee | 83.302 | 96.452 |
| Mean predicted ee of top 10 | 69.411 | 85.806 |

The five generator morphology categories contain 192 heteroatom-rich, 117
flexible/sp3-rich, 113 fused/polycyclic, 34 diaryl/bicyclic, and 27 simple
aryl-tether structures. The 16-member development panel and sealed 8+8 panel
were selected after contract, applicability, predicted-ee, uncertainty,
information-gain, and morphology-diversity filters; no outcome was revealed.

### Explanation of the 127 enumeration candidates

The final enumeration EE table currently contains 50,000 rows rather than the
full 50,560-row equal-budget table. The missing IDs are the final 560 rows,
`enum-050000` through `enum-050559`. Among those missing rows, 127 are both
contract-valid and in-domain, six are contract-valid but out-of-domain, and
the remainder are invalid/duplicate rows. Thus, the 127 candidates were not
chemically rejected; they are in-domain, eligible enumeration candidates for
which a prediction row was not written because the EE scoring artifact was
truncated at 50,000 rows.

This is the one generation-screening record that still requires a concrete
release action. Either:

1. rebuild and deposit the complete 50,560-row enumeration EE table; or
2. retain the current table but state explicitly that 127 eligible in-domain
   candidates were not scored and are excluded from all scored-count totals.

The underlying raw enumeration, AD, funnel, and summary files already permit
the discrepancy to be audited.

## 9. Sealed 8+8 proposal-panel inventory (SI S14–S15)

### Status: completed and sealed

The panel contains eight copilot/generator candidates and eight comparator/
enumeration candidates. Each branch contains four round-A and four round-B
records. All rows are `in_domain`; `outcome_ee` is blank and
`outcome_revealed=false`.

| ID | Branch | Round | Canonical SMILES | Predicted ee |
|---|---|---|---|---:|
| rnn-1101-00057 | copilot | A | `COC(=O)c1ccc(CCc2ccccc2N=[N+]=[N-])cc1` | 83.3021 |
| rnn-4404-07513 | copilot | A | `[N-]=[N+]=Nc1ccccc1CCc1ccc(O)cc1` | 82.7366 |
| rnn-5505-08915 | copilot | A | `[N-]=[N+]=Nc1ccccc1CCc1cccc(O)c1` | 81.3699 |
| rnn-4404-05903 | copilot | A | `Cc1ccc(CNC(=O)OCCc2ccccc2N=[N+]=[N-])cc1` | 78.1930 |
| rnn-2202-08414 | copilot | B | `CN(C)C(=O)Oc1cc(CCc2ccccc2N=[N+]=[N-])cc(C(=O)O)c1` | 77.9428 |
| rnn-1101-03461 | copilot | B | `[N-]=[N+]=Nc1ccccc1CCc1ccccc1` | 77.8171 |
| rnn-2202-01263 | copilot | B | `[N-]=[N+]=Nc1ccccc1CCc1ccncc1` | 77.6354 |
| rnn-1101-07965 | copilot | B | `[N-]=[N+]=Nc1ccccc1CCc1cccnc1` | 76.1076 |
| enum-035788 | comparator | A | `[N-]=[N+]=Nc1cc(CCO)ccc1CCc1cc(-c2ccoc2)cc(-c2ccsc2)c1` | 96.4522 |
| enum-034990 | comparator | A | `[N-]=[N+]=Nc1cc(CCO)ccc1CCc1cc(-c2ccsc2)cc(C(F)(F)F)c1` | 95.3734 |
| enum-034989 | comparator | A | `[N-]=[N+]=Nc1cc(CCO)ccc1CCc1cc(-c2ccoc2)cc(C(F)(F)F)c1` | 94.8609 |
| enum-034664 | comparator | A | `Cc1cc(CCc2ccc(CCO)cc2N=[N+]=[N-])cc(C(F)(F)F)c1` | 94.7864 |
| enum-035256 | comparator | B | `Cc1ccccc1-c1cc(CCc2ccc(CCO)cc2N=[N+]=[N-])cc(-c2ccsc2)c1` | 94.7551 |
| enum-035218 | comparator | B | `[N-]=[N+]=Nc1cc(CCO)ccc1CCc1cc(-c2ccc(Cl)cc2)cc(-c2ccsc2)c1` | 94.3682 |
| enum-035255 | comparator | B | `Cc1ccccc1-c1cc(CCc2ccc(CCO)cc2N=[N+]=[N-])cc(-c2ccoc2)c1` | 94.2425 |
| enum-034914 | comparator | B | `[N-]=[N+]=Nc1cc(CCO)ccc1CCc1cc(Cl)cc(-c2ccsc2)c1` | 93.8822 |

The authoritative CSV is
`data/expansion/pptl/sealed-prospective-panel.csv`. Its lock file is
`data/expansion/pptl/sealed-prospective-panel-lock.json`, which records the
counts, branch/round allocation, SHA-256, and unrevealed-outcome status.

## 10. Catalyst-to-source attribution in the main text

### Status: source-paper provenance completed; shared ABAB/hydrogen-bond-donor wording still requires author confirmation

The P7 reference is the doublet α-Fe(IV)-aminyl intermediate `2B` from the
JACS 2025 source package. The source record is `jacs-2025-si`, with the
relevant SI pages documented as S63, S68, and S115–S122. The reference geometry
uses BP86/def2-SVP gas-phase geometry followed by TPSSh/def2-TZVP-D3BJ/SMD
ether single-point treatment. The Fe–N distance in the stored reference is
1.703457 Å, with atom maps 47 and 215. The fixed-core policy is the
porphyrin–metal–nitrene core.

The CMC-Por reference is `(S,R)-cmcporFeCl`, Fe(IV)-aminyl `4B1`, from the
Angewandte Chemie SI. The source record is `anie-2023-si`, SI pages S61–S62
and S69–S73, with Cartesian coordinates for `4B1`. The stored method is
UωB97XD/LanL2DZ for Fe and 6-31G* for the other atoms, gas phase, quartet
`4B1`, neutral-coordinate assumption. The Fe–N distance is 1.832774 Å, with
atom maps 189 and 191; chloride is atom 190 and the substrate anchor is atom
192 S from the sulfonyl `4B1` record. The aryl-scope calculations use the S
anchor as a geometry proxy because a dedicated aryl Fe–aminyl reference was not
available.

These records establish the catalyst-specific structures and source-paper
assignments. A repository search did not find an explicit author confirmation
for a shared “ABAB/hydrogen-bond-donor” description. The main text should not
present that shared description as confirmed until the author-check note is
resolved. The chemically supported wording is that both systems are
Fe-aminyl/porphyrin reference geometries with separately sourced catalyst
structures and separate geometry assumptions.

## 11. Final reproducibility and release details (SI S9 and S14–S15)

### Status: local replay package and manifests completed; public release metadata still open

### Frozen package and manifests

The SI3 package manifest is `SI3/manifest.json`. It uses
`si3-package-manifest-v1`, contains 612 files, and records 301,068,233 bytes
with file-level SHA-256 entries. The raw-data completeness audit reports zero
hash mismatches for the deposited non-XYZ scientific files. The package
contains raw record inputs, learning curves, model predictions and metrics, pose
arrays, transfer replicates, generator streams, proposal ledgers, and funnel
reports. Large XYZ/coordinate collections are handled separately in the data
package policy.

### Environments

The primary analysis environment is recorded as Python 3.14.6 with RDKit
2026.3.4, SciPy 1.18.0, scikit-learn 1.9.0, and LightGBM 4.7.0. The frozen
generator environment is Python 3.11.16 with PyTorch 2.13.0 and RDKit
2026.3.5. The generator environment is in `requirements-generator.txt`; the
analysis environment is in `requirements.txt` and the methods/data-availability
record at `SI3/procedure/source-docs/output/supporting-information/manuscript-methods-and-data-availability.md`.

SMILES-RNN is pinned to commit
`c8ee705961b4411707c69f73d309c1cf61208b95` with checkpoint
`ChEMBL28pur.ckpt`, SHA-256
`bf0882cc1f35743c6226001129a1031e79ad25f357f903d02f953ed0e5d0d289`.
PromptSMILES is pinned to version 1.7.2. The upstream generator licenses are
SMILES-RNN MIT and PromptSMILES Apache-2.0. Project code/data license fields
remain placeholders and must be selected before public release.

### Exact replay commands

From the repository root, the locked contract and bidirectional analysis can
be replayed with:

```bash
python scripts/pptl/validate_contract.py \
  --contract scripts/pptl/pptl-contract.json \
  --output scripts/pptl/contract-validation.json

python scripts/pptl/build_overlap_ledger.py \
  --p7-records data/jacs_2025/stage2/curated-reaction-records.jsonl \
  --cmcpor-records data/expansion/catalyst_rerun/cmcpor/stage2-records.jsonl \
  --output data/expansion/pptl/canonical-overlap-rebuilt.json

python scripts/pptl/run_bidirectional_matrix.py \
  --p7-records data/jacs_2025/stage2/curated-reaction-records.jsonl \
  --cmcpor-records data/expansion/catalyst_rerun/cmcpor/stage2-records.jsonl \
  --p7-stage2p data/jacs_2025/stage2/features/stage2p-features.jsonl \
  --cmcpor-stage2p data/expansion/catalyst_rerun/cmcpor_uff_full/stage2p/features/stage2p-features.jsonl \
  --p7-catalyst-features data/jacs_2025/stage2/features/pose-interaction.jsonl \
  --cmcpor-catalyst-features data/expansion/catalyst_rerun/cmcpor_uff_full/stage2/features/pose-interaction.jsonl \
  --arms B1,B2,B3,B4,B5,P0,P1,P2,P3,P4 \
  --output data/expansion/pptl/rebuilt-bidirectional-ee-matrix.json

python scripts/pptl/build_model_progression_tables.py
python scripts/pptl/build_supporting_information.py
```

The generator is not regenerated during analysis replay. Its deterministic
outputs are frozen in `data/expansion/pptl/generator-freeze-config.json` and
the raw production/enumeration streams. The freeze configuration records the
five seeds, complete 50,560-row batches, grammar fixture, deterministic gates,
raw-string retention, rejection reasons, and prediction-only status.

### Executable and test records

The PPTL contract is `scripts/pptl/pptl-contract.json`. The repository contains
the executable validation, overlap-ledger, transfer-matrix, progression, and
SI-build scripts, together with the corresponding JSON/CSV artifacts. The
current evidence package does not contain a separately named executable or test
record for “CBAL-SSE”; that identifier must be mapped to a concrete script and
artifact before it is cited in the SI. Until then, the SI should cite the
locked PPTL contract and the exact replay commands above rather than claiming a
CBAL-SSE replay record.

### Remaining release fields

The following are not yet available as final public-release values:

- GitHub repository URL;
- frozen public release tag or commit identifier;
- project code license;
- project data/license terms;
- final updated manifest after any release-only additions;
- permanent archive DOI;
- explicit CBAL-SSE executable/test artifact, if CBAL-SSE is a required named
  reference dataset;
- author confirmation of the shared ABAB/hydrogen-bond-donor description;
- repaired or explicitly documented full 50,560-row enumeration EE scoring
  table.

The local package is therefore reproducible from the repository, but the SI
should describe public availability as pending until those release metadata and
the 127-row enumeration discrepancy are resolved.

## Recommended concise SI conclusion

The remaining limitations are documentary and release-related rather than a
need for new experiments. The 38-substrate rerun, exact cohort/split
membership, progression and transfer ledgers, route/acquisition definitions,
matched transfer uncertainty, Stage 3 feature provenance, CREST join, and
sealed 8+8 inventory are now supported by frozen row-level artifacts. The
claims should remain limited to the analyses actually completed: retrospective
prediction, directional transfer evidence, and prediction-only candidate
generation. Public-release metadata, author confirmation of the catalyst
description, a named CBAL-SSE artifact if required, and the 127-row
enumeration scoring-table repair remain the final actions before the SI can be
described as fully release-complete.
