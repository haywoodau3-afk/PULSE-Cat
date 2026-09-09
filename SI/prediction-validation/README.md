# Prediction and validation records

The links here separate model evaluation from raw curated inputs. Use the
row-level prediction CSVs together with their JSON split files to recompute
metrics without reconstructing membership from narrative text.

Key files:

- `p7-model-reports/full-scope-structure-model-predictions.csv` — one held-out
  prediction row per model/substrate/split, including observed target,
  prediction, residual, interval columns, validation score, and estimator
  parameters.
- `p7-model-reports/full-scope-structure-splits.json` — exact train,
  validation, and target IDs for the 38-substrate target-holdout analysis.
- `p7-model-reports/family-heldout-structure-ee-model-predictions.csv` and
  `family-heldout-ee-splits.json` — family-held-out EE validation.
- `p7-stage2/features/` — feature matrices, feature manifests, and pose-derived
  feature blocks used by the P7 rerun.
- `transfer-and-route-artifacts/matrix-ee-b5-p3-p4.json` — reciprocal B5/P3/P4
  transfer rows and summaries.
- `transfer-and-route-artifacts/routes/` and `.../scaffold/` — random-route,
  paired, and scaffold bootstrap inputs/results.

The original full filenames are preserved below these links. See
[`../algorithms/ALGORITHM_SPECIFICATIONS.md`](../algorithms/ALGORITHM_SPECIFICATIONS.md)
for metric and bootstrap definitions.

