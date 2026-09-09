---
status: accepted
---

# Primary study uses bidirectional guarded progressive transfer

The primary study evaluates two reciprocal, label-masked replays: P7 aryl→CMC-Por aryl and CMC-Por aryl→P7 aryl. In each direction the source is frozen, the target is revealed one whole substrate at a time, and target-only, source-specific, pooled, and guarded experts remain separately identifiable. Source contributions are updated from prequential target error and may be suppressed when they cause negative transfer; unconditional pooling is retained only as a comparator. D4-Por is a deferred extension after this reciprocal contract is reproducible. The workflow uses a low-resource RDKit tier, while pose representations must pass matched incremental-value gates before adoption. This preserves catalyst-domain boundaries and transfer auditability at the cost of more model arms, and limits claims to computational replay rather than wet-lab or GNN validation.

## Considered options

- One pooled cross-catalyst model was rejected as the sole method because it hides which source helps and cannot expose source-specific negative transfer.
- A D4-first study was deferred because D4 records, geometry, and constraint inputs are not yet complete; making them a prerequisite would block a testable reciprocal study.
- A one-way P7→CMC-Por study was rejected as the primary design because it cannot reveal transfer asymmetry or whether CMC-Por is a useful source for P7.
- Pose-first learning was rejected as the default because existing pose results are mixed and pose generation conflicts with the low-resource niche.

## Consequences

- Every target prefix in both directions is evaluated against target-only, source-specific, combined-source, and guarded-ensemble arms.
- EE and yield maintain separate models, losses, and expert weights.
- The low-resource workflow must run without poses; Stage 2p and catalyst-aware blocks are optional tiers.
- Canonical shared compounds are excluded from cold-start source training and retained in a separate paired diagnostic.
- The paper may claim reciprocal transfer efficiency only if the predeclared bidirectional gates pass; otherwise it reports direction-specific safety or explanation results.
