# Reviewer 1, comment 3: Representation and acquisition interaction

## Reviewer comment

The study separates PULSE-Pose representation from PULSE-Acquire ordering, but never tests whether the combination of both components outperforms either alone. It is possible that the ordering benefit depends on the quality of the representation, or conversely that a better representation reduces the need for sophisticated acquisition. This interaction is unexplored.

## Highlighted material

The quoted text below is highlighted in yellow in the corresponding document copy. Figure captions identify the adjacent artwork. Table entries reproduce the highlighted cells.

### Manuscript

**Abstract — paragraph 6**

> Substrate-scope construction is an information-acquisition problem: the order in which substrates are examined determines how efficiently catalyst behaviour is learned. Here, catalyst-contextual representation and information-guided substrate ordering were retrospectively evaluated in two small iron-porphyrin datasets for enantioselective intramolecular C(sp3)–H amination. PULSE-Pose introduced catalyst-referenced geometric descriptors that improved Fe(P7)Cl prediction relative to structure-only features, with the largest benefit under target-held-out validation and a smaller improvement when complete substrate families were withheld. PULSE-Acquire combines predictive uncertainty, molecular diversity, and chemical-family coverage to prioritise informative experiments from only tens of measured outcomes. The acquisition analysis compares learning trajectories at matched label budgets, distinguishing information-guided scope development from performance-oriented selection. In matched progressive-learning comparisons, uncertainty–diversity ordering reduced mean-prefix enantiomeric-excess error by 55.3% and 33.2% relative to reported substrate order for Fe(P7)Cl and Fe(CMC-Por)Cl, respectively, and outperformed diversity-first, random, and performance-first selection. These results show that catalyst-contextual representation and substrate order can each increase the information extracted from small catalytic datasets while addressing distinct aspects of model development. Across the evaluated endpoints and estimators, the clearest and most consistent acquisition improvements were observed for enantiomeric excess, while yield showed more variable trends.

**1 Introduction — paragraph 15**

> Within PULSE-Cat, PULSE-Acquire was developed to evaluate how substrate reveal order affects learning of the remaining scope at matched experimental budgets. The complementary PULSE-Pose component was developed to evaluate the predictive value of explicitly representing a substrate within the catalyst environment when only a small scope is available. The representation and acquisition components use different feature matrices and validation schemes and are assessed as complementary but separate analyses; their improvements are neither additive nor evidence that pose features caused the ordering advantage.

**3.1 PULSE-Pose molecular representation — paragraph 31**

> 3.1 PULSE-Pose molecular representation

**3.1 PULSE-Pose molecular representation — paragraph 32**

> Structure-only descriptors and fingerprints encode connectivity and physicochemical properties.[27,28] PULSE-Pose is conceptually inspired by SMART/SMARTpy catalyst-cavity descriptors, which use spatial probes to characterise reactive-pocket constraints.[25,26] Here, catalyst context is introduced by embedding substrate conformations relative to a fixed catalyst environment and summarising accessibility around the reported reactive site. This complements, rather than replaces, structure-only molecular representations and established 3D-QSAR approaches.

**3.1 PULSE-Pose molecular representation — paragraph 33**

> Baseline molecular inputs are sanitised starting-material azide SMILES. Compact RDKit physicochemical descriptors and radius-2 binary Morgan fingerprints encode size, lipophilicity, polarity, flexibility, ring content, heteroatom content, and local connectivity.[27,29] Outcome values, catalyst identity, source order, and family or scaffold labels are excluded from the molecular predictor columns. The complete descriptor list and fingerprint dimensions remain in SI Section S2.

**3.1 PULSE-Pose molecular representation — paragraph 35**

> The Stage-2p representation contains 248 fields organised by chemical function rather than treated as an uninterpreted descriptor block. These include radial and angular spatial distributions around the nitrene and transferred-hydrogen anchors, directed geometry along the reported N–H–C reaction corridor, corridor occupancy, symmetry and stratum-contrast summaries, relational distribution features, and compact catalyst-interaction or pocket-crowding quantities. Distributional kernels, equations, field ordering, and selected-column manifests are retained in the SI and computational release.

**3.2 Model fitting and validation — paragraph 39**

> Target-held-out validation and family-held-out validation address different questions. Target holdout asks whether a specific substrate can be predicted from the remaining scope, whereas family holdout removes every member of a chemical family and tests extrapolation across that family boundary. The matched Fe(P7)Cl development cohort contains 38 substrates from 17 families. Results from the two protocols are reported separately and are not numerically conflated; complete split memberships and inner-validation sizes remain in SI Section S3.

**3.2 Model fitting and validation — paragraph 40**

