# ChemCatChem evidence matrix

| Manuscript claim | Required evidence | Current artifact | Status |
|---|---|---|---|
| P7 model is useful within domain | Scaffold/family-held-out MAE, RMSE, rank and interval coverage | Existing P7 reports and locked V6 predictions | Development evidence; independent reproduction required |
| CMC-Por is an independent challenge | Ar­yl-only contract, no sulfonyl leakage, sealed audit | `cmcpor_aryl_scope_progression/`, reciprocal matrices | Development-pass |
| Progressive learning improves retrospective ee learning | Matched historical-order, AI-guided, and random trajectories under equal budgets | `data/expansion/pptl/historical-vs-ai-progressive-comparison.json` and scope-progression artifacts | Computational-pass; no prospective outcome claim |
| Transfer is safe/useful | B5/P3/P4 bidirectional guarded vs target-only results | `aryl-bidirectional-ee-matrix.json`, `aryl-bidirectional-yield-matrix.json` | Development-pass; superiority gate unresolved |
| Geometry contributes information | Multi-start stability, calibration, incremental-value test | Pose-interaction features and P4 replay | Secondary/conditional; stability panel pending |
| Copilot generates chemically valid scope | Fixed-seed generation, deterministic funnel, enumeration comparator | Generator freeze config, production funnel, and grammar fixtures | Computational-pass; proposals only |
| Recommendations are chemically in-contract | Exact starting-material identity, aryl-azide morphology and deterministic closure validity | Grammar fixtures and funnel validator | Computationally implemented |
| Closed loop works | Recommend → make/buy → test → reveal → refit with untouched audit | Locked protocol retained as an optional future validation | Not claimed in computational paper |
| Uncertainty is decision-useful | 80/95% coverage, calibration, applicability-domain warnings | Planned reporting contract | Not yet run on generator candidates |

## Submission-stop conditions

For this computational manuscript, do not claim experimental prospective
validation or a closed loop. State explicitly that the generator proposes
starting materials and that the demonstrated benefit is retrospective learning
efficiency. If the manuscript is submitted as a chemistry paper, the editor may
still request experimental validation; that would be a new scope decision, not a
result that can be filled in computationally.

The checkpoint 1–9 manuscript freeze, including the reconciled generator budget,
is recorded in `docs/checkpoint-1-9-manuscript-freeze.md`.
