# Guarded-transfer procedure

## Directions and splits

Run P7 → CMC-Por aryl and CMC-Por → P7 aryl. Canonicalize after removing atom
maps, reconcile the 13 shared compounds, and exclude their source counterparts
from cold-start source training. Keep source and target catalyst domains,
pathways, family/scaffold groups, and target labels explicit.

## Experts

At each target prefix, fit and retain:

- E0 target-only;
- source-only zero-shot and target-adapted experts;
- pooled source/target domain-indicator expert;
- source-coefficient-regularized expert;
- source-prediction residual-correction expert; and
- E4 guarded ensemble.

Ridge with `alpha=10` and predictions clipped to `[0, 100]` is primary. Elastic
Net and Tanimoto-kNN are challengers in the independent progression suite.

## Trust update

Before the target label is revealed, calculate all eligible predictions. Start
with target weight 0.5 and distribute source weight 0.5 using frozen,
label-independent coverage and reciprocal reliability. Update separate EE and
yield losses after reveal. During the first five scored post-seed reveals,
source total weight cannot exceed 0.5. Set a source's active weight to zero if
its cumulative MAE is both greater than one percentage point and more than 10%
worse than E0. Preserve its shadow prediction and loss history.

## Audits

Report the complete prefix rows, pre/post weights, expert errors, ensemble
error, disagreement, suppression events, and scaffold/family negative-transfer
diagnostics. Compare the guarded ensemble against target-only, unconditional
pooling, source-volume, outcome-permutation, and equal-dimensional feature
controls. Yield results are not allowed to rescue a failed ee claim.