> Elastic Net is used for the principal representation comparison, Ridge for the dedicated matched acquisition comparison, and Elastic Net, Ridge, and Tanimoto-kNN for the independent acquisition robustness analyses.[34,35] Representation prediction is summarised by MAE, RMSE, and R². Progressive learning is evaluated using mean-prefix MAE for the dedicated matched comparison and trapezoidal AUC-MAE for the independent trajectories. Hyperparameter grids and implementation settings remain in the SI.

**3.3 PULSE-Acquire — paragraph 42**

> PULSE-Acquire tests whether substrate selection can improve learning of the remaining scope at matched numbers of known outcomes. The independent robustness progression begins from a fixed central-plus-diverse two-substrate seed. At each step, the known substrates are used to fit the model; unrevealed candidates are scored; one candidate is selected; its recorded outcome is revealed; the model is refitted; and prediction error is evaluated on the remaining unrevealed pool. Only outcomes already revealed at that prefix inform fitting and selection.

**3.3 PULSE-Acquire — paragraph 49**

> Two retrospective acquisition analyses are reported and should be distinguished. The dedicated matched comparison reproduces the archived route-specific progressions and compares mean-prefix MAE at matched numbers of revealed labels. In that comparison, “matched” refers to equivalent label budgets rather than identical initial substrate identities. The independent robustness analysis uses a separately documented progression protocol and evaluates multiple estimators using trajectory-level AUC-MAE. These analyses therefore test related but distinct questions and are not pooled numerically.

**4.1 Catalyst-referenced representations — paragraph 54**

> In the matched 38-substrate Fe(P7)Cl comparison (Fig. 3), adding selected pose descriptors to the structure-only Elastic Net model reduced target-held-out MAE from 12.612 to 8.583 ee percentage points, a 31.9% reduction. With complete families withheld, MAE decreased from 10.406 to 9.334, a smaller 10.3% improvement.

**4.1 Catalyst-referenced representations — paragraph 56**

> Figure 3. Selected catalyst-referenced descriptors improve prediction in the matched 38-substrate Fe(P7)Cl comparison using Elastic Net. Errors are ee percentage points. Target- and family-held-out validation answer different questions; SI Section S3 provides full metrics and split definitions.

**4.1 Catalyst-referenced representations — paragraph 57**

> The smaller family-held-out improvement indicates that catalyst-referenced geometry supplies useful information within the studied chemical domain but is less powerful when extrapolating across complete substrate families. The two protocols therefore support different levels of inference: the target-held-out result quantifies interpolation among represented chemistry, whereas the family-held-out result provides the more demanding test of transfer across family boundaries.

**4.2 Information-guided substrate acquisition — paragraph 65**

> The dedicated matched Ridge comparison measures learning by mean-prefix ee MAE. Uncertainty–diversity reduced this error from 21.672 to 9.684 for Fe(P7)Cl and from 13.155 to 8.787 for the Fe(CMC-Por)Cl aryl population relative to reported order, corresponding to 55.3% and 33.2% reductions (Table 2). It also outperformed diversity-first, random, and performance-first selection in both matched comparisons.

**4.2 Information-guided substrate acquisition — paragraph 69**

> An independent robustness analysis used a fixed molecular-plus-pose representation and three estimators. Uncertainty–diversity gave the lowest ee AUC-MAE for Elastic Net, Ridge, and Tanimoto-kNN in Fe(P7)Cl, and for Elastic Net and Ridge in Fe(CMC-Por)Cl. Diversity-first was slightly better for Fe(CMC-Por)Cl Tanimoto-kNN (171.515 versus 175.443 AUC-MAE). The result is therefore robust across several estimator/domain combinations but is not universal (Table 3 and Fig. 5).

**4.2 Information-guided substrate acquisition — paragraph 70**

> Table 3. Acquisition route giving the lowest independent ee AUC-MAE among the evaluated routes for each catalyst-domain and estimator combination. Not every estimator was evaluated under every stochastic comparison route; complete evaluated combinations are given in SI Tables S9–S12.

**4.3 Information content of molecular representations — paragraph 80**

> Representation is a chemical design choice encompassing both information content and computational complexity.[39] The occupancy and CREST/GFN2-xTB ablations show that adding more spatial, conformational, or electronic variables does not automatically improve prediction. Catalyst-contextual descriptors allow chemists to encode system-specific information and test its predictive value,[25,26,40] consistent with the broader use of steric and electrostatic descriptors in catalyst-library screening.[41]

**4.4 From retrospective analysis to experimental scope design — paragraph 84**

