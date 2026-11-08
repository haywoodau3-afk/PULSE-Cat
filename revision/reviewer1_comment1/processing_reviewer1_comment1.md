# Reviewer 1, comment 1: Uncertainty and initial seeds

## Reviewer comment

The matched acquisition comparison uses mean-prefix MAE as the primary metric, but no confidence intervals or statistical significance tests are reported. Given the small number of substrates (38 and 26), the observed 55.3% and 33.2% reductions could arise from chance variation, and the stability of these improvements across different initial seeds is not examined.

## Highlighted material

The quoted text below is highlighted in yellow in the corresponding document copy. Figure captions identify the adjacent artwork. Table entries reproduce the highlighted cells.

### Manuscript

**2.2 Dataset populations — paragraph 23**

> The numerical populations used for curation, representation development, progression, and cross-catalyst visualisation are distinct (Table 1). The retained ledgers contain 41 Fe(P7)Cl and 50 Fe(CMC-Por)Cl records; the latter comprise 33 aryl substrates and 17 sulfonyl controls. The principal PULSE-Pose development comparison uses 38 Fe(P7)Cl substrates from 17 families. Independent Fe(CMC-Por)Cl progression uses 26 active aryl labels per endpoint rather than the complete retained ledger, and the exact remaining pool depends on the reveal route. Only 13 exact canonical aryl identities are shared between catalyst domains and eligible for paired geometry comparison. These counts describe different analysis inputs and must not be treated as interchangeable versions of one dataset.

**3.2 Model fitting and validation — paragraph 39**

> Target-held-out validation and family-held-out validation address different questions. Target holdout asks whether a specific substrate can be predicted from the remaining scope, whereas family holdout removes every member of a chemical family and tests extrapolation across that family boundary. The matched Fe(P7)Cl development cohort contains 38 substrates from 17 families. Results from the two protocols are reported separately and are not numerically conflated; complete split memberships and inner-validation sizes remain in SI Section S3.

**3.2 Model fitting and validation — paragraph 40**

> Elastic Net is used for the principal representation comparison, Ridge for the dedicated matched acquisition comparison, and Elastic Net, Ridge, and Tanimoto-kNN for the independent acquisition robustness analyses.[34,35] Representation prediction is summarised by MAE, RMSE, and R². Progressive learning is evaluated using mean-prefix MAE for the dedicated matched comparison and trapezoidal AUC-MAE for the independent trajectories. Hyperparameter grids and implementation settings remain in the SI.

**3.3 PULSE-Acquire — paragraph 42**

> PULSE-Acquire tests whether substrate selection can improve learning of the remaining scope at matched numbers of known outcomes. The independent robustness progression begins from a fixed central-plus-diverse two-substrate seed. At each step, the known substrates are used to fit the model; unrevealed candidates are scored; one candidate is selected; its recorded outcome is revealed; the model is refitted; and prediction error is evaluated on the remaining unrevealed pool. Only outcomes already revealed at that prefix inform fitting and selection.

**3.3 PULSE-Acquire — paragraph 49**

> Two retrospective acquisition analyses are reported and should be distinguished. The dedicated matched comparison reproduces the archived route-specific progressions and compares mean-prefix MAE at matched numbers of revealed labels. In that comparison, “matched” refers to equivalent label budgets rather than identical initial substrate identities. The independent robustness analysis uses a separately documented progression protocol and evaluates multiple estimators using trajectory-level AUC-MAE. These analyses therefore test related but distinct questions and are not pooled numerically.

**3.3 PULSE-Acquire — paragraph 51**

> Mean-prefix MAE is the arithmetic mean of the remaining-pool MAE values across the evaluated label budgets and is the primary metric for the dedicated matched comparison. Independent robustness uses trapezoidal AUC-MAE, which integrates the learning trajectory over prefix size. Although both metrics summarise progressive learning, they weight the evaluated label budgets differently and are therefore reported separately. Improvements are interpreted as relative gains in predictive learning efficiency over matched retrospective budgets; prospective evaluation would be required to determine how these gains translate into experimental effort.

