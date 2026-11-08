# Reviewer 1, comment 2: Acquisition weights

## Reviewer comment

The uncertainty-diversity acquisition weights (0.40/0.40/0.20) are presented as a fixed rule without justification for the specific values. No sensitivity analysis is performed to show how the results change when these weights are varied, nor is there evidence that this particular combination is optimal or even reasonable for the studied systems.

## Highlighted material

The quoted text below is highlighted in yellow in the corresponding document copy. Figure captions identify the adjacent artwork. Table entries reproduce the highlighted cells.

### Manuscript

**3.3 PULSE-Acquire — paragraph 42**

> PULSE-Acquire tests whether substrate selection can improve learning of the remaining scope at matched numbers of known outcomes. The independent robustness progression begins from a fixed central-plus-diverse two-substrate seed. At each step, the known substrates are used to fit the model; unrevealed candidates are scored; one candidate is selected; its recorded outcome is revealed; the model is refitted; and prediction error is evaluated on the remaining unrevealed pool. Only outcomes already revealed at that prefix inform fitting and selection.

**3.3 PULSE-Acquire — paragraph 45**

> Figure 2. PULSE-Acquire workflow. At each iteration, unrevealed substrates are ranked using predictive uncertainty, molecular diversity, and chemical-family coverage; the selected recorded outcome is then revealed and the model is updated. Molecular strings and arrows are schematic rather than a measured acquisition trajectory.

**3.3 PULSE-Acquire — paragraph 46**

> The acquisition functions combine four normalised quantities that describe different properties of each unrevealed candidate. Predictive uncertainty, represented by U, measures the model's limited confidence in the candidate outcome. Molecular diversity, D, rewards candidates that are structurally non-redundant relative to the substrates already revealed, while chemical-family coverage, C, increases the priority of candidates belonging to incompletely represented substrate families. Predicted performance, P, is the model-estimated outcome and is included only in the performance-first comparator. Normalisation places these quantities on comparable scales before their weighted combination. The frozen acquisition scores are

**3.3 PULSE-Acquire — paragraph 47**

> SUD=0.40U+0.40D+0.20C,

**3.3 PULSE-Acquire — paragraph 49**

> Two retrospective acquisition analyses are reported and should be distinguished. The dedicated matched comparison reproduces the archived route-specific progressions and compares mean-prefix MAE at matched numbers of revealed labels. In that comparison, “matched” refers to equivalent label budgets rather than identical initial substrate identities. The independent robustness analysis uses a separately documented progression protocol and evaluates multiple estimators using trajectory-level AUC-MAE. These analyses therefore test related but distinct questions and are not pooled numerically.

**3.3 PULSE-Acquire — paragraph 50**

> Uncertainty–diversity prioritises candidates that are uncertain, molecularly non-redundant, and informative for family coverage. Performance-first instead favours predicted outcome while retaining uncertainty and diversity terms. These routes are compared with source-reported order, diversity-first selection, and whole-substrate random selection. Exact normalisation, tie-breaking, and candidate-set rules are documented in SI Section S4 and the released algorithm specification.

**4.2 Information-guided substrate acquisition — paragraph 74**

> The three components of uncertainty–diversity address different failure modes in sequential scope construction. Predictive uncertainty identifies substrates for which the current model has limited confidence, but uncertainty alone may repeatedly concentrate sampling within a narrow region of chemical space. Molecular diversity discourages such redundancy by favouring candidates that are structurally distinct from the measured set, although structural novelty does not necessarily imply that a substrate will be informative about the response surface.[38] Chemical-family coverage provides a complementary safeguard by preventing recognised substrate classes from remaining systematically underrepresented. The acquisition score therefore balances three distinct questions: where the model is uncertain, where the chemistry is insufficiently sampled, and which regions of the defined scope remain poorly represented. Their combination is intended to avoid overcommitting to any single notion of informativeness.

**4.4 From retrospective analysis to experimental scope design — paragraph 85**

> For PULSE-Acquire, prospective use would require calibration and validation of the acquisition score for each new reaction context. The present uncertainty–diversity policy combines predictive uncertainty, molecular diversity, and chemical-family coverage because these terms address complementary forms of incomplete knowledge in the studied scopes. In a different catalytic system, however, the relevant notion of diversity, the definition of a chemically meaningful family, the reliability of model-derived uncertainty, and the relative importance of these terms may differ. The present 0.40/0.40/0.20 weighting should therefore be regarded as a study-specific acquisition rule rather than a universally optimal policy. A prospective implementation would ideally begin with a predefined acquisition objective and candidate pool, then evaluate whether the chosen score remains informative as new outcomes are collected.

