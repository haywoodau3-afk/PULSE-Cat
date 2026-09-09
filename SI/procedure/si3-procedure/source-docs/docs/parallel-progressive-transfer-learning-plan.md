# Bidirectional Parallel Progressive Transfer Learning Development Plan

Status: accepted development plan  
Date: 2026-09-01

## Purpose and publication niche

This project is a fully computational, low-data demonstration of a chemist-in-the-loop workflow for iron-porphyrin C–H amination. The primary study treats the completed P7 and CMC-Por catalyst domains as reciprocal sources and targets:

* P7 aryl → CMC-Por aryl; and
* CMC-Por aryl → P7 aryl.

Each target is revealed one whole substrate at a time while the source domain remains frozen. EE is the primary endpoint; isolated yield is a separate secondary endpoint. D4-Por is deliberately deferred until this reciprocal study has a stable contract and reproducible results.

The publishable niche is not universal predictive superiority over GNNs. It is a resource-aware **AI-coworker** workflow that quantifies how much labelled chemistry is needed, chooses the next informative calculation, shows which source is trusted, and turns off harmful transfer. It is designed for small, structured datasets and modest CPU/RAM budgets, where a high-capacity neural model is not the appropriate default.

## Decisions fixed after grilling

1. **Study direction:** bidirectional P7↔CMC-Por is primary; D4 is a later unseen-target extension.
2. **Progression:** source rows are frozen and complete; target labels are revealed by whole substrate. A both-growing budget study is optional and secondary.
3. **Pathway:** aryl↔aryl is the primary comparable cohort. CMC-Por sulfonyl records are a separate cold/mismatched-pathway control and never silently enter the aryl model.
4. **Overlap:** canonical shared compounds are excluded from source training for cold-start generalization metrics. The same pairs are retained only in a separately labelled paired diagnostic.
5. **Pose panel:** use the 13 canonical P7–CMC-Por shared compounds after map-insensitive canonicalization for pose overlays and domain-shift diagnostics, subject to valid persisted pose artifacts.
6. **Evidence boundary:** all conclusions are retrospective, label-masked computational replays. No wet-lab acceleration or GNN head-to-head claim is made.

## Existing data and constraints

* P7: 41 reaction rows, 40 numeric ee labels, 41 yield labels.
* CMC-Por: 50 rows with numeric ee/yield; its aryl cohort is the primary comparison and its sulfonyl cohort is isolated as a pathway control.
* Map-insensitive canonicalization of the current committed ledger yields 13 P7–CMC-Por pairs. Exact paper record IDs are not interchangeable with canonical compound identity.
* Existing progressive learning is whole-substrate sequential progression with fixed catalyst/condition domains. Preserve that unit and its locked route/audit conventions.
* The existing transfer pilot is diagnostic only: it is narrow, includes D4, and must not be presented as the primary reciprocal result.
* Existing pose results are mixed. Stage 2p is the primary compact pose block; Stage 2pp/Stage 2″ remains exploratory and cannot be selected post hoc.

## Scientific hypotheses

**H1 — early data efficiency.** At matched target-label prefixes, guarded transfer lowers EE MAE and progressive MAE area relative to a target-only model.

**H2 — direction asymmetry.** P7→CMC-Por and CMC-Por→P7 need not have equal gains; the difference is evidence about domain relatedness rather than a nuisance.

**H3 — safe reuse.** A guarded ensemble is safer than unconditional pooling because it suppresses a source whose prequential loss is worse than target-only.

**H4 — incremental pose value.** Stage 2p or a compact catalyst-aware block adds information beyond full and reduced 2D features under equal labels, splits, estimator capacity, and dimensional controls.

**H5 — geometric explanation.** Paired pose similarity and reaction-corridor summaries explain transfer gain, disagreement, or negative transfer even when they are not predictive features.

Yield repeats these hypotheses independently and cannot rescue a failed EE claim.

## Data and leakage contract

### Cohorts and labels

