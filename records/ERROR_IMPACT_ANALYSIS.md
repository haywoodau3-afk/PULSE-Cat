# Impact analysis of the nitrene atom-index error

**Assessment: substantial and cross-cutting.** The error changes pose-derived inputs and downstream numerical results, and at least one previously reported comparison changes direction. It does not alter the source experiments or measured outcomes. The analyses retained in the corrected manuscript and SI have been rerun or explicitly checked; earlier calculations are retained only as historical provenance. This archive is a corrected working package, not a journal submission release: the original historical run tree is incomplete for bitwise reconstruction, and author review and final repository-deposit steps remain.

## What went wrong

Some feature-generation code assumed atom index 0 in a molecular representation was the nitrene nitrogen. That assumption fails for certain valid orderings of the same type of molecular input, where atom 0 is carbon. The assembly code had reordered the nitrene, so using the original atom index to find it in the assembly could point at the wrong atom. This affects the geometry around the nitrene, selection of a nearby hydrogen, derived directional features and models consuming those features. The code has been changed to identify the actual nitrene atom.

A direct audit of all 200 archived coordinates for 1ah gives mean nitrene-nitrogen–reactive-carbon distance **3.5815 Å**, versus **2.5386 Å** in the original feature file. The same independent coordinate check agrees with the original 1a value. This establishes a concrete error rather than merely a potential code concern. The original chemical structures, measured ee and yield, and archived pose coordinates have not been changed by this correction; derived features and predictions can change.

## How much of the input changes?

The comparison joins archived and regenerated Stage 2p feature records by substrate ID and counts numerical field changes using absolute and relative tolerance 1 × 10⁻⁹. Each record has 248 fields. A count is not an estimate of chemical or statistical importance: many fields are related summaries of the same underlying geometry.

| Dataset and coverage | Records with changed fields | Extent |
|---|---:|---|
| Fe(P7)Cl active modelling cohort | 12 of 38 | 182 distinct fields change in at least one record; affected records each have 161–182 changed fields. |
| Fe(CMC-Por)Cl complete regenerated feature set | 30 of 50 | 182 distinct fields change in at least one record; this includes 14 active aryl, 6 of 7 locked audit, and 10 sulfonyl records. |

The 38 previously comparable Fe(P7)Cl ee records are the modelling cohort used for changed-field counts. Corrected feature coverage now contains 40 P7 records: the same 38 ee records plus 1ad and 1an, which are yield-only and were generated separately because no comparable archived Stage 2p feature rows were available for them. The unrelated 1z label is not in the corrected P7 source set. For all 38 and all 50 CMC compared records, recorded target values agree. See [record-by-record counts](stage2p_record_changes.csv) and [feature summary](feature_change_summary.json). These counts apply to Stage 2p, not every feature family or report. Separately, all 8,200 archived Fe(P7)Cl pose-interaction records match corrected records by substrate and pose ID; 28 distinct fields change in at least one pose across 12 substrates. The nitrene-N-to-reactive-C distance changes in 2,400 poses (200 for each of those 12 substrates), and selected hydrogen index changes in 852 poses. See [pose-level field counts](pose_interaction_change_summary.json).

## Changes to representation validation

The following Fe(P7)Cl Elastic Net comparisons use the same archived held-out memberships; the corrected pose-interaction features were regenerated and model selection rerun. Errors are mean absolute errors (MAE) in ee percentage points, so smaller is better.

| Validation | Structure only | Original structure + pose | Corrected structure + pose | Reduction versus structure only: original → corrected |
|---|---:|---:|---:|---:|
| Target held out | 12.612 | 8.583 | 7.979 | 31.9% → 36.7% |
| Family held out | 10.406 | 9.334 | 8.538 | 10.3% → 17.9% |

The direction of these pooled comparisons remains favourable to pose features, but the actual values and claims change. The corrected family-level summary favours pose for 11 of 17 families and 23 of 38 substrates, compared with 11 families and 25 substrates originally; family sizes are unequal. These retrospective splits are not independent new-dataset validation, and the protocols differ, so their difference is not evidence of a statistically significant change in generalisation.