**4.4 From retrospective analysis to experimental scope design — paragraph 89**

> The principal limitations accordingly apply to both components of the framework. For PULSE-Pose, the present analysis assumes a known reactive site and a fixed catalyst reference geometry; substantially flexible catalysts or reactions with competing unknown sites may require catalyst-ensemble sampling, joint catalyst–substrate conformational treatment, or an upstream site-selectivity model. For PULSE-Acquire, the analyses remain retrospective, different acquisition routes can leave different remaining prediction pools, sensitivity to the exact initial measured panel has not been exhaustively characterised, and the preferred policy is not universal across estimators or endpoints. No prospective laboratory loop or cross-reaction validation is reported. These boundaries define the next validation tasks: testing acquisition robustness to different starting scopes, determining whether acquisition rules require system-specific recalibration, evaluating chemically distinct catalyst families, and ultimately measuring whether information-guided substrate selection improves prospective experimental scope construction.

### Supporting information

**S4.1 Reveal protocol and acquisition scores — paragraph 119**

> Independent progression begins from a central-plus-diverse two-substrate seed, then reveals one recorded label at a time. The initial seed is held fixed within deterministic route/estimator comparisons. At each prefix, feature processing and model fitting use only revealed labels; predictions and selection quantities are recorded before the next label is exposed. After revealing the selected substrate, the model is refitted and evaluated on the remaining unrevealed pool. These post-refit pool metrics and the pre-reveal selected-substrate error are distinct.

**S4.1 Reveal protocol and acquisition scores — paragraph 120**

> Let U,D,C,P denote the documented uncertainty, molecular-diversity, family-coverage, and predicted-performance score components. The frozen weighted scores are

**S4.1 Reveal protocol and acquisition scores — paragraph 121**

> SUD=0.40U+0.40D+0.20C,

**S4.1 Reveal protocol and acquisition scores — paragraph 123**

> These weights were specified in the study; literature on active learning and reaction optimisation does not establish them [34,35,36,37]. The reported-order route follows source presentation order, which is not verified as the original chronological experimental order. Diversity-first prioritises Morgan/Tanimoto distance and family coverage. Random routes sample whole substrates without replacement: 500 replicates are reported for Ridge and Tanimoto-kNN, no random Elastic Net summary is included in this comparison.

**S4.1 Reveal protocol and acquisition scores — paragraph 124**

> Two retrospective acquisition experiments are reported. The dedicated matched comparison reproduces archived route-specific progressions and compares mean-prefix MAE at equivalent numbers of revealed labels; “matched” therefore denotes matched label budgets rather than identical initial substrate identities. The independent robustness experiment instead uses the separately documented central-plus-diverse seed protocol, multiple estimators, and trajectory-level AUC-MAE. The two experiments test related but distinct questions and their numerical summaries are not pooled.

**S4.1 Reveal protocol and acquisition scores — paragraph 125**

> The release inventory identifies algorithms/ALGORITHM_SPECIFICATIONS.md and linked source code for the exact U,D,C,P definitions, normalisation, tie-breaking, candidate-set conventions, and random-seed construction. Those details cannot be inferred solely from the weighted equations. In particular, the recorded family-coverage component is not necessarily a binary new-family indicator. The dedicated mean-prefix comparison and independent progression experiment remain separate analyses; Section S5.3 identifies the archived outputs underlying the dedicated result.

**S4.1 Reveal protocol and acquisition scores — paragraph 126**

> The weighted equations specify score arithmetic, not evidence that a particular substrate maximised the score over all eligible candidates. The single-step worked example from the full draft is omitted because it cannot establish that selection claim without the complete contemporaneous candidate-score log. The identified event records retain acquisition sequences; verifying score maximisation additionally requires pre-reveal scores and eligibility/tie decisions for every eligible candidate. This is distinct from recalculating the mean-prefix errors from the archived learning curves (Section S5.3).

**S5.8 Data availability and study boundary — paragraph 187**

> The V4/V6 acquisition-weight study in Section S6 is retained as a separate exploratory development record and is not used as validation of the main-text results.

**S6 Exploratory hierarchical Bayesian optimisation of substrate-selection weights — paragraph 188**