Keep catalyst, condition, pathway, paper, record role, and missing-status provenance on every row. A missing ee is excluded only from the ee fit/score; it is never converted to zero. Yield and ee have separate prefixes, models, losses, and metrics.

Primary cohorts:

| Direction | Source | Target | Pathway |
|---|---|---|---|
| D1 | P7 (`fe-p7-cl`) | CMC-Por (`cmcpor-fecl`) | aryl |
| D2 | CMC-Por (`cmcpor-fecl`) | P7 (`fe-p7-cl`) | aryl |

Secondary controls: CMC sulfonyl as a separate cold/mismatched-pathway analysis; source-label subsampling and outcome-permutation controls; optional both-growing budget simulation.

### Canonical compound grouping

Canonicalize substrate SMILES with one frozen RDKit procedure that removes atom-map labels before canonicalization. Persist `canonical_compound_group`, `split_group`, family/scaffold group, and provenance. For each direction:

1. identify the 13 shared canonical compounds and record the valid subset actually present after pathway filtering;
2. remove the target counterpart from the source training rows for cold-start metrics;
3. score a warm-start diagnostic that explicitly allows the pair, but never mix it with the headline cold-start number;
4. keep paired rows available for pose overlays and catalyst-domain diagnostics only.

CMC's current aryl family label is coarse. Use a frozen scaffold/group holdout for generalization and report the coarse family result as a limited diagnostic. Do not invent family labels after observing outcomes.

### Locked evaluation

Every arm uses identical group splits, target prefixes, route seeds, estimator grid, and prediction bounds. Feature scaling, projection, feature selection, and hyperparameter choice occur inside training folds. The final locked audit is untouched by acquisition, trust updates, or arm selection.

## Frozen representation ladder

The primary canonical 2D baseline is 15 RDKit descriptors plus radius-2 Morgan (1,024 bits). Historical 35+512 and 2,048-bit contracts are sensitivity analyses only.

| Arm | Features | Role |
|---|---|---|
| B0 | training-fold mean | no-feature reference |
| B1 | six chemist-readable RDKit scalars | minimal low-resource baseline |
| B2 | all 15 RDKit scalars | compact descriptor baseline |
| B3 | B2 + 128-bit Morgan | reduced fingerprint |
| B4 | B2 + 256-bit Morgan | dimension-matched 2D control |
| B5 | B2 + 1,024-bit Morgan | full 2D reference |
| P0 | Stage 2p, 248 columns | pose-only diagnostic |
| P1 | B1 + P0 | minimal 2D plus pose |
| P2 | B5 + raw P0 | legacy pose diagnostic only |
| P3 | B5 + compact C1 geometry | compact pose upgrade |
| P4 | B5 + C1 + catalyst-aware C2 block | transfer-specific pose tier |
| P5 | B5 residual head from C1+C2 | preferred correction model |
| P6 | B5 with pose/domain source gating | preferred AI-coworker integration |
| PX | Stage 2″ alone/addition | exploratory occupancy/flexibility |

Reduced RDKit must mean either the fixed six-feature B1 core or fold-local reduction/projection with predeclared dimensions 16/32/64. It must not mean a post-hoc best subset.

Required controls: B4 dimension match; B5 plus 248 random-noise columns over declared seeds; source-permuted pose rows inside each training fold; fold-local PCA/random projection to common dimensions. Separate reaction-centre metadata from actual pose-derived columns.

## Model arms and guarded transfer

At every target prefix, fit:

* **E0 target-only:** revealed target labels only;
* **E1 source-only P7:** zero-shot and target-adapted variants;
* **E2 source-only CMC-Por:** zero-shot and target-adapted variants;
* **E3 combined source:** pooled domain-indicator model;
* **E4 guarded ensemble:** E0 plus E1–E3 with online source trust.

Primary estimator is standardized Ridge (`alpha=10`, predictions clipped to 0–100). Elastic Net and Tanimoto kNN are challengers. Transfer mechanisms remain separately named: zero-shot, pooled domain-indicator, source-coefficient regularization, residual correction, and guarded ensemble.

