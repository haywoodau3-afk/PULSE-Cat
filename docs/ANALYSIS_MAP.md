# Analysis map

The paths below identify saved outputs, not independently verified reruns. Under `records/corrected_project/analysis_runs/`:

| Analysis | Folder | Main use |
| --- | --- | --- |
| Dedicated acquisition replay | `corrected_dedicated_replay/` | Route-specific mean-prefix comparisons. |
| Shared starts | `corrected_shared_starts/` | Sensitivity to 50 initial substrate pairs. |
| Common held-out tests | `corrected_common_test/` | Comparisons using common test substrates and overlapping splits. |
| Acquisition weights | `corrected_weight_sensitivity/` | Retrospective 21-setting weight grid. |
| Representation and ordering | `corrected_factorial/` | Four-cell representation-by-order comparisons. |
| Substrate classes | `corrected_class/` | Mixed-pool and sulfonyl-only sensitivity analyses. |
| Yield | `corrected_yield/` | Matched yield endpoint comparisons. |
| Established acquisition methods | `corrected_baselines/` | Query by committee and optimisation comparisons. |
| Independent progression | `independent_progression/` | Trajectory and AUC-MAE summaries. |

The principal 38-substrate representation benchmark is represented by split, prediction and report records under `records/full_scope/` and `records/corrected_project/model_comparisons/p7/`; related recomputation scripts are under `revision/reviewer2_comment2/`. Figure and manuscript descriptions must be checked against the exact release outputs before citation.
