# Computational data completeness audit

Audit date: 2026-09-03

## Present and locked

| Data block | Current state |
|---|---|
| P7 source records | 41 records retained; the P7 arm excludes `1z` (Fe(P2)Cl) and `1ad` (unresolved ee), leaving 39 progression records and 38 usable ee labels because `1an` is achiral/not applicable |
| CMC-Por records | 50 records: 33 aryl records in the primary domain and 17 sulfonyl records retained as a separate control |
| Structural curation | Mapped structures, reaction-centre decisions, corrected CMC records, grammar fixtures, and canonical-overlap ledger |
| Independent/transfer models | Structure, transfer, pose, reciprocal matrices, scaffold/family diagnostics, and fixed-prefix learning artifacts |
| Progressive replay | Historical-order, diversity, uncertainty–diversity, performance-first, and 500-replicate random routes; historical-versus-AI comparison is locked |
| Generator provenance | SMILES-RNN commit/checkpoint, PromptSMILES version, five seeds, 50,560 persisted raw SMILES (10,112 per seed), funnel rejection reasons, hashes, and a matched 50,560-row enumeration comparator |
| Proposal set | Sealed 8+8 computational panel with Round A/B assignments and `outcome_revealed=false` |
| Applicability and morphology | Contract-valid counts, Morgan-distance applicability labels, morphology families, and predicted-ee proposal rankings |

The publication-ledger hashes currently verify against the stored P7/CMC records,
Stage 2p features, and PPTL contract.

## Data that are intentionally absent

- No experimental ee/yield outcomes for the generated panel or the five P7
  prediction-only substrates. This is intentional under the computational-only
  scope; no values should be fabricated or imputed.
- No supplier/availability, retrosynthetic-route, or laboratory-safety evidence
  is used. Those are outside the present claim.

## Evidence still conditional rather than missing labels

- Pose stability and geometry calibration are available as exploratory pose
  artifacts, but pose should remain a secondary/conditional claim unless the
  independent multi-start stability and calibration checks are promoted into the
  final methods table.
- Historical uncertainty and applicability diagnostics exist. A formal
  candidate-level interval-coverage/calibration table for the unlabelled
  generator pool is not an experimental result and should be reported only as a
  model diagnostic, if included.
- A clean independent rerun in a second environment and final figure/table
  reconciliation are publication-quality reproducibility steps, not new chemical
  data.

## Conclusion

All data required for the current computational claim are present. The project
does not have—and does not claim to have—the data required for prospective
experimental validation or a closed-loop chemistry claim.

The checkpoint-by-checkpoint manuscript freeze and the remaining D4 exclusion
are recorded in `docs/checkpoint-1-9-manuscript-freeze.md`.
