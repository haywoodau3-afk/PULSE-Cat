# Reviewer 1, comment 7: Active learning baselines

## Reviewer comment

The study compares uncertainty-diversity against only three baselines: diversity-first, random, and performance-first. More established active learning strategies such as query-by-committee, expected improvement, or Thompson sampling are not evaluated. The reported advantage over these simple baselines does not demonstrate that the proposed acquisition function is competitive with state-of-the-art methods.

## Highlighted material

The quoted text below is highlighted in yellow in the corresponding document copy. Figure captions identify the adjacent artwork. Table entries reproduce the highlighted cells.

### Manuscript

**1 Introduction — paragraph 10**

> Substrate scopes establish catalyst generality, but their construction also determines which chemical limitations are exposed.[1] Systematic substrate selection addresses the representativeness of a scope,[2] while reaction optimisation balances exploration and exploitation to identify desirable outcomes.[3,4] The question addressed in this work is whether the sequence in which a substrate scope is constructed can also be optimised for chemical information. The substrate expected to give the highest yield or ee and the substrate expected to be most informative may differ: the former evaluates promising chemistry, while the latter may clarify uncertain or underrepresented regions of the scope.

**1 Introduction — paragraph 11**

> Recent machine learning in catalysis spans data-efficient reaction optimisation and data-intensive prediction of reactivity and selectivity.[3,5,6,7,8] Selected examples illustrate this breadth. Bayesian optimisation efficiently explores multidimensional reaction conditions, as demonstrated for palladium-catalysed arylation,[3] while high-throughput experimentation enables systematic screening of catalyst and condition combinations.[9] Beyond optimisation, a mechanism-informed multitask graph neural network predicted arene C–H functionalisation site selectivity using 256 reactions,[10] and three-dimensional deep learning predicted ruthenium-catalysed ketone hydrogenation enantioselectivity using literature data supplemented by more than 1,000 high-throughput experiments.[8] These predictive studies illustrate the value of substantial training datasets, rather than a requirement shared by all machine-learning methods. Condition optimisation asks which reaction settings should be tested to improve an outcome, whereas substrate-scope information acquisition asks which molecular example should be measured to learn catalyst behaviour across a scope.

**1 Introduction — paragraph 12**

> At the frontier of catalyst development, a practical starting point is often a substrate scope containing only tens of measured examples, rather than a large training dataset.[11,12] Sparse chemical-space coverage and overfitting challenge reliable prediction, motivating chemically informed small-data models.[11,12,13,14] Decision-support tools should therefore complement chemical judgement by identifying informative next experiments from limited observations.[15,16,17] Relevant precedents include Rana and co-workers' representative substrate panels selected through chemical-space mapping[2] and Souza and co-workers' uncertainty-guided Ni-photoredox yield modelling across large virtual spaces using hundreds of measurements.[18] Active learning itself is not proposed as a new principle. The present aim is not to construct a universally accurate reaction predictor from tens of points, but to ask which measurement is most informative when only tens of measurements are available.

**3.3 PULSE-Acquire — paragraph 42**

> PULSE-Acquire tests whether substrate selection can improve learning of the remaining scope at matched numbers of known outcomes. The independent robustness progression begins from a fixed central-plus-diverse two-substrate seed. At each step, the known substrates are used to fit the model; unrevealed candidates are scored; one candidate is selected; its recorded outcome is revealed; the model is refitted; and prediction error is evaluated on the remaining unrevealed pool. Only outcomes already revealed at that prefix inform fitting and selection.

**3.3 PULSE-Acquire — paragraph 46**

> The acquisition functions combine four normalised quantities that describe different properties of each unrevealed candidate. Predictive uncertainty, represented by U, measures the model's limited confidence in the candidate outcome. Molecular diversity, D, rewards candidates that are structurally non-redundant relative to the substrates already revealed, while chemical-family coverage, C, increases the priority of candidates belonging to incompletely represented substrate families. Predicted performance, P, is the model-estimated outcome and is included only in the performance-first comparator. Normalisation places these quantities on comparable scales before their weighted combination. The frozen acquisition scores are

**3.3 PULSE-Acquire — paragraph 47**

> SUD=0.40U+0.40D+0.20C,

**3.3 PULSE-Acquire — paragraph 48**

> Sperformance=0.50P+0.30U+0.20D.