> A prospective chemist-facing workflow would begin with a small, chemically diverse measured scope, fit or update the predictive model, rank available substrates, select an informative candidate, perform the experiment, reveal the outcome, and repeat. Within such a loop, PULSE-Pose and PULSE-Acquire address different decisions. PULSE-Pose determines how each candidate is represented relative to the catalyst environment, whereas PULSE-Acquire determines which candidate should be prioritised next from the currently available information. PULSE-Cat is therefore intended as decision support rather than an autonomous replacement for chemical judgement. Candidate availability, synthesis cost, safety, mechanistic priorities, and practical experimental constraints can all override an algorithmic ranking, while the ranking provides an explicit estimate of what additional information a candidate may contribute.

**4.4 From retrospective analysis to experimental scope design — paragraph 88**

> Transferability should therefore be considered separately for the representation and acquisition components. Catalyst-referenced descriptors such as PULSE-Pose are intrinsically dependent on the geometry and chemistry of the catalytic environment; extension to a different catalyst or transformation may require redefining the reactive frame, interaction features, or conformational treatment. PULSE-Acquire, by contrast, operates at a more abstract experimental-design level and may not require the same molecular representation to be retained. Its broader principle—balancing what the model does not yet know with what regions of chemical space remain poorly represented—could be implemented using different reaction-appropriate descriptors, uncertainty estimates, and chemical groupings. Future cross-reaction studies should therefore distinguish representation transfer, in which a molecular encoding remains predictive in a new system, from acquisition transfer, in which an information-guided selection strategy remains beneficial after the representation and acquisition components have been adapted to the new chemistry. The present work establishes neither form of transfer across unrelated catalytic classes.

**4.4 From retrospective analysis to experimental scope design — paragraph 89**

> The principal limitations accordingly apply to both components of the framework. For PULSE-Pose, the present analysis assumes a known reactive site and a fixed catalyst reference geometry; substantially flexible catalysts or reactions with competing unknown sites may require catalyst-ensemble sampling, joint catalyst–substrate conformational treatment, or an upstream site-selectivity model. For PULSE-Acquire, the analyses remain retrospective, different acquisition routes can leave different remaining prediction pools, sensitivity to the exact initial measured panel has not been exhaustively characterised, and the preferred policy is not universal across estimators or endpoints. No prospective laboratory loop or cross-reaction validation is reported. These boundaries define the next validation tasks: testing acquisition robustness to different starting scopes, determining whether acquisition rules require system-specific recalibration, evaluating chemically distinct catalyst families, and ultimately measuring whether information-guided substrate selection improves prospective experimental scope construction.

**5 Conclusions — paragraph 91**

> Selected catalyst-referenced descriptors added predictive value for Fe(P7)Cl, while information-guided ordering lowered retrospective learning error in both studied systems. The strongest and most consistent acquisition support was observed for ee; the advantage was neither estimator- nor endpoint-universal. Together, the results support substrate order as an experimental-design variable for learning data-limited catalyst scopes and position catalyst-contextual representation and acquisition as complementary, separately tested components.

**Table 3 in document order — Table 3. Acquisition route giving the lowest independent ee AUC-MAE among the evaluated routes for each catalyst-domain and estimator combination. Not every estimator was evaluated under every stochastic comparison route; complete evaluated combinations are given in SI Tables S9–S12.**

- Domain | Estimator | Lowest ee AUC-MAE route
- Fe(P7)Cl | Elastic Net | Uncertainty–diversity
- Fe(P7)Cl | Ridge | Uncertainty–diversity
- Fe(P7)Cl | Tanimoto-kNN | Uncertainty–diversity
- Fe(CMC-Por)Cl | Elastic Net | Uncertainty–diversity
- Fe(CMC-Por)Cl | Ridge | Uncertainty–diversity
- Fe(CMC-Por)Cl | Tanimoto-kNN | Diversity-first

### Supporting information

**S2.1 Molecular connectivity and feature definitions — paragraph 22**

> Molecular inputs are sanitised starting-material azide SMILES. Missing or unparsable SMILES and duplicate substrate identifiers stop feature-table construction. Outcome, catalyst, source-order, and grouping metadata are not molecular predictor columns. Morgan bit vectors follow circular-fingerprint methodology [7]. B3–B5 use radius 2, binary rather than count fingerprints, and includeChirality=False.

**S2.1 Molecular connectivity and feature definitions — paragraph 23**

