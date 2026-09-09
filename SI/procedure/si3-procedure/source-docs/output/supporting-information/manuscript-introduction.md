# Introduction

Defining the substrate scope of a catalytic reaction is a sequential learning
problem. Each additional experiment must provide a useful synthetic result
while also improving understanding of the chemical space in which the catalyst
operates. This challenge is particularly important for asymmetric reactions,
where small changes in substrate structure, conformation, or catalyst–substrate
geometry can produce substantial changes in enantioselectivity. Conventional
scope development is usually guided by chemical intuition and historical
ordering, but these choices do not necessarily maximize the information gained
from a limited experimental budget. A computational framework that learns
progressively from completed substrates, distinguishes two-dimensional
structure from three-dimensional pose information, and transfers knowledge
carefully between related catalysts could therefore make scope development
more systematic and data-efficient.

Here, we established such a framework using two independently curated iron
porphyrin systems, Fe(P7)Cl (P7) and CMC-Por-FeCl (CMC-Por). The frozen study
contains 41 P7 reaction records and 50 CMC-Por records, with enantioselectivity
as the primary prediction target and isolated yield retained as a separate
secondary endpoint. The two catalyst domains were modeled independently before
any transfer analysis was performed, preserving their distinct catalyst and
reaction-condition identities. Starting-material SMILES, recorded product
SMILES, experimental outcomes, reaction-site annotations, molecular features,
and provenance were retained at the individual-substrate level. This produced
an auditable foundation for comparing representations and learning strategies
without treating the two catalysts as a single undifferentiated dataset.

We first constructed a hierarchy of two-dimensional molecular representations.
The hierarchy begins with compact, chemically interpretable RDKit descriptors
and progresses through expanded descriptor sets to radius-2 Morgan
fingerprints of increasing dimensionality. The full two-dimensional reference
combines 15 RDKit descriptors with a 1,024-bit Morgan fingerprint. In total, we
defined 11 representation arms: a no-feature mean reference (B0), five
two-dimensional levels (B1–B5), and five pose-containing or pose-only levels
(P0–P4). Ten feature-bearing arms were compared in both transfer directions.
Progressing from the six-descriptor B1 model to the full B5 representation
reduced target-only mean absolute error (MAE) from 12.895 to 11.815 ee points
for CMC-Por→P7, an 8.4% improvement, and from 14.243 to 12.234 ee points for
P7→CMC-Por, a 14.1% improvement. Across all analysis branches, five distinct
supervised estimator families were tested—Ridge regression, Elastic Net,
Tanimoto-k-nearest neighbours, LightGBM, and Gaussian-process regression—in
addition to the B0 training-fold-mean reference. This design allows prediction
performance to be traced from a simple descriptor model to more expressive
substructure and pose representations under matched evaluation conditions.

We then incorporated three-dimensional information derived from aligned
substrate pose ensembles. The pose hierarchy includes pose-only diagnostics,
combined structure–pose models, compact geometric summaries, and a
catalyst-interaction feature block. Numerical occupancy and reaction-corridor
descriptors were retained together with per-substrate density arrays and
graphical pose overlays. These comparisons show that pose information can
provide additional predictive signal beyond two-dimensional structure in
specific model and validation settings, including improvements for the
Elastic Net model in the independent P7 holdout analysis. Adding pose features
reduced Elastic Net MAE from 15.436 to 11.649 ee points in the target-holdout
test (a 3.787-point or 24.5% reduction) and from 14.221 to 12.390 ee points in
the family-holdout test (a 1.831-point or 12.9% reduction). The best
structure-plus-pose result, 11.649 ee points, was also lower than the best
structure-only target-holdout result of 12.236 ee points obtained with
LightGBM. However, pose features worsened the corresponding Ridge and LightGBM
results and left Gaussian-process performance effectively unchanged. Pose
information is therefore interpreted as a conditional source of added signal,
not an unconditional replacement for RDKit and Morgan features.