**4.2 Information-guided substrate acquisition — paragraph 65**

> The dedicated matched Ridge comparison measures learning by mean-prefix ee MAE. Uncertainty–diversity reduced this error from 21.672 to 9.684 for Fe(P7)Cl and from 13.155 to 8.787 for the Fe(CMC-Por)Cl aryl population relative to reported order, corresponding to 55.3% and 33.2% reductions (Table 2). It also outperformed diversity-first, random, and performance-first selection in both matched comparisons.

**4.2 Information-guided substrate acquisition — paragraph 66**

> These comparisons support an information-selection effect within the available substrate sets. Reported order is used as a reproducible literature-derived comparator based on source presentation, rather than as a reconstruction of laboratory chronology. The analysis evaluates the unrevealed candidate pool at each step; because each acquisition policy reveals a different sequence of substrates, this pool evolves differently along each trajectory. The resulting reductions quantify how substrate ordering affected retrospective model error as labels accumulated, while prospective validation is needed to establish the corresponding effect on experimental effort.

**4.2 Information-guided substrate acquisition — paragraph 67**

> Table 2. Central matched acquisition comparison: mean-prefix ee MAE (ee percentage points) using Ridge. Lower values indicate more accurate learning at the evaluated label budgets; the Fe(CMC-Por)Cl population is aryl-only.

**4.2 Information-guided substrate acquisition — paragraph 69**

> An independent robustness analysis used a fixed molecular-plus-pose representation and three estimators. Uncertainty–diversity gave the lowest ee AUC-MAE for Elastic Net, Ridge, and Tanimoto-kNN in Fe(P7)Cl, and for Elastic Net and Ridge in Fe(CMC-Por)Cl. Diversity-first was slightly better for Fe(CMC-Por)Cl Tanimoto-kNN (171.515 versus 175.443 AUC-MAE). The result is therefore robust across several estimator/domain combinations but is not universal (Table 3 and Fig. 5).

**4.2 Information-guided substrate acquisition — paragraph 70**

> Table 3. Acquisition route giving the lowest independent ee AUC-MAE among the evaluated routes for each catalyst-domain and estimator combination. Not every estimator was evaluated under every stochastic comparison route; complete evaluated combinations are given in SI Tables S9–S12.

**4.2 Information-guided substrate acquisition — paragraph 73**

> Figure 5. Independent ee acquisition robustness analyses. Top (a): representative Fe(P7)Cl Ridge learning trajectories; reported order denotes source presentation rather than verified laboratory chronology. Bottom (b): reported-order and uncertainty–diversity AUC-MAE across estimators and catalyst domains; lower values indicate lower integrated error. Other acquisition routes are reported in Table 3 and SI Tables S9–S12. These analyses are distinct from the mean-prefix comparison in Table 2.

**4.4 From retrospective analysis to experimental scope design — paragraph 89**

> The principal limitations accordingly apply to both components of the framework. For PULSE-Pose, the present analysis assumes a known reactive site and a fixed catalyst reference geometry; substantially flexible catalysts or reactions with competing unknown sites may require catalyst-ensemble sampling, joint catalyst–substrate conformational treatment, or an upstream site-selectivity model. For PULSE-Acquire, the analyses remain retrospective, different acquisition routes can leave different remaining prediction pools, sensitivity to the exact initial measured panel has not been exhaustively characterised, and the preferred policy is not universal across estimators or endpoints. No prospective laboratory loop or cross-reaction validation is reported. These boundaries define the next validation tasks: testing acquisition robustness to different starting scopes, determining whether acquisition rules require system-specific recalibration, evaluating chemically distinct catalyst families, and ultimately measuring whether information-guided substrate selection improves prospective experimental scope construction.

**Table 2 in document order — Table 2. Central matched acquisition comparison: mean-prefix ee MAE (ee percentage points) using Ridge. Lower values indicate more accurate learning at the evaluated label budgets; the Fe(CMC-Por)Cl population is aryl-only.**