> The 15 RDKit descriptors, in the documented column order, are heavy-atom count, molecular weight, Crippen logP [8], topological polar surface area [9], formal charge, fraction of sp3 carbon, rotatable-bond count, total ring count, aromatic-ring count, hydrogen-bond acceptor count, hydrogen-bond donor count, heteroatom count, aliphatic-ring count, spiro-atom count, and tetrahedral chiral-centre count. The last counts assigned and unassigned centres through Chem.FindMolChiralCenters(includeUnassigned=True); it is not an absolute-configuration encoding. B1 retains molecular weight, logP, polar surface area, fraction sp3, rotatable bonds, and total rings.

**S2.1 Molecular connectivity and feature definitions — paragraph 26**

> C1 contains 44 retained geometry summaries; C2 contains 16 explicit catalyst-interaction summaries. Their functional categories include attack-corridor geometry, directed fields, stratum contrasts/stability, catalyst contacts, pocket crowding, and corridor obstruction. Exact selected column names are referred to the released feature manifests, data dictionary, and feature source described in Section S5.5. Repeated numeric interaction values are averaged by substrate before selecting C2; missing required interactions cause failure, not zero imputation. A separate legacy candidate-site builder uses a chirality-aware 2,048-bit fingerprint and is not B5. Literature on cavity descriptors motivates catalyst-aware representations but does not validate this study's feature selection [6,10].

**S3.1 Leakage controls and protocol separation — paragraph 77**

> A substrate, not a pose, is the statistical observation. All of its poses remain in the same split. Standardisation, constant-feature filtering, and any learned feature selection or projection must use training data only, separating model selection from performance evaluation [23]. Family and scaffold exclusions are separate tests; ordinary sequential replay is not relabelled as a scaffold-held-out evaluation.

**S3.1 Leakage controls and protocol separation — paragraph 78**

> In target-held-out development, one of the 38 Fe(P7)Cl substrates is withheld. MaxMin Morgan/Tanimoto selection chooses 29 training substrates from the other 37; eight form a validation set for model selection. For held-out families of size 1, 2, 3, or 12, documented training/validation counts are respectively 30/7, 29/7, 28/7, and 21/5. The release inventory identifies the model-report split files for family assignments and split membership (Section S5.2). The matched structure-only and structure-plus-pose matrices contain 547 and 1,241 columns: they are not B5 and P2. Their ordered feature lists, selected parameters, and fitting settings should be matched to the released feature/report trees and source code, rather than inferred from dimensions alone.

**S3.1 Leakage controls and protocol separation — paragraph 79**

> Later Stage 3 and CREST comparisons use the same 38 substrates from 17 families with outer and inner leave-one-family-out evaluation, but a different validation implementation and locked 248-column geometry reference. The separate occupancy comparison uses its own reported local-geometry reference. No row in Table S5 should be compared across protocol blocks as if it were a paired ablation.

**S3.3 Protocol-matched development results — paragraph 92**

> Table S5. Fe(P7)Cl ee development on the matched 38-substrate cohort. Each block is a separate validation experiment; all rows are Elastic Net results.

**S3.3 Protocol-matched development results — paragraph 94**

> The target- and family-holdout pose gains are 4.029 and 1.072 ee points, or 31.9% and 10.3%, respectively. The occupancy augmentation worsens MAE by 3.851 points (37.5%). Stage 3a-alt changes MAE by only -0.030 points; the combined Stage 3 block lowers MAE by 0.087 but worsens RMSE and R². No paired uncertainty interval for these small Stage 3 changes is available. These comparisons support selective retention of information, not a universal advantage of larger representations. The published descriptor literature provides methodological context, not evidence for these specific gains [6,30].

**S4.1 Reveal protocol and acquisition scores — paragraph 119**

> Independent progression begins from a central-plus-diverse two-substrate seed, then reveals one recorded label at a time. The initial seed is held fixed within deterministic route/estimator comparisons. At each prefix, feature processing and model fitting use only revealed labels; predictions and selection quantities are recorded before the next label is exposed. After revealing the selected substrate, the model is refitted and evaluated on the remaining unrevealed pool. These post-refit pool metrics and the pre-reveal selected-substrate error are distinct.

**S4.1 Reveal protocol and acquisition scores — paragraph 124**

> Two retrospective acquisition experiments are reported. The dedicated matched comparison reproduces archived route-specific progressions and compares mean-prefix MAE at equivalent numbers of revealed labels; “matched” therefore denotes matched label budgets rather than identical initial substrate identities. The independent robustness experiment instead uses the separately documented central-plus-diverse seed protocol, multiple estimators, and trajectory-level AUC-MAE. The two experiments test related but distinct questions and their numerical summaries are not pooled.

**S4.2 Learning metrics and the separate dedicated comparison — paragraph 132**

> Table S8. Dedicated matched Ridge route comparison: mean-prefix ee MAE. This is not the independent multi-estimator experiment.

