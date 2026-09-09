# ChemCatChem development gate status

Last updated: 2026-09-02

| Gate | Status | Evidence | Remaining action |
|---|---|---|---|
| Gate 0 — computational reconciliation | Development-pass | Corrected CMC aryl progression, audit schemas, reciprocal B5/P3/P4 ee/yield matrices, integrity checks | Independent second-person reproduction and manuscript-number ledger |
| Gate 1 — chemical contract | **Passed by project decision (single-reviewer exception)** | User confirmation of CMC-Por repairs, P7 sites/products, grammar and exclusions | Complete source checksum and final mapped-product verification before external submission; independent review is waived by project decision |
| Gate 2 — constrained generator | **Cross-fitted ee-aware acquisition checkpoint complete** | 5-fold out-of-fold acquisition gives MAE 5.57 at n=4 and 5.28 at n=16 versus random 23.36 and 18.11; observed-ee enrichment is also higher. | Treat as retrospective support only; validate on untouched prospective substrates |
| Gate 3 — synthesis/availability/safety | **Out of scope for computational study** | Starting-material morphology contract and structural validator retained; availability/safety ledgers archived as optional future work | Do not use availability or safety as model-selection criteria; institutional EHS remains mandatory if experiments occur |
| Gate 4 — prospective proposal panel | **Computational-pass; prediction-only** | 8 copilot + 8 comparator candidates, 4+4 rounds per branch, pre-outcome predictions and SHA-256 lock | No experiment is part of the current study; retain the lock for optional future validation |
| Gates 5–6 — closed loop and publication | **Not claimed** | Reveal/refit gate is implemented and tested only as a fail-closed software path | Do not present a closed-loop or experimental claim without a separate validation study |

## Current decision

The project is computationally ready for enantioselectivity-focused generative
evaluation. The strongest supported claim is retrospective: model-guided
progressive ordering improves ee-learning efficiency relative to the historical
source order, while the generator supplies contract-valid starting-material
proposals. No experimental outcome, availability assertion, or closed-loop
success is claimed.

The claim-to-evidence mapping is maintained in `docs/chemcatchem-evidence-matrix.md`.