- Acquisition route | Fe(P7)Cl | Fe(CMC-Por)Cl
- Reported order | 21.672 | 13.155
- Diversity-first | 11.197 | 9.842
- Random | 11.261 | 13.654
- Performance-first | 11.716 | 14.514
- Uncertainty–diversity | 9.684 | 8.787

**Table 3 in document order — Table 3. Acquisition route giving the lowest independent ee AUC-MAE among the evaluated routes for each catalyst-domain and estimator combination. Not every estimator was evaluated under every stochastic comparison route; complete evaluated combinations are given in SI Tables S9–S12.**

- Domain | Estimator | Lowest ee AUC-MAE route
- Fe(P7)Cl | Elastic Net | Uncertainty–diversity
- Fe(P7)Cl | Ridge | Uncertainty–diversity
- Fe(P7)Cl | Tanimoto-kNN | Uncertainty–diversity
- Fe(CMC-Por)Cl | Elastic Net | Uncertainty–diversity
- Fe(CMC-Por)Cl | Ridge | Uncertainty–diversity
- Fe(CMC-Por)Cl | Tanimoto-kNN | Diversity-first

### Supporting information

**S1.1.1 Reaction sources and curation — paragraph 15**

> Table S2. Reported populations. Counts describe different analysis inputs, not successive interchangeable versions of one dataset.

**S1.1.1 Reaction sources and curation — paragraph 17**

> The independent progression summaries end at 37 revealed Fe(P7)Cl ee labels, 38 yield labels, and 25 Fe(CMC-Por)Cl aryl labels, leaving a route-dependent residual pool. These progression endpoints must not be substituted for the 38-substrate development cohort. Removing only 1ad from 41 records cannot explain a 39-record progression set. The release inventory identifies dataset-id-lists.csv as the explicit reconciliation; its population memberships and exclusion reasons must be used when reproducing each analysis.

**S3.1 Leakage controls and protocol separation — paragraph 78**

> In target-held-out development, one of the 38 Fe(P7)Cl substrates is withheld. MaxMin Morgan/Tanimoto selection chooses 29 training substrates from the other 37; eight form a validation set for model selection. For held-out families of size 1, 2, 3, or 12, documented training/validation counts are respectively 30/7, 29/7, 28/7, and 21/5. The release inventory identifies the model-report split files for family assignments and split membership (Section S5.2). The matched structure-only and structure-plus-pose matrices contain 547 and 1,241 columns: they are not B5 and P2. Their ordered feature lists, selected parameters, and fitting settings should be matched to the released feature/report trees and source code, rather than inferred from dimensions alone.

**S3.2 Prediction metrics and uncertainty — paragraph 90**

> Bootstrap resampling estimates sampling variability by drawing observations with replacement [29]. Confidence intervals are limited to those documented for the corresponding analysis. CREST paired bootstraps resample substrate IDs with replacement using identical indices for both models, 20,000 draws, and NumPy seed 20260907. The statistic is baseline MAE minus augmentation MAE, so positive values favour augmentation. This is not a family-cluster bootstrap, a posterior probability, or prospective experimental confidence.

**S4.1 Reveal protocol and acquisition scores — paragraph 119**

> Independent progression begins from a central-plus-diverse two-substrate seed, then reveals one recorded label at a time. The initial seed is held fixed within deterministic route/estimator comparisons. At each prefix, feature processing and model fitting use only revealed labels; predictions and selection quantities are recorded before the next label is exposed. After revealing the selected substrate, the model is refitted and evaluated on the remaining unrevealed pool. These post-refit pool metrics and the pre-reveal selected-substrate error are distinct.

**S4.1 Reveal protocol and acquisition scores — paragraph 124**

> Two retrospective acquisition experiments are reported. The dedicated matched comparison reproduces archived route-specific progressions and compares mean-prefix MAE at equivalent numbers of revealed labels; “matched” therefore denotes matched label budgets rather than identical initial substrate identities. The independent robustness experiment instead uses the separately documented central-plus-diverse seed protocol, multiple estimators, and trajectory-level AUC-MAE. The two experiments test related but distinct questions and their numerical summaries are not pooled.