**3.3 PULSE-Acquire — paragraph 49**

> Two retrospective acquisition analyses are reported and should be distinguished. The dedicated matched comparison reproduces the archived route-specific progressions and compares mean-prefix MAE at matched numbers of revealed labels. In that comparison, “matched” refers to equivalent label budgets rather than identical initial substrate identities. The independent robustness analysis uses a separately documented progression protocol and evaluates multiple estimators using trajectory-level AUC-MAE. These analyses therefore test related but distinct questions and are not pooled numerically.

**3.3 PULSE-Acquire — paragraph 50**

> Uncertainty–diversity prioritises candidates that are uncertain, molecularly non-redundant, and informative for family coverage. Performance-first instead favours predicted outcome while retaining uncertainty and diversity terms. These routes are compared with source-reported order, diversity-first selection, and whole-substrate random selection. Exact normalisation, tie-breaking, and candidate-set rules are documented in SI Section S4 and the released algorithm specification.

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

**4.2 Information-guided substrate acquisition — paragraph 74**

> The three components of uncertainty–diversity address different failure modes in sequential scope construction. Predictive uncertainty identifies substrates for which the current model has limited confidence, but uncertainty alone may repeatedly concentrate sampling within a narrow region of chemical space. Molecular diversity discourages such redundancy by favouring candidates that are structurally distinct from the measured set, although structural novelty does not necessarily imply that a substrate will be informative about the response surface.[38] Chemical-family coverage provides a complementary safeguard by preventing recognised substrate classes from remaining systematically underrepresented. The acquisition score therefore balances three distinct questions: where the model is uncertain, where the chemistry is insufficiently sampled, and which regions of the defined scope remain poorly represented. Their combination is intended to avoid overcommitting to any single notion of informativeness.

**4.2 Information-guided substrate acquisition — paragraph 77**

> Performance-first and information-first selection address complementary experimental objectives. Performance-first selection prioritises substrates that the current model expects to give favourable outcomes, making it appropriate when the immediate aim is to identify synthetically useful chemistry. Information-first selection prioritises measurements expected to reduce uncertainty about catalyst behaviour across the wider scope. A predicted high-performing substrate can be valuable for establishing practical utility, whereas an uncertain or structurally distinct substrate can be valuable for refining the learned response surface. This distinction separates optimisation, which asks where the reaction is expected to perform best, from characterisation, which asks where and how catalyst behaviour changes across chemical space. The lower retrospective learning error observed for uncertainty–diversity relative to performance-first selection is therefore consistent with its information-oriented objective.

**4.4 From retrospective analysis to experimental scope design — paragraph 85**

> For PULSE-Acquire, prospective use would require calibration and validation of the acquisition score for each new reaction context. The present uncertainty–diversity policy combines predictive uncertainty, molecular diversity, and chemical-family coverage because these terms address complementary forms of incomplete knowledge in the studied scopes. In a different catalytic system, however, the relevant notion of diversity, the definition of a chemically meaningful family, the reliability of model-derived uncertainty, and the relative importance of these terms may differ. The present 0.40/0.40/0.20 weighting should therefore be regarded as a study-specific acquisition rule rather than a universally optimal policy. A prospective implementation would ideally begin with a predefined acquisition objective and candidate pool, then evaluate whether the chosen score remains informative as new outcomes are collected.

**4.4 From retrospective analysis to experimental scope design — paragraph 89**

> The principal limitations accordingly apply to both components of the framework. For PULSE-Pose, the present analysis assumes a known reactive site and a fixed catalyst reference geometry; substantially flexible catalysts or reactions with competing unknown sites may require catalyst-ensemble sampling, joint catalyst–substrate conformational treatment, or an upstream site-selectivity model. For PULSE-Acquire, the analyses remain retrospective, different acquisition routes can leave different remaining prediction pools, sensitivity to the exact initial measured panel has not been exhaustively characterised, and the preferred policy is not universal across estimators or endpoints. No prospective laboratory loop or cross-reaction validation is reported. These boundaries define the next validation tasks: testing acquisition robustness to different starting scopes, determining whether acquisition rules require system-specific recalibration, evaluating chemically distinct catalyst families, and ultimately measuring whether information-guided substrate selection improves prospective experimental scope construction.

**5 Conclusions — paragraph 91**