> S6 Exploratory hierarchical Bayesian optimisation of substrate-selection weights

**S6 Exploratory hierarchical Bayesian optimisation of substrate-selection weights — paragraph 189**

> This exploratory study examines whether reweighting chemically grouped rule features can improve retrospective substrate selection in the P7 and CMC-Por domains. The search first selects weights within V4, then within V6, and finally a V4/V6 mixing coefficient with both sets of group weights fixed. The methods below describe the supplied implementation; the numerical results are taken from the supplied 66-evaluation aggregate trace rather than a new execution during manuscript preparation.

**S6.1 Feature groups, populations, and retrospective replay — paragraph 191**

> V4 weights three named rule-feature groups: bde, electronic, and reaction_contrast. V6 additionally weights path_accessibility and local_regime. These are group-level acquisition parameters, not coefficients fitted to individual predictor columns. The supplied study description places each version at roughly 150–200 scalar columns but only tens of active substrates; reducing the search to interpretable groups limits its dimensionality without eliminating overfitting. Exact rule definitions and scaling are delegated to scripts/rule_based_diversity.py; the group names alone do not establish mechanistic or quantum-chemical interpretations.

**S6.1 Feature groups, populations, and retrospective replay — paragraph 192**

> The supplied configuration description specifies the P7 active scope excluding 1ad and the CMC-Por primary aryl scope excluding seven locked audit records (2y, 2z, 4a, 4b, 4c, 4d, and 4e) from route fitting. Each domain is evaluated separately for ee and isolated yield, giving four domain–endpoint cells. Missing outcomes are excluded per endpoint, not replaced by zero. The original configuration and filtered snapshots were not supplied with this trace, so exact population membership and endpoint counts cannot be verified here or substituted from the other SI cohorts.

**S6.1 Feature groups, populations, and retrospective replay — paragraph 193**

> The predictor contract is rdkit_morgan_stage2p, imported from scripts/scope_progression.py. Ridge predictions determine learning error; disagreement between Ridge and Tanimoto-kNN predictions contributes to acquisition. Elastic Net is disabled in this study. Each replay starts with two substrates selected by the existing diversity-first seed procedure, using random.Random(0). Remaining-pool Ridge MAE is evaluated at labelled prefixes from 2 to Nc-1, where Nc is the active population for cell c; one substrate remains unrevealed at the end. At each acquisition step, the highest-scoring whole substrate is selected, ties favour earlier source order, and the recorded outcome is revealed before refitting. Only revealed outcomes enter the within-route model fitting and acquisition calculation; the outer weight search nevertheless uses retrospective prediction errors from the full replay.

**S6.2 Executable acquisition equations — paragraph 194**

> S6.2 Executable acquisition equations

**S6.2 Executable acquisition equations — paragraph 195**

> For candidate i, revealed set L, and group g containing pg scaled features zᵢgk, group novelty is the nearest revealed-substrate distance within that group:

**S6.2 Executable acquisition equations — paragraph 196**

> dg(i| L)=j∈ L(1)/(pg)∑k=1pg|zᵢgk-zjgk|, Nᵥ(i| L)=∑g∈ Gᵥwᵥgdg(i| L),

**S6.2 Executable acquisition equations — paragraph 197**

> where v∈4,6, wᵥg≥0, and ∑g wᵥg=1. The nearest neighbour is determined separately within each group, before summing weighted distances.

**S6.2 Executable acquisition equations — paragraph 198**

> Let Mt denote min–max normalisation across the current candidate pool, returning zero for a constant vector. Model disagreement D is Mt applied to the population standard deviation of the Ridge and Tanimoto-kNN predictions. Coverage Cᵥ averages family coverage and the version-specific rule-coverage score. The executable uncertainty and acquisition terms are

**S6.2 Executable acquisition equations — paragraph 199**

> Uᵥ = 0.5Mt(Nᵥ)+0.5D,

**S6.2 Executable acquisition equations — paragraph 200**

> Aᵥ = 0.4Nᵥ+0.4Uᵥ+0.2Cᵥ

**S6.2 Executable acquisition equations — paragraph 201**

> = 0.4Nᵥ+0.2Mt(Nᵥ)+0.2D+0.2Cᵥ.

**S6.2 Executable acquisition equations — paragraph 202**

> Only the group weights in novelty are searched within each version; the outer coefficients are fixed at their supplied default values. With the selected V4 and V6 equations fixed, the final stage searches 0≤λ≤1 in