**S4.2 Learning metrics and the separate dedicated comparison — paragraph 128**

> For prefix sizes n₁,…,nm, mean-prefix MAE is the arithmetic mean of the corresponding pool errors. The documented independent-trajectory convention is trapezoidal integration,

**S4.2 Learning metrics and the separate dedicated comparison — paragraph 130**

> where the documented specification describes M as median learning-curve MAE. Replicate aggregation and prefix membership are specified by the trajectory manifests. AUC has units of percentage points times label count and is not mean-prefix error; absolute AUCs across unequal prefix ranges should not be ranked as comparable datasets.

**S4.2 Learning metrics and the separate dedicated comparison — paragraph 132**

> Table S8. Dedicated matched Ridge route comparison: mean-prefix ee MAE. This is not the independent multi-estimator experiment.

**S4.2 Learning metrics and the separate dedicated comparison — paragraph 134**

> The relative reductions from reported order to uncertainty–diversity are 55.3% and 33.2%, rounded to one decimal place. These percentages compare retrospective learning trajectories at matched label budgets and do not estimate prospective reductions in laboratory effort. The dedicated record also stores “AUC” values of 780.199/348.624 for Fe(P7)Cl and 315.717/210.884 for Fe(CMC-Por)Cl (reported order/uncertainty–diversity). These behave as mean-prefix MAE times prefix count to rounding precision, not demonstrably as the independent experiment's trapezoidal integral. They are therefore not mixed with the following AUC tables. The dedicated matched comparison has been traced to its archived run outputs. For both catalyst domains, the corresponding manifests identify analysis populations and exclusions, the representation is rdkit_morgan_stage2p, and selection-events.csv records acquisition sequences. The raw learning-curve records contain per-prefix MAE, RMSE, and Spearman statistics. Re-averaging the recorded prefix MAEs reproduces all ten values in Table S8 at the reported three-decimal precision and supports the 55.3% and 33.2% reductions. A complete substrate-level prediction archive is not available for every run, and the manifests lack explicit input hashes and a run-specific random-seed field. These limitations concern complete archival regeneration, not recalculation of the reported aggregate learning metrics; Section S5.3 identifies the records and distinguishes these reproducibility levels.

**S4.3 Complete independent-progression summaries — paragraph 136**

> Tables S9–S12 present all 56 documented independent route/estimator rows. The representation is fixed at rdkit_morgan_stage2p: 15 RDKit descriptors, 1,024 Morgan bits, and 248 Stage 2p fields (1,287 columns, P2 composition). This does not imply that Tanimoto-kNN uses non-fingerprint columns. Its matrix and settings must not be substituted for the separate dedicated comparison.

**S4.3 Complete independent-progression summaries — paragraph 137**

> Route codes D, H, P, R, and U mean diversity-first, reported order, performance-first, random, and uncertainty–diversity. Model codes EN, R, and K mean Elastic Net, Ridge, and Tanimoto-kNN. NA means the threshold was not reached. Final n is the number of revealed labels, not the number of test predictions. The reference MAE and Δ (final minus reference) are documented summary values; discrepancies of 0.001 from subtraction of rounded MAEs are retained. Final-prefix MAEs concern route-dependent remaining substrates and cannot establish superiority on a common test set.

**S4.3 Complete independent-progression summaries — paragraph 146**

> Uncertainty–diversity minimises ee AUC-MAE for all three Fe(P7)Cl estimators and for Fe(CMC-Por)Cl Elastic Net/Ridge, but diversity-first gives lower Fe(CMC-Por)Cl Tanimoto-kNN AUC (171.515 versus 175.443). The latter estimator also reaches n₉0 earlier under reported order than under uncertainty–diversity (7 versus 14 labels). Thus threshold convergence and integrated error can disagree.

**S4.3 Complete independent-progression summaries — paragraph 152**