**S4.2 Learning metrics and the separate dedicated comparison — paragraph 134**

> The relative reductions from reported order to uncertainty–diversity are 55.3% and 33.2%, rounded to one decimal place. These percentages compare retrospective learning trajectories at matched label budgets and do not estimate prospective reductions in laboratory effort. The dedicated record also stores “AUC” values of 780.199/348.624 for Fe(P7)Cl and 315.717/210.884 for Fe(CMC-Por)Cl (reported order/uncertainty–diversity). These behave as mean-prefix MAE times prefix count to rounding precision, not demonstrably as the independent experiment's trapezoidal integral. They are therefore not mixed with the following AUC tables. The dedicated matched comparison has been traced to its archived run outputs. For both catalyst domains, the corresponding manifests identify analysis populations and exclusions, the representation is rdkit_morgan_stage2p, and selection-events.csv records acquisition sequences. The raw learning-curve records contain per-prefix MAE, RMSE, and Spearman statistics. Re-averaging the recorded prefix MAEs reproduces all ten values in Table S8 at the reported three-decimal precision and supports the 55.3% and 33.2% reductions. A complete substrate-level prediction archive is not available for every run, and the manifests lack explicit input hashes and a run-specific random-seed field. These limitations concern complete archival regeneration, not recalculation of the reported aggregate learning metrics; Section S5.3 identifies the records and distinguishes these reproducibility levels.

**S4.3 Complete independent-progression summaries — paragraph 136**

> Tables S9–S12 present all 56 documented independent route/estimator rows. The representation is fixed at rdkit_morgan_stage2p: 15 RDKit descriptors, 1,024 Morgan bits, and 248 Stage 2p fields (1,287 columns, P2 composition). This does not imply that Tanimoto-kNN uses non-fingerprint columns. Its matrix and settings must not be substituted for the separate dedicated comparison.

**S4.3 Complete independent-progression summaries — paragraph 146**

> Uncertainty–diversity minimises ee AUC-MAE for all three Fe(P7)Cl estimators and for Fe(CMC-Por)Cl Elastic Net/Ridge, but diversity-first gives lower Fe(CMC-Por)Cl Tanimoto-kNN AUC (171.515 versus 175.443). The latter estimator also reaches n₉0 earlier under reported order than under uncertainty–diversity (7 versus 14 labels). Thus threshold convergence and integrated error can disagree.

**S6.1 Feature groups, populations, and retrospective replay — paragraph 193**

> The predictor contract is rdkit_morgan_stage2p, imported from scripts/scope_progression.py. Ridge predictions determine learning error; disagreement between Ridge and Tanimoto-kNN predictions contributes to acquisition. Elastic Net is disabled in this study. Each replay starts with two substrates selected by the existing diversity-first seed procedure, using random.Random(0). Remaining-pool Ridge MAE is evaluated at labelled prefixes from 2 to Nc-1, where Nc is the active population for cell c; one substrate remains unrevealed at the end. At each acquisition step, the highest-scoring whole substrate is selected, ties favour earlier source order, and the recorded outcome is revealed before refitting. Only revealed outcomes enter the within-route model fitting and acquisition calculation; the outer weight search nevertheless uses retrospective prediction errors from the full replay.

**Table 6 in document order — Table S5. Fe(P7)Cl ee development on the matched 38-substrate cohort. Each block is a separate validation experiment; all rows are Elastic Net results.**

- Protocol and representation | MAE | RMSE | R²
- Target holdout: structure only | 12.612 | 15.183 | 0.064
- Target holdout: structure + pose | 8.583 | 11.932 | 0.422
- Family holdout: structure only | 10.406 | 13.525 | 0.257
- Family holdout: structure + pose | 9.334 | 12.557 | 0.359
- Occupancy comparison: local geometry | 10.281 | 13.023 | 0.311
- Occupancy comparison: +655 features | 14.132 | 17.005 | -0.175
- Nested families: locked geometry | 8.498 | 11.357 | 0.476
- Nested families: +Stage 3a-alt | 8.468 | 11.289 | 0.482
- Nested families: +Stage 3b | 8.664 | 11.978 | 0.417
- Nested families: +Stage 3a-alt +Stage 3b | 8.411 | 11.810 | 0.433

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

## Factorial analysis completed

The prespecified plan, results, validation and response are recorded in `experiment_plan.md`, `interaction_results.md`, `validation_report.txt`, and `reviewer_response_draft.md`. The matched comparison found that full Stage 2p plus acquisition improved on full Stage 2p plus source order but had higher average held-out error than both structure-only cells in both domains. Results are descriptive and use a different representation and model from the original selected-feature Elastic Net benchmark.