**S6.2 Executable acquisition equations — paragraph 203**

> Amix=λ A₄+(1-λ)A₆.

**S6.2 Executable acquisition equations — paragraph 204**

> The supplied overview and equation-export strings omit Mt from the novelty contribution to uncertainty. Equations S8 and S9 instead follow the executable calculation. Although mixed novelty has group weights λ w₄g+(1-λ)w₆g, the full score also retains separate normalisation and version-specific coverage. It cannot generally be replaced by the exported shorthand 0.6Nmix+0.2D+0.2C. The supplied source is retained unchanged so this distinction remains auditable.

**S6.4 Hierarchical search and recorded budgets — paragraph 214**

> Initial group weights are sampled from a Dirichlet distribution with all concentration parameters equal to one; initial mixing coefficients are uniform on [0,1]. Bayesian proposals use a Gaussian-process surrogate with a Matern kernel (=2.5), an additive white-noise kernel initially set to 10⁻5, and normalised objective values. Group weights are encoded as log ratios to the final component, giving two surrogate coordinates for V4 and four for V6; the mixing stage has one coordinate. The source clips weights at 10⁻8 before normalising and encoding them.

**S6.4 Hierarchical search and recorded budgets — paragraph 215**

> At each Bayesian step, expected improvement for minimising J is evaluated over 2,048 proposals. Of these, approximately 65% perturb one of the eight best observed encoded vectors with Gaussian noise of standard deviation 0.8; the remainder are fresh global draws. The surrogate uses random_state=0, no additional hyperparameter-optimisation restarts, and suppressed convergence warnings. Mixing proposals from local perturbations may fall outside [0,1] and are clipped only after expected-improvement ranking. Duplicate decoded proposals are replaced by random draws but retain the trace label bayesian. Thus, the reported search is a finite proposal procedure, not a guaranteed global or strictly bounded acquisition-function optimum.

**S6.4 Hierarchical search and recorded budgets — paragraph 216**

> The supplied/default search seed is 20260914; the initial replay selector and Gaussian process separately use zero as described above. The aggregate trace has no seed field or accompanying original manifest. Table S13 therefore distinguishes the observed counts from the larger supplied defaults rather than claiming an independently verified original command.

**S6.5 Best observed equations and search trace — paragraph 220**

> Across the 66 supplied evaluations, the best observed objectives were 0.136810 for V4, 0.133336 for V6, and 0.131367 for the mixture (Table S14). The selected mixing coefficient was λ=0.3530403716, giving V4 and V6 score contributions of approximately 35.3% and 64.7%, respectively. Table S15 records the selected group weights and the corresponding mixed-novelty weights; Section S6.7 gives every evaluated parameter vector and objective component at the supplied numerical precision, including the selected observations, directly in this SI.

**S6.5 Best observed equations and search trace — paragraph 221**

> Table S14. Best observations in the supplied trace. Iterations are zero-based within each method. B̅, F̅ and H̅ average the components over the four cells.

**S6.5 Best observed equations and search trace — paragraph 223**

> Table S15. Selected group weights, rounded to six decimal places. Zeros denote groups absent from V4. The final column combines novelty weights only, not the complete acquisition equation.

**S6.5 Best observed equations and search trace — paragraph 225**

> Bayesian evaluations improved the best initial random objective from 0.137351 to 0.136810 in V4 and from 0.131865 to 0.131367 in the mixing stage. V6's best weights came from random iteration 13; its Bayesian trials did not improve that result. The mixture reduced the composite objective and normalised area relative to selected V6, but had a higher mean-change penalty and the same largest-jump penalty. The result therefore represents a trade-off under the specified objective, not uniform improvement in all measures of stability. A single finite trace also does not establish the superiority of Bayesian optimisation over an equal-budget random-only search.

**S6.5 Best observed equations and search trace — paragraph 227**

> Figure S7. Hierarchical acquisition-weight search, rendered from the supplied aggregate trace. Points show individual objective evaluations; the black line shows the best value observed so far within each stage. Dashed lines separate random initialisation from Bayesian-labelled evaluations. The horizontal axis is search-evaluation order, not substrate label budget, and these are not learning curves.

**S6.6 Interpretation, records, and reproduction limits — paragraph 232**

