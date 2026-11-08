# Stage 2p Publication Readiness

Status: **not_ready**

This report evaluates the fixed-catalyst `[Fe(P7)Cl]` Stage 2p substrate model. It does not claim cross-catalyst transfer or signed stereochemical prediction.

## Locked scientific scope

- Primary target: unsigned ee magnitude until product configurations are manually curated.
- Catalyst: fixed `fe-p7-cl`; out-of-domain catalysts are excluded before feature generation.
- Validation: nested leave-one-family-out evaluation with train-only feature masking and applicability calibration.
- Incumbent: Elastic Net; Ridge, median, and chemical nearest-neighbour models are required challengers.
- Conditions: published temperature and condition-set identity are encoded explicitly.

## Incumbent performance

- MAE: 9.627 ee
- RMSE: 12.991 ee
- Within ±10 ee: 25/38
- Within ±15 ee: 28/38
- Within ±20 ee: 32/38
- Precision at ≥80 ee: 0.875
- 80% interval coverage: 0.816
- 95% interval coverage: 0.974

## Readiness gates

- [x] fixed_catalyst_domain_clean
- [x] out_of_domain_records_excluded
- [x] nested_family_holdout
- [ ] signed_ee_curated
- [ ] genuine_feasibility_negatives
- [x] yield_model_available
- [ ] prospective_panel_locked
- [ ] catalyst_bridge_matrix

## Blocking items

- absolute product configurations are not curated; target remains ee magnitude
- the literature cohort lacks genuine tested-substrate feasibility negatives
- no locked prospective panel is present
- no connected cross-catalyst bridge matrix is present

## Decision rule for future candidates

Advance only when the lower 80% interval clears both 80 ee and 50% yield and the applicability decision is `in_domain`. Cases whose interval crosses a threshold are uncertain; out-of-domain cases must abstain.
