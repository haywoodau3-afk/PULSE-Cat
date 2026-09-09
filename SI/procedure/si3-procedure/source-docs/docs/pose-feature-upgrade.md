# Pose-feature upgrade: from raw augmentation to transfer-aware correction

Status: accepted upgrade specification  
Date: 2026-09-01

## Observed failure mode

The current Stage 2p block contains 248 continuous, highly correlated summaries for approximately 33–40 labelled substrates. It is catalyst-stripped, uses UFF-ranked geometric proxies, fixes the reported reactive site, and is concatenated directly with B5 (15 RDKit descriptors plus 1,024 Morgan bits). In the reciprocal progressive replay, B5+Stage 2p is worse than B5 in both directions. The independent single-domain pose experiments can still show local gains because they do not face the same source-domain shift, prefix scarcity, and online trust problem.

This is evidence against the current feed, not proof that all pose information is useless.

## Upgrade hypothesis

Pose information should help by explaining catalyst-conditioned residuals and source applicability, not by replacing molecular identity features. The upgraded feed therefore has three roles:

1. **Compact geometry:** a low-dimensional, stable summary of attack-corridor geometry.
2. **Catalyst-aware interaction:** explicit catalyst–substrate contact and pocket features.
3. **Transfer correction/gating:** a residual head and source-trust signal evaluated after cross-fitted B5 predictions.

The raw Stage 2p block remains an exploratory diagnostic and is never selected as the headline block after seeing results.

## Frozen feature tiers

### C0 — B5 reference

The existing 15-descriptor plus 1,024-bit Morgan representation.

### C1 — compact Stage 2p geometry (primary upgrade)

Build at most 32–64 features from the current Stage 2p names:

- N···H and N···C radial/axial means, robust spread, and upper quantiles;
- directed N→H and H→N corridor fractions;
- attack-axis symmetry and antisymmetry;
- top-100 versus bottom-100 differences;
- Wasserstein/Jensen–Shannon contrasts;
- pose stability and underfilled-pose indicators when persisted.

Use fold-local variance filtering, correlation clustering, and optional PCA/PLS. Never select columns using the complete labelled set.

### C2 — catalyst-aware interaction block

Persist a small block of catalyst-conditioned quantities:

- Fe–N axis and catalyst–substrate contact distances;
- ligand-side approach asymmetry;
- pocket openness/steric crowding;
- corridor obstruction by catalyst atoms;
- catalyst-conditioned low/high pose contrasts;
- pose failure and underfill indicators.

P7 and CMC-Por must use the same definitions and force-field/constraint protocol. The existing `pose-interaction.jsonl` files contain repeated ranked-pose rows, so the implemented feed first averages numeric leaves by substrate and then retains 16 stable contact/axis/steric summaries. Missing catalyst-aware features fail closed; they are not replaced by zeros.

### C3 — cross-catalyst pair/domain features

For the 13 canonical paired compounds, calculate reaction-frame distances and source-to-target prototype distances. These are diagnostic unless used through the frozen transfer-gating contract. They must not be treated as extra labels.

## Model integration

Evaluate four integration modes:

1. `B5 + C1` direct compact augmentation;
2. `B5 + C1 + C2` direct catalyst-aware augmentation;
3. `B5 residual ← C1+C2`, where the pose head predicts cross-fitted B5 residuals;
4. `B5 + guarded source gating`, where pose/domain similarity modifies source trust but not the B5 target prediction.

The residual and gating modes are the preferred publication candidates because they preserve the strong B5 substrate baseline and use pose where it is mechanistically most plausible: explaining domain-specific deviations.

## Required controls and gates

Run C0–C3 under identical scaffold-held-out folds, fixed prefixes, 500 random routes, and separate EE/yield scoring. Include equal-dimensional random features and substrate-permuted pose rows.

Adopt a pose tier only if it:

- improves scaffold-held-out EE MAE by at least 1 point or early-prefix EE AUC by at least 10% versus B5;
- has a paired bootstrap interval excluding zero;
- beats random and permuted controls;
- has no material scaffold-level negative transfer;
- remains beneficial or safely gated in both transfer directions.

If these gates fail, retain pose as a domain-shift explanation or acquisition diagnostic and report the negative predictive result.