> Selected catalyst-referenced descriptors added predictive value for Fe(P7)Cl, while information-guided ordering lowered retrospective learning error in both studied systems. The strongest and most consistent acquisition support was observed for ee; the advantage was neither estimator- nor endpoint-universal. Together, the results support substrate order as an experimental-design variable for learning data-limited catalyst scopes and position catalyst-contextual representation and acquisition as complementary, separately tested components.

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

**S3.1 Leakage controls and protocol separation — paragraph 80**

> The estimator families include Ridge regression [24], Elastic Net [25], LightGBM [26], and Gaussian-process regression [27]. Scikit-learn provides the software framework for the documented conventional estimators and preprocessing [28]. These references establish the methods and software, not the study-specific hyperparameters, selection procedures, or performance; Table S4 records the available fitting settings.

**S4.1 Reveal protocol and acquisition scores — paragraph 119**

> Independent progression begins from a central-plus-diverse two-substrate seed, then reveals one recorded label at a time. The initial seed is held fixed within deterministic route/estimator comparisons. At each prefix, feature processing and model fitting use only revealed labels; predictions and selection quantities are recorded before the next label is exposed. After revealing the selected substrate, the model is refitted and evaluated on the remaining unrevealed pool. These post-refit pool metrics and the pre-reveal selected-substrate error are distinct.

**S4.1 Reveal protocol and acquisition scores — paragraph 120**

> Let U,D,C,P denote the documented uncertainty, molecular-diversity, family-coverage, and predicted-performance score components. The frozen weighted scores are

**S4.1 Reveal protocol and acquisition scores — paragraph 121**

> SUD=0.40U+0.40D+0.20C,

**S4.1 Reveal protocol and acquisition scores — paragraph 122**

> Sperformance=0.50P+0.30U+0.20D.

**S4.1 Reveal protocol and acquisition scores — paragraph 123**

> These weights were specified in the study; literature on active learning and reaction optimisation does not establish them [34,35,36,37]. The reported-order route follows source presentation order, which is not verified as the original chronological experimental order. Diversity-first prioritises Morgan/Tanimoto distance and family coverage. Random routes sample whole substrates without replacement: 500 replicates are reported for Ridge and Tanimoto-kNN, no random Elastic Net summary is included in this comparison.

**S4.1 Reveal protocol and acquisition scores — paragraph 124**

> Two retrospective acquisition experiments are reported. The dedicated matched comparison reproduces archived route-specific progressions and compares mean-prefix MAE at equivalent numbers of revealed labels; “matched” therefore denotes matched label budgets rather than identical initial substrate identities. The independent robustness experiment instead uses the separately documented central-plus-diverse seed protocol, multiple estimators, and trajectory-level AUC-MAE. The two experiments test related but distinct questions and their numerical summaries are not pooled.

**S4.1 Reveal protocol and acquisition scores — paragraph 125**

> The release inventory identifies algorithms/ALGORITHM_SPECIFICATIONS.md and linked source code for the exact U,D,C,P definitions, normalisation, tie-breaking, candidate-set conventions, and random-seed construction. Those details cannot be inferred solely from the weighted equations. In particular, the recorded family-coverage component is not necessarily a binary new-family indicator. The dedicated mean-prefix comparison and independent progression experiment remain separate analyses; Section S5.3 identifies the archived outputs underlying the dedicated result.

**S4.2 Learning metrics and the separate dedicated comparison — paragraph 128**

> For prefix sizes n₁,…,nm, mean-prefix MAE is the arithmetic mean of the corresponding pool errors. The documented independent-trajectory convention is trapezoidal integration,

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

**S5.4 Acquisition and metric definitions — paragraph 170**

> algorithms/ALGORITHM_SPECIFICATIONS.md is the designated specification for uncertainty, diversity, chemical-family coverage, predicted-performance scores, normalisation, nearest-neighbour use, initial-substrate selection, tie-breaking, and error metrics. Section S4 states the documented weights and distinguishes mean-prefix MAE, trapezoidal AUC-MAE, and n₉0. The exact implementation and run-specific settings must be linked to each analysis rather than inferred from these high-level definitions.

**S6 Exploratory hierarchical Bayesian optimisation of substrate-selection weights — paragraph 189**