A separate preprocessing issue also requires correction: the original 38-substrate representation benchmark used a global **label-blind** constant-feature filter before splitting, not exclusively training-only filtering as previously stated. For the already selected corrected Elastic Net hyperparameters, training-only filtering reproduces all 76 held-out predictions to numerical precision; this does not validate hyperparameter reselection or other estimators.

## Changes to acquisition and reviewer analyses

The common-test comparison uses the same held-out substrates, starting pairs, budgets and observed outcomes before and after correction. It averages prediction MAEs over five budgets, three starts and 20 overlapping splits. Positive source-minus-uncertainty–diversity (UD) means UD has lower error. Values in ee points:

| Catalyst | Historical minus UD, original → corrected | Splits favouring UD, original → corrected | Random minus UD, original → corrected |
|---|---:|---:|---:|
| Fe(P7)Cl | 2.85 → 6.99 | 17/20 → 19/20 | 0.37 → 1.45 |
| Fe(CMC-Por)Cl | 1.43 → 2.50 | 11/20 → 11/20 | 1.06 → 1.22 |

These differences cannot be substituted for the paper's **55.3% and 33.2%** figures: the paper uses a different remaining-pool, mean-prefix metric. The corrected dedicated replay changes reported-order/UD MAEs from 21.67/9.68 to 25.51/7.48 for P7 and from 13.15/8.79 to 16.98/9.64 for CMC; corresponding descriptive reductions are 70.7% and 43.2%. These route-specific replay values are conditional because the remaining pool changes with each route; they are not fixed-test estimates or population-level significance tests. The dedicated mean-prefix table uses three random continuations and is not comparable to the separate independent AUC-MAE analysis, which was rerun using 500 random continuations per endpoint. In that corrected AUC-MAE progression, UD is below reported order for all three estimators on both endpoints in both cohorts; diversity-first is lower than UD for CMC ee with Tanimoto-kNN. Tables S9–S12 and Figures S5–S6 report the corrected independent progression.

The seven-record CMC fixed-audit comparison is particularly sensitive: its historical-minus-UD mean changes from **−0.40 to +3.88 ee points**, and the fraction of 50 starting pairs favouring UD from **54% to 86%**. Six of those seven held-out records have changed features. This conditional audit is based on one fixed, small set and does not establish generalisation to a new catalyst or population.

| Reviewer point | Impact observed in the provisional reruns | Implication |
|---|---|---|
| R1.1 uncertainty and starting pairs | The common-test and fixed-audit summaries change substantially as above. | Recalculate intervals and paired results and revise the response and figures; do not retain earlier significance claims. |
| R1.2 acquisition weights | Default grid MAE changes 13.88 → 13.72 for P7 and 14.27 → 13.83 for CMC. On the 21-point grid the lowest observed P7 weight combination changes; this is exploratory and does not establish an optimum. | Replace sensitivity tables, plots and any ranking-dependent statements. |
| R1.3 representation × ordering | For P7 the estimated interaction changes −3.58 → −7.73 ee points; CMC changes −2.58 → −3.65. Structure-only values remain identical in these checks. The combined method remains worse on average than structure-only/historical in these comparisons. | Recompute the interaction table and maintain its conditional interpretation. |
| R1.4 family generalisation | Family-held-out pooled and per-substrate pose errors change as above; size imbalance remains. | Update the family table, text and uncertainty caveats. |
| R1.5 substrate classes | The corrected mixed and sulfonyl analyses change; for sulfonyl-only, historical and UD MAE change 17.51/18.61 → 17.98/19.22. | Revalidate class memberships, strata and predictions; update tables and avoid extrapolating from aryl-only results. |
| R1.6 isolated yield | For CMC yield, historical-minus-UD changes **−0.61 → +1.98** and random-minus-UD **−0.23 → +1.04** yield points. This reverses the average direction in this fixed-test analysis, though splits remain mixed. P7 historical-minus-UD changes +2.84 → +6.98. | Reconsider the interpretation rather than preserving the previous explanation of worse CMC yield performance. These results do not identify a chemical mechanism. |
| R1.7 active-learning baselines | QBC mean MAE changes 13.22 → 13.08 for P7 and 13.99 → 13.40 for CMC; corrected UD is 13.72 and 13.83, respectively. Expected-improvement and Thompson results also change. | Rebuild the comparison and objective-specific caveats. QBC remains lower on average in these replays; this is not a universal ranking. |
| R2.1 low/zero ee inclusion | Cohort membership and measured values do not depend on this correction, but predictions and low-ee residual summaries do. | Retain only source-verified inclusion counts after checking; recompute prediction-dependent statements. |
| R2.2 chemical examples | The 1ah geometric descriptor and held-out pose predictions change; the figures and explanatory text were drafted using corrected values. | Independently validate the correction and the illustrated examples before finalising. |