## Computational implementation order

1. Freeze and persist compact C1 feature names and provenance.
2. Add C2 catalyst-aware persistence and fail-closed validation.
3. Implement cross-fitted B5 residual and source-gating evaluators.
4. Re-run the reciprocal scaffold, route, and pose-control suites.
5. Update the final report with effect sizes, intervals, failed arms, and resource cost.

No feature or integration mode is promoted because it produces a lower score on one split.

## First applied replay (2026-09-01)

The C1 selector was applied to the publication ledgers. It retains 44 pose
features per substrate and produces a 1,083-column P3 matrix (1,039 B5
structure columns plus C1), compared with 1,287 columns for the raw P2 arm.
The reciprocal fixed-prefix EE replay is persisted at
`data/expansion/pptl/matrix-ee-b5-p2-p3.json` and the residual experiment at
`data/expansion/pptl/pose-upgrade-ee.json`.

The first result supports the upgrade direction but not a universal pose claim:

| Direction | B5 target-only MAE | P3 target-only MAE | B5 guarded MAE | P3 guarded MAE |
| --- | ---: | ---: | ---: | ---: |
| P7 → CMC-Por aryl | 12.234 | 12.205 | 11.702 | 11.480 |
| CMC-Por → P7 aryl | 11.815 | 11.276 | 11.654 | 10.973 |

Adding the aggregated 16-feature C2 catalyst-interaction block gives a
1,099-column P4 arm. In the matched EE replay, P4 guarded MAE is 11.509 for
P7 → CMC-Por and 10.741 for CMC-Por → P7. Thus C2 is slightly less effective
than C1 in the first direction and slightly better in the reverse direction;
it is a mechanistic transfer tier, not a universally dominant representation.

The compact block therefore improves both reciprocal fixed-prefix EE scores in
this replay, with the larger target-only reduction in CMC-Por → P7. The
residual correction is direction-dependent: it improves P7 → CMC-Por
(target-only MAE 12.234 → 12.021; guarded 11.702 → 11.412), but not
CMC-Por → P7 (11.815 → 12.323 for target-only). This is exactly why the
publication arm must retain guarded source trust and report both directions,
rather than presenting a one-direction or one-split pose win.

The matched-control runs with equal-dimensional random and substrate-permuted compact blocks are
persisted in `data/expansion/pptl/pose-controls-ee.json`; both controls lose
the compact arm in the guarded replay. This supports the interpretation that
the compact improvement is not merely a dimension-count effect. The matched
route bootstrap below supplies the uncertainty interval; the prespecified
promotion gate remains unresolved because the relative effect is below 10% and
the scaffold intervals are not conclusive.

The 500-route matched bootstrap supplies paired uncertainty intervals for the
label-efficiency comparison, but it does not pass the prespecified 10% relative
early-AUC gate. Relative to B5, the guarded AUC delta (pose minus B5) is:

| Pose arm | CMC-Por → P7 | P7 → CMC-Por |
| --- | ---: | ---: |
| P3 compact | −13.19 [−15.09, −11.30] | −13.37 [−15.19, −11.68] |
| P4 compact + catalyst interaction | −19.18 [−21.15, −17.23] | −6.01 [−8.03, −3.93] |

All matched-route intervals exclude zero, but the mean relative AUC reductions
are about 4.3% (CMC-Por → P7) and 1.6% (P7 → CMC-Por), both below the 10%
promotion threshold. The scaffold-paired bootstrap is more
conservative: P3 target-only improvement is significant for P7 → CMC-Por but
not the reverse; neither P4 guarded scaffold interval excludes zero. The
combined evidence supports reporting P4 as a conditional transfer-pose tier
and P3 as its compact ablation, with the claim framed around directional
early-label diagnostics rather than universal final-model accuracy.

Yield remains secondary. The missing P7 `1an` Stage2p geometry has now been
generated by `scripts/generate_stage2p_missing.py` from its checked Stage 1
pose ensemble without adding an EE label.
The yield replay is persisted at `data/expansion/pptl/pose-upgrade-yield.json`.
It does not show a pose gain: yield is therefore retained as a separate
secondary outcome and cannot be used to rescue an EE claim.