Before each held-out target label is revealed, every eligible expert predicts it. After reveal, update separate EE/yield losses. Start with 0.5 target weight and distribute 0.5 across source experts using frozen label-independent candidate coverage and reciprocal grouped-transfer reliability. Use exponential loss updates; cap total source weight at 0.5 through five scored post-seed reveals. Set a source's active weight to zero when its cumulative MAE is both >1 point and >10% worse than E0, while retaining shadow predictions for diagnostics.

Record unguarded/guarded weights, eligibility, cumulative losses, disagreement, and the exact target row at every reveal.

## Progressive replay and acquisition

Use the existing two-substrate central-plus-diverse seed and reveal one complete substrate at a time. Every fixed-prefix arm receives the same order, making the transfer-gain curve a paired comparison. Report uncertainty-plus-diversity as the systematic route, with historical and 500-replicate random routes as controls.

The AI-coworker policy may choose independently from the locked candidate pool using:

```text
0.4 * model/source disagreement + 0.4 * novelty + 0.2 * family coverage
```

At each step write the selected substrate, two alternatives, predicted EE/yield, uncertainty, source weights, nearest-source similarity, negative-transfer warning, structural novelty, and expected information value. This is a recommendation to reveal an existing computational label, not a claim of autonomous laboratory execution.

## Pose generation and paired overlays

Use persisted P7 and CMC-Por Stage 2p artifacts under one frozen UFF/constraint contract. Do not fabricate missing poses and do not infer electron density from occupancy fields. Record attempted, valid, retained, failed, and underfilled counts plus CPU time and storage.

For each of the 13 reconciled paired compounds, align poses in a reaction-centred frame using nitrene N, transferred H, reactive C, and Fe–N axis where available. Produce catalyst-stripped occupancy overlays, pairwise difference maps, representative low/high pose overlays, and compact contact/corridor tables. Quantify Wasserstein distance, Jensen–Shannon divergence, centroid displacement, corridor overlap, and contact-distance deltas. Treat associations with source error or transfer gain as explanatory unless they pass the frozen P3/P4 ablation.

## Metrics and predeclared gates

EE primary metrics: early-prefix MAE AUC, full progressive MAE AUC, scaffold/group-held-out MAE, locked-audit MAE where viable, labels required to reach a reference threshold, calibration, rank correlation, and family/scaffold negative-transfer rate. Yield is a parallel secondary table.

Use paired bootstrap intervals over held-out groups and report route distributions, not the best seed. The primary EE transfer gate requires the guarded ensemble to:

1. reduce early-prefix MAE AUC by ≥10% versus E0;
2. improve or preserve full-curve AUC;
3. show no material scaffold/family negative transfer;
4. beat size-matched and mismatched-source controls;
5. reproduce in both directions or clearly report direction-specific asymmetry.

Pose is adopted as a predictive tier only if it lowers held-out MAE by ≥1 ee point, has a paired interval favouring augmentation, lowers progressive AUC or label requirement by ≥10%, beats dimension-matched/random/permuted controls, and introduces no material negative transfer. If pose beats only reduced RDKit, claim compact representation—not superior pose information.

Resource claims require CPU-hours, wall time, peak RAM, storage, pose failure rate, feature time per substrate, fit time per prefix, and labels consumed. Report accuracy per label and per compute.

## Implementation phases

### Phase 0 — bidirectional contract freeze

Update `scripts/pptl/pptl-contract.json` with D1/D2, aryl primary, sulfonyl control, canonical overlap policy, representation ladder, gates, and D4 deferred status. Validate P7/CMC paths without requiring D4 files. Write `data/expansion/pptl/publication-ledger-lock.json` with SHA-256 hashes and a lock digest.

### Phase 1 — identity ledger and splits

Generate the canonical overlap ledger, pathway filters, split/scaffold groups, locked target prefixes, and cold/warm-start manifests. Reconcile the 13 pairs and document any SMILES mismatch. The lock artifact is the sole authority for files used by publication runs.