> The selected equations are retrospective development results. Their weights were chosen using the same domain–endpoint curves on which the objectives are reported; there is no independent outer test of the selected weights. In addition, the supplied code constructs and scales rule-feature matrices over filtered records including the locked audit rows. Although audit outcomes are excluded from route fitting and the objective, fully isolated audit preprocessing cannot be assumed without inspecting the imported feature and coverage routines. No audit-panel or prospective laboratory performance is supplied. An outcome-blind evaluation after freezing the equations is required before claiming general substrate-expansion performance.

**S6.6 Interpretation, records, and reproduction limits — paragraph 234**

> The implementation is designed to write filtered input snapshots, stage-specific search records, per-cell objectives, selected mixed-route learning curves and substrate sequences, equation exports, and a provenance manifest. Those original outputs, the configuration, and the two imported project modules were not supplied with the aggregate trace. Their absence prevents a complete replay or verification that the supplied source generated this trace. In particular, full prefix-level curves and selected routes cannot be reconstructed from aggregate objective rows alone. Figure S7 is derived solely from the supplied aggregate numerical trace.

**S6.6 Interpretation, records, and reproduction limits — paragraph 235**

> The recorded random/Bayesian evaluation counts are 12/8 for V4, 16/10 for V6, and 12/8 for the mixture. The supplied/default seed is 20260914, but the original run seed is not independently documented. These settings alone do not provide an exact-regeneration recipe without the missing configuration, modules, inputs, and compatible software environment.

**Table 14 in document order — Table S13. Recorded search budgets versus supplied defaults. Counts are random plus Bayesian objective evaluations, not laboratory experiments.**

- Stage | Recorded random | Recorded Bayesian | Default random + Bayesian
- V4 | 12 | 8 | 24 + 16
- V6 | 16 | 10 | 32 + 20
- V4/V6 mixture | 12 | 8 | 24 + 16
- Total | 40 | 26 | 80 + 52

**Table 15 in document order — Table S14. Best observations in the supplied trace. Iterations are zero-based within each method. B̅, F̅ and H̅ average the components over the four cells.**

- Stage | Selected observation | J | B̅ | F̅ | H̅
- V4 | Bayesian 2 | 0.136810 | 0.146871 | 0.139084 | 0.092775
- V6 | Random 13 | 0.133336 | 0.150387 | 0.121231 | 0.085310
- Mixture | Bayesian 7 | 0.131367 | 0.141656 | 0.134309 | 0.085310

**Table 16 in document order — Table S15. Selected group weights, rounded to six decimal places. Zeros denote groups absent from V4. The final column combines novelty weights only, not the complete acquisition equation.**

- Rule-feature group | V4 | V6 | Mixed novelty
- BDE rule | 0.451395 | 0.070945 | 0.205259
- Electronic | 0.094759 | 0.102770 | 0.099942
- Reaction contrast | 0.453847 | 0.248608 | 0.321065
- Path accessibility | 0.000000 | 0.371888 | 0.240596
- Local regime | 0.000000 | 0.205790 | 0.133138

## R1.2 sensitivity work completed

The revision-local 21-point simplex analysis and its findings are in `experiment_plan.md`, `weight_sensitivity_results.md`, `results/weight_sensitivity/`, and `validation_report.md`. The operational code definition is `U=0.5D+0.5Q`, so the written default `0.4U+0.4D+0.2C` expands to `0.6D+0.2Q+0.2C`. The default ranked 11th/21 in Fe(P7)Cl and tied 10th–11th/21 in Fe(CMC-Por)Cl. It was not the lowest-error setting in either domain; observed grid minima were only 0.53 and 0.66 ee points lower, respectively. No replacement weights were selected.

The source data show 26 active CMC-Por aryl records; the seven locked late-stage audit records are a separate cohort. One initial CMC command stopped before analysis at a mistaken assertion about the count. The plan was corrected before the successful CMC run. The P7 calculations were unaffected by that CMC-only assertion correction.

The cumulative R1.2 DOCX copies are `Manuscript_weight_sensitivity_revised.docx` and `Supporting_Information_weight_sensitivity_revised.docx`. They carry forward the R1.1 edits and highlight new R1.2 changes. No production acquisition code or original archived files were modified.

## Follow-up and closeout

The common-test baseline comparisons, full grid results, and limitation on reconstructing remaining-pool mean-prefix MAE are recorded in `weight_sensitivity_results.md`. The cumulative highlighted documents are `Manuscript_comment2_closed.docx` and `Supporting_Information_comment2_closed.docx`. The comment is closed for this revision with the limitations in `editorial_closeout.md`.
