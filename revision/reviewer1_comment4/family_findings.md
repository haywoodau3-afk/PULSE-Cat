# Reviewer 1 comment 4: family-held-out findings

The original archived Elastic Net prediction records were paired by substrate and checked against the family split file. Recalculated substrate-weighted MAEs reproduce the manuscript: target-held-out 12.6123 versus 8.5826, and family-held-out 10.4060 versus 9.3342 ee points (structure-only versus structure plus pose). The family-held-out absolute improvement is 1.0718 ee points (10.3% of the structure-only MAE). Different splits and fitted models mean the difference between the 31.9% and 10.3% percentages alone does not establish a statistically significant change or quantify a universal extrapolation penalty.

The 38 substrates comprise 17 predefined families: nine singletons, four pairs, three groups of three, and one group of 12. Pose features lower the family MAE in 11/17 families and lower absolute error for 25/38 substrates. Equal weighting of the 17 family MAEs gives 11.99 versus 9.84 ee points. This is a post hoc descriptive summary and gives each singleton family the same weight as the 12-member family; it does not prove general performance for new chemical families.

The 12-member diaryl-ethyl-aryl-substituted family contributes 31.6% of substrates to the pooled MAE. Its structure-only and pose MAEs are 5.25 and 6.44, respectively, so pose increases error in this family by 1.20 points. Excluding it gives pooled MAEs of 12.79 versus 10.67 over the remaining 26 substrates; this is a descriptive sensitivity check, not an independent test or a reason to discard the family. The result depends on the family definitions and observed scope. The family-level errors span a wide range; all 17 rows are retained in `results/family_results.csv` and the revised Supporting Information.

The principal limitation remains: these retrospective splits test unseen substrate families within one studied catalyst system, not unseen catalyst families, reaction classes or prospective performance. Many families have one or a few members, the underlying data and training sets overlap, and the existing analysis provides no family-level population confidence interval. The earlier result of comment 3 using all 248 pose fields and Ridge is a different experiment and should not be substituted for this selected-feature Elastic Net benchmark.

## Reproducibility and checks

- `analysis_plan.md` was recorded before calculation; `family_diagnostics.py` stores paired errors, all families, source and script hashes in `results/`.
- Recomputed absolute errors and all four archived MAEs; matched all 38 IDs, observed outcomes, train/validation partitions, family labels and family split definitions. Held-out family records were excluded from training and validation.
- `verify_family_diagnostics.py` independently reassembled the 17 family MAEs and checked matched structure/pose partitions and target exclusion. Its result is in `validation_report.txt`.
- These are secondary analyses of existing predictions; no new model training or laboratory experiments were conducted and no formal significance test is claimed.