To emulate the practical development of a substrate scope, we evaluated the
models progressively as labelled substrates were revealed. Five substrate
selection logics were investigated—historical order, diversity-first,
performance-first, uncertainty–diversity, and random selection—with Ridge,
Elastic Net, and Tanimoto-k-nearest-neighbour estimators compared across the
progressive analyses. The random control was aggregated over 500 independent
routes. With Ridge held fixed, uncertainty–diversity was the best policy in
both catalyst domains: relative to historical ordering, it reduced mean prefix
MAE from 21.672 to 9.684 ee points for P7 (55.3%) and from 13.155 to 8.787 ee
points for CMC-Por (33.2%). When all estimator–policy combinations were ranked
by area under the progressive MAE curve, Tanimoto-k-nearest neighbours gave
the best P7 result with uncertainty–diversity (AUC-MAE 306.116; final-prefix
MAE 1.215 ee points) and the best CMC-Por result with diversity-first (AUC-MAE
171.515; final-prefix MAE 2.089 ee points). These findings distinguish the
quality of the complete learning trajectory from the error at only the final
prefix and demonstrate that both estimator choice and substrate ordering
affect retrospective learning efficiency. They do not constitute prospective
evidence that the algorithm improves experimental enantioselectivity.

The independently learned domains were next connected through guarded,
bidirectional transfer. P7 was used as a frozen source for progressive learning
of CMC-Por, and CMC-Por was separately used as a frozen source for P7. The
framework evaluates target-only and source-informed predictions concurrently,
updates the trust assigned to transferred information from prequential target
error, and suppresses source contributions when they cause negative transfer.
This analysis establishes a reproducible route for transferring information
between related iron porphyrins while maintaining catalyst-specific boundaries.
For CMC-Por→P7, the catalyst-aware P4 arm was the best tested transfer
representation: target-only MAE was 11.061 ee points and guarded MAE was
10.741, compared with 11.815 and 11.654, respectively, for the B5
structure-only reference. For P7→CMC-Por, compact-pose P3 gave the lowest
matched errors (12.205 target-only and 11.480 guarded), but its progressive
AUC-MAE of 373.801 was slightly worse than B5 at 372.493. Thus, guarded
transfer improved matched MAE directionally in both systems, while the
prespecified 10% superiority criterion based on the full progressive error
curve remains unresolved and is not claimed as achieved.

Finally, the frozen learning workflow was coupled to a generative substrate
search. A provenance-controlled SMILES generation process produced 50,560 raw
candidates, which were subjected to structural-contract validation,
applicability-domain filtering, and comparison with a deterministic enumeration
baseline of equal size. The generator yielded 563 contract-valid candidates,
of which 483 lay inside the frozen applicability domain. The enumeration
comparator yielded 18,545 contract-valid candidates, of which 18,350 were
inside the applicability domain. The resulting computational shortlist
provides a ranked, chemically diverse starting point for future scope expansion
in the two studied systems. These candidates remain prediction-only proposals:
their availability, synthetic feasibility, safety, yield, and
enantioselectivity have not been established experimentally.

Together, checkpoints 1–9 deliver an end-to-end and auditable workflow spanning
independent catalyst models, progressively richer molecular representations,
pose-aware prediction, learning-curve analysis, guarded transfer, and
generative substrate prioritization. All underlying non-XYZ records, feature
matrices, predictions, learning-curve rows, pose-density arrays, transfer
replicates, and generation outputs are retained in the accompanying supporting
information. The principal contribution is therefore not a claim of universal
model superiority, but a reproducible strategy for learning and extending
substrate scope while testing explicitly when two-dimensional structure,
three-dimensional pose, and prior catalyst knowledge are useful.

## Checkpoint 10 placeholder: transfer to an unseen iron-porphyrin system

**[PLACEHOLDER—TO BE COMPLETED WHEN THIRD-SYSTEM DATA ARE AVAILABLE]**

The final checkpoint will evaluate whether the frozen workflow transfers to a
third, previously unseen iron-porphyrin catalyst, provisionally designated
D4-Por. This section will be completed only after the catalyst identity and
conditions, curated substrate/outcome records, reference geometry, constraint
profile, pose features, and prospective evaluation protocol are available.
The future analysis should apply the representation definitions, acquisition
rules, transfer guard, and success criteria frozen in checkpoints 1–9 without
post hoc modification. Required results will include target-only and
source-informed learning curves, uncertainty intervals, negative-transfer
diagnostics, performance against the prespecified transfer gate, and clearly
identified prospective experimental outcomes. No result for checkpoint 10 is
currently inferred from the reciprocal P7/CMC-Por study.