> Figure S6. Independent acquisition analyses, retained as corroboration rather than the source of the main-text 55.3% and 33.2% reductions. (A) Fe(P7)Cl Ridge ee-learning trajectories. The displayed legend uses “reported_order” for the source record's “historical_order”; only the legend wording has changed, not the curves or data. Reported order is not verified laboratory chronology. Random curves show the mean and 25th/75th percentiles. (B) Reported-order versus uncertainty–diversity integrated ee error for three estimators in each catalyst domain. These trapezoidal AUC-MAE results are distinct from the dedicated mean-prefix comparison in Table S8 and the main-text matched-acquisition table. Panel B does not display every competing route; Tables S9–S12 give complete comparisons, including the Fe(CMC-Por)Cl Tanimoto-kNN exception.

**S5.2 Predictions, validation splits, and feature matrices — paragraph 163**

> Recalculation of MAE, RMSE, R², confidence intervals, and learning-curve statistics requires matching the endpoint, validation protocol, evaluation population, and resampling unit. Final-prefix errors from different acquisition routes are not common-test-set comparisons.

**S5.3 Central matched acquisition replay: provenance and reproducibility — paragraph 166**

> For Fe(P7)Cl, the archived learning curves are located at data/jacs_2025/scope_progression/learning-curve.csv. The same run directory contains scope-progression-manifest.json, which records the population and run information, and selection-events.csv, which records acquisition sequences. For Fe(CMC-Por)Cl, the corresponding run information and progression outputs are retained under data/expansion/catalyst_rerun/cmcpor_aryl_scope_progression/. The dedicated comparison uses the rdkit_morgan_stage2p representation and standardised Ridge regression with α=10. These identified run records, rather than representation dimensions alone, establish the link to the dedicated comparison.

**S5.3 Central matched acquisition replay: provenance and reproducibility — paragraph 167**

> The recorded initial substrate pairs are 1a/1b for the Fe(P7)Cl reported-order route and 1a/1am for uncertainty–diversity; for Fe(CMC-Por)Cl they are 2aa/2ab and 2b/2ac, respectively. These are route-specific initial substrate selections, distinct from the pseudorandom seed used by code. Acquisition sequences are retained in selection-events.csv, and the learning curves report MAE, RMSE, and Spearman statistics at each evaluated prefix. Re-averaging the recorded prefix MAEs reproduces 21.672 and 9.684 for Fe(P7)Cl and 13.155 and 8.787 for Fe(CMC-Por)Cl (reported order and uncertainty–diversity, respectively), at the precision reported in the main-text matched-acquisition table. The remaining six policy means are reproduced from their corresponding learning-curve records by the same arithmetic averaging convention.

**S5.3 Central matched acquisition replay: provenance and reproducibility — paragraph 168**

> The archive supports reconstruction of the reported aggregate learning curves and mean-prefix comparisons, but it is not a complete frozen prediction-level execution archive. A complete per-substrate prediction log is not available for the Fe(P7)Cl run, while the Fe(CMC-Por)Cl archive contains only the locked-audit prediction records. The original manifests do not record explicit input hashes or a run-specific random seed. The code default is 20260824, but the run manifests do not assign that value to the original execution; it is therefore not treated as verified run metadata. These limitations prevent a claim of bitwise regeneration of the original execution but do not prevent recalculation of the reported aggregate metrics from the archived outputs.

**Table 2 in document order — Table S2. Reported populations. Counts describe different analysis inputs, not successive interchangeable versions of one dataset.**

- Analysis population | Count | Definition and qualification
- Fe(P7)Cl retained ledger | 41 | Substrate-identity records; includes the valid zero-ee record 1z.
- Fe(P7)Cl matched development ee | 38 | 17 families; excludes 1ad, 1an, and 1z. Reported cohort identifier f11a0a2ec491.
- Initial Fe(P7)Cl yield benchmark | 41 | 19 families; distinct from progressive yield.
- Fe(P7)Cl CREST completion set | 40 | Excludes 1z; removing 1ad and 1an leaves all 38 modelled substrates.
- Fe(P7)Cl independent progression | 38/39 | 38 usable ee and 39 yield labels; the release inventory identifies dataset-id-lists.csv for reconciliation.
- Fe(CMC-Por)Cl retained ledger | 50 | 33 aryl and 17 sulfonyl substrates; sulfonyl substrates are a pathway control.
- Fe(CMC-Por)Cl independent progression | 26 | Active aryl labels per endpoint in the independent progression record; not the complete 33-record aryl ledger.
- Shared canonical aryl identities | 13 | Cross-catalyst overlap; excluded from source training as specified above.
- Density-field inventory | 91 | 41 Fe(P7)Cl plus 50 Fe(CMC-Por)Cl substrate-level fields, not 91 unique identities across domains.