> This exploratory study examines whether reweighting chemically grouped rule features can improve retrospective substrate selection in the P7 and CMC-Por domains. The search first selects weights within V4, then within V6, and finally a V4/V6 mixing coefficient with both sets of group weights fixed. The methods below describe the supplied implementation; the numerical results are taken from the supplied 66-evaluation aggregate trace rather than a new execution during manuscript preparation.

**S6.1 Feature groups, populations, and retrospective replay — paragraph 193**

> The predictor contract is rdkit_morgan_stage2p, imported from scripts/scope_progression.py. Ridge predictions determine learning error; disagreement between Ridge and Tanimoto-kNN predictions contributes to acquisition. Elastic Net is disabled in this study. Each replay starts with two substrates selected by the existing diversity-first seed procedure, using random.Random(0). Remaining-pool Ridge MAE is evaluated at labelled prefixes from 2 to Nc-1, where Nc is the active population for cell c; one substrate remains unrevealed at the end. At each acquisition step, the highest-scoring whole substrate is selected, ties favour earlier source order, and the recorded outcome is revealed before refitting. Only revealed outcomes enter the within-route model fitting and acquisition calculation; the outer weight search nevertheless uses retrospective prediction errors from the full replay.

**S6.2 Executable acquisition equations — paragraph 198**

> Let Mt denote min–max normalisation across the current candidate pool, returning zero for a constant vector. Model disagreement D is Mt applied to the population standard deviation of the Ridge and Tanimoto-kNN predictions. Coverage Cᵥ averages family coverage and the version-specific rule-coverage score. The executable uncertainty and acquisition terms are

**S6.4 Hierarchical search and recorded budgets — paragraph 214**

> Initial group weights are sampled from a Dirichlet distribution with all concentration parameters equal to one; initial mixing coefficients are uniform on [0,1]. Bayesian proposals use a Gaussian-process surrogate with a Matern kernel (=2.5), an additive white-noise kernel initially set to 10⁻5, and normalised objective values. Group weights are encoded as log ratios to the final component, giving two surrogate coordinates for V4 and four for V6; the mixing stage has one coordinate. The source clips weights at 10⁻8 before normalising and encoding them.

**S6.4 Hierarchical search and recorded budgets — paragraph 215**

> At each Bayesian step, expected improvement for minimising J is evaluated over 2,048 proposals. Of these, approximately 65% perturb one of the eight best observed encoded vectors with Gaussian noise of standard deviation 0.8; the remainder are fresh global draws. The surrogate uses random_state=0, no additional hyperparameter-optimisation restarts, and suppressed convergence warnings. Mixing proposals from local perturbations may fall outside [0,1] and are clipped only after expected-improvement ranking. Duplicate decoded proposals are replaced by random draws but retain the trace label bayesian. Thus, the reported search is a finite proposal procedure, not a guaranteed global or strictly bounded acquisition-function optimum.

**S6.5 Best observed equations and search trace — paragraph 225**

> Bayesian evaluations improved the best initial random objective from 0.137351 to 0.136810 in V4 and from 0.131865 to 0.131367 in the mixing stage. V6's best weights came from random iteration 13; its Bayesian trials did not improve that result. The mixture reduced the composite objective and normalised area relative to selected V6, but had a higher mean-change penalty and the same largest-jump penalty. The result therefore represents a trade-off under the specified objective, not uniform improvement in all measures of stability. A single finite trace also does not establish the superiority of Bayesian optimisation over an equal-budget random-only search.

**S6.6 Interpretation, records, and reproduction limits — paragraph 232**

> The selected equations are retrospective development results. Their weights were chosen using the same domain–endpoint curves on which the objectives are reported; there is no independent outer test of the selected weights. In addition, the supplied code constructs and scales rule-feature matrices over filtered records including the locked audit rows. Although audit outcomes are excluded from route fitting and the objective, fully isolated audit preprocessing cannot be assumed without inspecting the imported feature and coverage routines. No audit-panel or prospective laboratory performance is supplied. An outcome-blind evaluation after freezing the equations is required before claiming general substrate-expansion performance.

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

## Revision analysis and response

The user-confirmed plan is in `analysis_plan.md`; benchmark methods, prediction and optimisation results, and writing/system adjustments are in `results_and_adjustments.md`. A response draft is in `reviewer_response_draft.md`. `results/` retains split-level scores, selection paths and predictions. The analysis shows that QBC has lower average common-test error in both domains; it does not establish state-of-the-art performance of PULSE.
