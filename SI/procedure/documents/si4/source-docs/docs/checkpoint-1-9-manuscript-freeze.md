# Checkpoint 1–9 manuscript freeze

Freeze date: 2026-09-03  
Scope: retrospective computational comparison of the P7 and CMC-Por
iron-porphyrin domains. D4-Por remains a deferred third-system extension.

## Frozen checkpoints

| Checkpoint | Frozen evidence | Manuscript boundary |
|---:|---|---|
| 1 | Independent P7 and CMC-Por catalyst records, reference geometries, constraints, pose ensembles, features and model outputs | Two fixed domains; no universal catalyst model |
| 2 | B5: 15 RDKit descriptors plus a 1,024-bit radius-2 Morgan fingerprint | Structure-only reference representation |
| 3 | Persisted Stage 2p pose features and Stage 2pp density artifacts for both domains | Pose rows are aggregated at substrate level; they are not independent labels |
| 4 | Matched structure/pose ablations, controls and reciprocal transfer matrices | Pose gains are directional/conditional; do not claim universal superiority over B5 |
| 5 | Per-substrate XYZ-derived density `.npz` and SVG artifacts | Occupancy fields are geometric summaries, not electron density |
| 6 | Historical, diversity, performance-first, uncertainty–diversity and random progressive routes | Retrospective learning-efficiency result only |
| 7 | Learning curves, AUC-MAE, `n90`, selection events and convergence manifests | Convergence is a model diagnostic, not chemical validation |
| 8 | Bidirectional guarded transfer with prequential weights and negative-transfer suppression | Guarding improves error in both directions, but the prespecified 10% AUC superiority gate is unresolved |
| 9 | Frozen SMILES-RNN + PromptSMILES provenance, 50,560 raw candidates, equal-budget 50,560 enumeration comparator, funnel and sealed proposal panel | Generated structures are prediction-only; no experimental, availability or safety claim |

## Generator budget reconciliation

The original request was 10,000 samples per seed (50,000 total). The persisted
production artifact contains the complete batch output of 10,112 samples per
seed (50,560 total). The 112-row per-seed overrun is recorded in
`generator-freeze-config.json` and retained without post hoc filtering. The
deterministic comparator was regenerated at the same 50,560-row budget.

## Frozen artifacts

- Publication ledger: `data/expansion/pptl/publication-ledger-lock.json`
- Generator configuration: `data/expansion/pptl/generator-freeze-config.json`
- Generator summary: `data/expansion/pptl/production-generation-summary.json`
- Equal-budget comparator: `data/expansion/pptl/enumeration-comparator-summary.json`
- Generator/comparator comparison: `data/expansion/pptl/generator-enumeration-comparison.json`
- Consolidated report: `data/expansion/pptl/pptl-final-report.md`

The P7/CMC-Por publication lock digest is
`c2613a95c111f1eba4ed0830c808e211e78c3e867edd65005dd86368dccdef03`.

## Excluded claim

No D4-Por substrate/outcome labels, reference geometry or constraint profile
are present. Transfer to a third unseen iron-porphyrin system is therefore a
future extension and is not part of this freeze.