**Table 9 in document order — Table S8. Dedicated matched Ridge route comparison: mean-prefix ee MAE. This is not the independent multi-estimator experiment.**

- Acquisition route | Fe(P7)Cl | Fe(CMC-Por)Cl aryl
- Reported order | 21.672 | 13.155
- Diversity-first | 11.197 | 9.842
- Random | 11.261 | 13.654
- Performance-first | 11.716 | 14.514
- Uncertainty–diversity | 9.684 | 8.787

**Table 10 in document order — Table S9. Fe(P7)Cl enantioselectivity: independent-progression summaries.**

- Route | Model | Final n | Final MAE | AUC-MAE | n₉0 | Ref. MAE | Δ
- D | EN | 37 | 4.454 | 343.044 | 4 | 13.238 | -8.785
- D | R | 37 | 3.772 | 391.662 | 24 | 13.238 | -9.466
- D | K | 37 | 1.215 | 368.284 | 19 | 13.238 | -12.024
- H | EN | 37 | 8.838 | 741.152 | NA | 13.238 | -4.400
- H | R | 37 | 9.719 | 757.662 | NA | 13.238 | -3.519
- H | K | 37 | 3.969 | 601.044 | 37 | 13.238 | -9.269
- P | EN | 37 | 16.511 | 403.781 | NA | 13.238 | 3.273
- P | R | 37 | 18.224 | 403.093 | 7 | 13.238 | 4.986
- P | K | 37 | 27.543 | 525.131 | NA | 13.238 | 14.304
- R | R | 37 | 8.122 | 355.527 | 29 | 13.238 | -5.116
- R | K | 37 | 8.344 | 337.493 | 27 | 13.238 | -4.894
- U | EN | 37 | 4.454 | 325.119 | 16 | 13.238 | -8.785
- U | R | 37 | 3.772 | 337.181 | 16 | 13.238 | -9.466
- U | K | 37 | 1.215 | 306.116 | 17 | 13.238 | -12.024

**Table 12 in document order — Table S11. Fe(CMC-Por)Cl enantioselectivity: independent-progression summaries.**

- Route | Model | Final n | Final MAE | AUC-MAE | n₉0 | Ref. MAE | Δ
- D | EN | 25 | 4.111 | 217.781 | 13 | 11.580 | -7.469
- D | R | 25 | 4.141 | 221.203 | 14 | 11.580 | -7.439
- D | K | 25 | 2.089 | 171.515 | 13 | 11.580 | -9.490
- H | EN | 25 | 5.352 | 292.463 | 12 | 11.580 | -6.228
- H | R | 25 | 8.773 | 297.250 | 16 | 11.580 | -2.807
- H | K | 25 | 1.482 | 238.721 | 7 | 11.580 | -10.098
- P | EN | 25 | 5.352 | 336.989 | 23 | 11.580 | -6.228
- P | R | 25 | 8.773 | 331.021 | 23 | 11.580 | -2.807
- P | K | 25 | 1.482 | 187.666 | 6 | 11.580 | -10.098
- R | R | 25 | 10.644 | 274.596 | 19 | 11.580 | -0.935
- R | K | 25 | 9.781 | 225.759 | 12 | 11.580 | -1.799
- U | EN | 25 | 4.111 | 193.940 | 6 | 11.580 | -7.469
- U | R | 25 | 4.141 | 195.890 | 8 | 11.580 | -7.439
- U | K | 25 | 2.089 | 175.443 | 14 | 11.580 | -9.490