See [all 78 measured comparisons](comparison_of_pre_and_post_correction.csv) for route-level values, including class and endpoint results. For each comparison, a positive or negative difference must be read using its column label; lower MAE is better.

## Checks performed and limits

The independent coordinate audit covers two examples, not every substrate. The [validation checks](validation_checks.json) confirm identical common-test splits, initial pairs and observed outcomes; identical 50-start lists and class-analysis split records; unchanged structure-only factorial controls; and independently reconstructed summary arithmetic for corrected common-test and held-out-prediction MAEs. They do **not** independently validate the corrected feature generator, model-selection implementation, or scientific interpretation. The corrected benchmark retained the original label-blind global feature screening for comparability.

The corrected Stage 2p, pose-interaction, Stage 2pp, model-comparison, independent progression, cross-catalyst scan, Stage 1-v2/Stage 2-v2/Stage 3a seed-pilot, and CREST/GFN2-xTB outputs are recorded under `corrected_project/`. The corrected Stage 1-v2 selection differs from the archived one in 148 of 600 pose identities across four of 12 seed sets. Its 11-record ee seed-pilot comparison gives MAEs of 6.775 (Stage 2 baseline), 15.201 (selected-pose Stage 2-v2), 6.886 (graph-only Stage 3a-alt), and 13.201 (reference/shell). The old Stage 3a shell comparison is superseded. Corrected CREST/GFN2-xTB point estimates favour augmentation, but paired substrate-bootstrap intervals include zero. The source audit now identifies the corrected scripts and input snapshot included in this archive, along with frozen `SI/`–`SI4/` source copies that still contain pre-correction positional assumptions. Those frozen copies are historical and are not the basis of the corrected manuscript or SI; the audit boundary is documented in `SOURCE_TREE_AUDIT.md`. The corrected coordinate-input archive and per-file hashes are included for source-to-feature reconstruction. The historical run tree remains incomplete for exact bitwise reconstruction of every earlier derived result, so the new package—not the old archived outputs—is the reproducibility basis for the correction.

## Current status and remaining limits

The corrected manuscript and SI now report the regenerated pose-dependent results, distinguish the different validation and acquisition metrics, and identify historical values as superseded. The correction archive retains the regenerated records, analysis scripts, tables, figures, and a file manifest. The point-by-point response is still a working draft and should be checked by the authors against the final journal files before submission.

Source review found that the Stage 1 conformer generator identifies the nitrene by connectivity, while the atom-index error affected downstream pose-feature paths. The dependent Stage 1-v2/Stage 2-v2/Stage 3a analyses were rerun or withdrawn where unstable. The corrected release includes the saved coordinate inputs and corrected source snapshots, allowing the affected pose features to be regenerated from the original inputs. The original historical output tree still lacks enough complete run metadata and feature records for exact bitwise reconstruction of every pre-correction derived result. This distinction and the older frozen source copies are documented in `SOURCE_TREE_AUDIT.md` and in the revised SI.

The remaining work is author review of the corrected scientific narrative and response, then depositing the corrected data/code package in the repository required by the journal. No prospective experiment or independent catalyst-family validation is claimed by this retrospective correction.


## Cross-catalyst occupancy update

The corrected Stage 2pp grids for the previously illustrated Fe(P7)Cl 1i / Fe(CMC-Por)Cl 2r shared identity yield Bhattacharyya overlap 0.978082, total variation distance 0.171882, and Jensen–Shannon divergence 0.030961 bits for the nitrene-centred all-heavy-atom channel across all 200 poses, after unit-sum normalization. A consistent scan of all 13 shared aryl identities confirms this pair remains rank 1 by Jensen–Shannon divergence. The previous overlap 0.9618 is superseded. These computed descriptor grids are not conformer populations or mechanistic evidence. The corrected visualization is `figures/figure5_corrected_cross_catalyst.png`.