### Phase 2 — target-only replays

Run B0–B5 target-only progression independently for CMC-Por aryl and P7 aryl. Produce deterministic curves, audit predictions, and resource ledgers.

### Phase 3 — reciprocal transfer experts

Run E1–E3 in both directions with overlap exclusion, source-volume controls, and grouped/scaffold-held-out scoring. Reconcile every prediction to a target prefix.

### Phase 4 — guarded ensemble

Implement prequential weights, source caps, negative-transfer suppression, shadow predictions, and separate EE/yield histories. Assert a synthetic harmful-source fixture.

### Phase 5 — acquisition/co-worker outputs

Run fixed-prefix, historical, random, and independent uncertainty-plus-diversity routes. Emit recommendation artifacts and policy metrics.

### Phase 6 — upgraded pose ablation and maps

Run raw P0, compact C1, catalyst-aware C2, residual P5, and gating P6 under target-only and guarded transfer, equal-dimension controls, paired overlays, numeric maps, and compute accounting. Raw P0 remains diagnostic only. The applied C1 implementation is `scripts/pptl/run_pose_upgrade.py`; C2 is now enabled from aggregated `pose-interaction.jsonl` records through `run_bidirectional_matrix.py` with the catalyst-feature paths declared in the contract.

### Phase 7 — report and D4 extension stub

Build the final computational report with pass/fail/unsupported status for each hypothesis. Leave a validated D4 extension contract and explicit missing-input checklist, but do not block the primary study on D4 geometry or labels.

## Required artifacts and tests

Scripts under `scripts/pptl/` should produce versioned JSON/JSONL/CSV/Markdown artifacts for contract validation (`validate_contract.py`), canonical overlap (`build_overlap_ledger.py`), publication locking (`freeze_publication_ledger.py`), reciprocal replays (`run_bidirectional.py`, `run_bidirectional_matrix.py`), scaffold holdout (`run_scaffold_holdout.py`), paired scaffold bootstrap (`bootstrap_scaffold_metrics.py`), fixed-prefix predictions, expert weights, acquisition events, feature arms, pose ablations, compact/residual pose upgrade (`run_pose_upgrade.py`), domain maps, resource ledger, and final report.

Tests must cover canonicalization and overlap exclusion, reproducible publication-ledger locking, aryl filtering, cross-catalyst split leakage, matched prefixes, prequential prediction, separate EE/yield weights, harmful-source suppression, deterministic feature dimensions, missing-pose fail-closed behavior, pose permutation/random controls, acquisition decomposition, map reproducibility, and metric reconciliation.

## Allowed conclusions

* If both directions pass: guarded reciprocal transfer improves computational low-data development under this declared chemistry contract.
* If only one direction passes: transfer is direction- and domain-related; report the asymmetry.
* If guarding helps but AUC does not: the workflow demonstrates transfer safety, not data-efficiency superiority.
* If pose helps only prediction, only acquisition, or only explanation: make that narrower claim.
* If all pose ablations fail: retain the Tier 1 RDKit workflow as canonical and report the negative result.
* Current route evidence supports P4 as the primary pose-transfer tier, with P3 retained as the compact ablation and yield kept secondary.
* If EE passes and yield fails: retain an EE-specific claim and report yield separately.
* Do not claim GNN superiority, wet-lab acceleration, universal catalyst transfer, or electron-density learning without new evidence.

## Publication structure

1. Small-data catalyst development and AI-coworker motivation.
2. Existing P7 and CMC-Por progressions.
3. Reciprocal fixed-prefix transfer design and overlap-safe splits.
4. Guarded source trust and negative-transfer control.
5. Bidirectional transfer-gain curves and acquisition efficiency.
6. Full/reduced RDKit versus Stage 2p pose ablations.
7. Paired pose overlays explaining catalyst-domain similarity.
8. Compute/data-resource accounting and limitations.
9. Deferred D4 extension and computational-only evidence boundary.
