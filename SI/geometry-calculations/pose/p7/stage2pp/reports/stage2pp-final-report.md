# Stage 2″ Final Report

Stage 2″ was implemented using the existing 200 retained Stage 1 poses per substrate. It writes persistent numerical cylindrical occupancy arrays, derived SVG diagnostics, cluster/weight provenance, variance and top-minus-bottom fields, and reaction-corridor flexibility features.

The official family-held-out run used the canonical 38-record ee cohort and 17 outer family splits. It did not improve the existing Stage 2p representation:

| Feature set | Model | MAE | RMSE | Within 20 ee points |
| --- | --- | ---: | ---: | ---: |
| Stage 2p | Elastic Net | 10.281 | 13.023 | 31/38 |
| Stage 2p + Stage 2″ | Elastic Net | 14.132 | 17.005 | 27/38 |
| Stage 2-alt | Elastic Net | 10.864 | 14.934 | 29/38 |
| Stage 2-alt + Stage 2″ | Elastic Net | 11.572 | 14.845 | 29/38 |
| Stage 2″ alone | Elastic Net | 13.055 | 16.484 | 29/38 |

The paired Stage 2p → augmented MAE change was `+3.852` ee points. The Stage 2-alt → augmented change was `+0.708` ee points. Neither augmentation passes the prespecified ≥1-point improvement gate.

This is a negative representation result, not evidence that the occupancy fields are chemically meaningless. The fields are retained for inspection and future ablation; Stage 2p/Stage 2-alt remain the stronger model branches for this cohort.

Artifacts:

- Features: `data/jacs_2025/stage2pp/features/stage2pp-features.jsonl`
- Manifest: `data/jacs_2025/stage2pp/features/stage2pp-manifest.json`
- Numerical fields: `data/jacs_2025/stage2pp/density/`
- SVG diagnostics: `data/jacs_2025/stage2pp/svg/`
- Metrics: `data/jacs_2025/stage2pp/modeling/stage2pp-model-comparison.json`
- Predictions: `data/jacs_2025/stage2pp/modeling/stage2pp-predictions.csv`
