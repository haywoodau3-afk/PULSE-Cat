# Iron substrate-scope expansion: completion status

Status: locally reproducible work completed on 2026-08-26. Two gates remain
external: a consistent higher-level reference calculation for BDE calibration,
and experimental measurements for the prospective substrates.

## Completed

| Work item | Status | Result |
|---|---|---|
| Frozen hard-rule diversity versions V0–V6 | Complete | Existing versions were preserved. The blocks cover coarse BDE priors, electronegativity shells, flexibility, steric/topological structure, polarity, site ambiguity, reaction contrast, path accessibility, and local reactivity regime. |
| P7 and cmcpor retrospective progression | Complete | The existing standard, corrected feature-mixture, and worst-first diagnostic runs remain unchanged and separate. |
| Interim BDE calibration | Complete as an interim check | 119 candidate-site pairs across 38 P7 substrates were joined to the completed GFN2-xTB/ALPB(ether) calculations. |
| Prospective computational panel | Complete for P7 | The five predeclared unlabelled late-stage candidates (1ap, 1aq, 1as, 1at, 1au) were scored with V0, V4, and V6. |

## Interim BDE result

The frozen rules preserve useful relative information but are not calibrated
absolute energies. Against the existing xTB panel, raw rule estimates gave
MAE 24.93 kcal/mol, RMSE 25.31 kcal/mol, bias −24.88 kcal/mol, and Pearson
r 0.803. Within-substrate ordering agreed exactly for 45.4% of site pairs
and was within one rank for 84.0%. A leave-one-substrate-out affine
correction reduced MAE to 2.71 kcal/mol and RMSE to 4.78 kcal/mol in this
interim xTB comparison.

This is evidence for calibrating the rule prior as a relative/ranked feature;
it is not a claim that the rule estimates are DFT-quality BDEs. The selected
12-site panel is ready for one consistent higher-level calculation.

## Prospective computational panel

The new structure-plus-rule model was kept separate from the existing
pose-aware Stage 2p/Stage 3a predictions. Historical P7 training used the same
38-substrate scope as the rule-mixture analysis.

| Version | Ridge LOO MAE | Elastic-net LOO MAE | Tanimoto-kNN LOO MAE |
|---|---:|---:|---:|
| V0 | 8.45 | 8.44 | 8.11 |
| V4 | 7.75 | 7.71 | 8.11 |
| V6 | 7.75 | 7.63 | 8.11 |

These are retrospective diagnostics, not measured accuracy for the five new
substrates. The candidate predictions and acquisition diagnostics are stored
with the panel output; all five still have `prediction_only` status.

## Remaining gates

1. A higher-level reference executable and results are not present in the
   workspace. The current xTB calculation is therefore recorded as an interim
   reference only. Final BDE calibration requires the selected panel to be run
   with one consistent higher-level method and re-evaluated by site ranking.
2. The five P7 late-stage substrates have no experimental ee labels in the
   workspace. Prospective validation requires fixed-condition laboratory runs
   and then a comparison of measured ee/yield with the stored predictions.
3. No unlabelled cmcpor prospective panel was present, so no new cmcpor
   candidate prediction was fabricated. The cmcpor retrospective progression
   remains complete.

## New artifacts

- `scripts/calibrate_rule_bde.py`
- `data/jacs_2025/stage3/calibration/bde-calibration-summary.json`
- `data/jacs_2025/stage3/calibration/bde-calibration-pairs.csv`
- `data/jacs_2025/stage3/calibration/bde-calibration-panel.csv`
- `scripts/rule_prospective_panel.py`
- `data/jacs_2025/stage3/prospective-rule-panel/report.json`
- `data/jacs_2025/stage3/prospective-rule-panel/predictions.csv`
- `tests/test_calibrate_rule_bde.py`
