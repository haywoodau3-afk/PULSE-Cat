# Reviewer 1, comment 6: Yield endpoint

## Reviewer comment

The yield endpoint shows inconsistent and sometimes worse performance under uncertainty-diversity compared to reported order or random selection. The manuscript attributes this to endpoint dependence, but does not explore why the acquisition strategy fails for yield. Without a mechanistic explanation, the claim that uncertainty-diversity is broadly useful for learning catalyst behaviour is weakened.

## Highlighted material

The quoted text below is highlighted in yellow in the corresponding document copy. Figure captions identify the adjacent artwork. Table entries reproduce the highlighted cells.

### Manuscript

**2.3 Endpoints and curation — paragraph 27**

> The principal selectivity endpoint is the magnitude of reported enantiomeric excess; signed stereochemical direction is not modelled. Because the target is |ee|, the present models predict the strength of stereochemical discrimination rather than its direction. Substrates giving equal-magnitude but opposite enantiomeric preferences are therefore equivalent under this target, and prospective prediction of absolute stereochemical preference would constitute a distinct modelling problem. Isolated yield is analysed separately rather than combined with ee into a composite outcome. Missing ee is not interpreted as zero and is not replaced by yield. Conversely, an experimentally measured zero-ee result remains a valid observation. Missing or unreported outcomes are retained as missing and are not assigned failure labels. The curation specification also preserves starting-material azide SMILES, free-nitrene structures used for pose construction, product SMILES when reported, reactive-site atom maps, family and scaffold groups, exclusions, source order, and provenance. Full row-level definitions and reconciliation of the analysis-specific populations are provided in SI Section S1.

**3.2 Model fitting and validation — paragraph 40**

> Elastic Net is used for the principal representation comparison, Ridge for the dedicated matched acquisition comparison, and Elastic Net, Ridge, and Tanimoto-kNN for the independent acquisition robustness analyses.[34,35] Representation prediction is summarised by MAE, RMSE, and R². Progressive learning is evaluated using mean-prefix MAE for the dedicated matched comparison and trapezoidal AUC-MAE for the independent trajectories. Hyperparameter grids and implementation settings remain in the SI.

**3.3 PULSE-Acquire — paragraph 50**

> Uncertainty–diversity prioritises candidates that are uncertain, molecularly non-redundant, and informative for family coverage. Performance-first instead favours predicted outcome while retaining uncertainty and diversity terms. These routes are compared with source-reported order, diversity-first selection, and whole-substrate random selection. Exact normalisation, tie-breaking, and candidate-set rules are documented in SI Section S4 and the released algorithm specification.

**4.2 Information-guided substrate acquisition — paragraph 65**

> The dedicated matched Ridge comparison measures learning by mean-prefix ee MAE. Uncertainty–diversity reduced this error from 21.672 to 9.684 for Fe(P7)Cl and from 13.155 to 8.787 for the Fe(CMC-Por)Cl aryl population relative to reported order, corresponding to 55.3% and 33.2% reductions (Table 2). It also outperformed diversity-first, random, and performance-first selection in both matched comparisons.

**4.2 Information-guided substrate acquisition — paragraph 69**

> An independent robustness analysis used a fixed molecular-plus-pose representation and three estimators. Uncertainty–diversity gave the lowest ee AUC-MAE for Elastic Net, Ridge, and Tanimoto-kNN in Fe(P7)Cl, and for Elastic Net and Ridge in Fe(CMC-Por)Cl. Diversity-first was slightly better for Fe(CMC-Por)Cl Tanimoto-kNN (171.515 versus 175.443 AUC-MAE). The result is therefore robust across several estimator/domain combinations but is not universal (Table 3 and Fig. 5).

**4.2 Information-guided substrate acquisition — paragraph 70**

> Table 3. Acquisition route giving the lowest independent ee AUC-MAE among the evaluated routes for each catalyst-domain and estimator combination. Not every estimator was evaluated under every stochastic comparison route; complete evaluated combinations are given in SI Tables S9–S12.

**4.2 Information-guided substrate acquisition — paragraph 75**

> Yield showed a less consistent acquisition response. In Fe(CMC-Por)Cl, uncertainty–diversity produced slightly higher integrated yield error than reported order for Elastic Net and Ridge, whereas Tanimoto-kNN showed the opposite trend. Fe(P7)Cl likewise exhibited estimator-dependent yield behaviour. Thus, the acquisition advantage observed most consistently for enantiomeric excess does not generalise uniformly to isolated yield, reinforcing that acquisition performance depends on both the endpoint and estimator.

**4.2 Information-guided substrate acquisition — paragraph 76**

> This endpoint dependence is chemically plausible without establishing a specific mechanism. Ee describes competition between stereochemical outcomes, whereas isolated yield aggregates productive conversion, competing or unproductive pathways, and practical isolation. The same representation and acquisition objective therefore need not be optimal for both quantities. Accordingly, there may be no universally informative next substrate independent of the property being learned. A substrate that most reduces uncertainty in stereochemical discrimination may not be the substrate that most improves prediction of reaction efficiency. Prospective implementations should therefore define the primary endpoint before acquisition or use an explicitly multi-objective acquisition function when several properties are important.

**4.2 Information-guided substrate acquisition — paragraph 77**

> Performance-first and information-first selection address complementary experimental objectives. Performance-first selection prioritises substrates that the current model expects to give favourable outcomes, making it appropriate when the immediate aim is to identify synthetically useful chemistry. Information-first selection prioritises measurements expected to reduce uncertainty about catalyst behaviour across the wider scope. A predicted high-performing substrate can be valuable for establishing practical utility, whereas an uncertain or structurally distinct substrate can be valuable for refining the learned response surface. This distinction separates optimisation, which asks where the reaction is expected to perform best, from characterisation, which asks where and how catalyst behaviour changes across chemical space. The lower retrospective learning error observed for uncertainty–diversity relative to performance-first selection is therefore consistent with its information-oriented objective.

**4.4 From retrospective analysis to experimental scope design — paragraph 86**

> This distinction is especially important because acquisition performance depends on the scientific objective. The present results most consistently support uncertainty–diversity ordering for learning enantiomeric excess, whereas yield shows stronger estimator dependence. An informative next substrate is therefore not necessarily an intrinsic property of the molecule: it depends on what aspect of catalyst behaviour is being learned. A substrate that resolves uncertainty in stereochemical discrimination may not be the substrate that best improves prediction of reaction efficiency. Future implementations could consequently use endpoint-specific acquisition policies or, when several experimental goals are important, an explicitly multi-objective score that balances information about selectivity, yield, or other properties. Such extensions remain prospective and are not tested here.

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

**S1 Study scope, datasets, and analysis populations — paragraph 8**

> All analyses are retrospective. Experimental outcomes originate from the two cited literature datasets, whereas computational poses are molecular representations rather than additional measured substrates. The selectivity target is unsigned enantiomeric excess (ee), reported in percent; MAE and RMSE are therefore expressed in ee percentage points. Yield is analysed separately. Missing labels, measured zero-ee outcomes, and protocol-specific analysis populations remain distinct.

**S1.1.1 Reaction sources and curation — paragraph 13**

> The experimental domains are Fe(P7)Cl and Fe(CMC-Por)Cl intramolecular C(sp3)–H amination, as reported independently by Lee and co-workers and Wang and co-workers, respectively [1,2]. The curation specification records reaction and substrate identifiers, catalyst and condition identifiers, starting-material azide SMILES, free-nitrene SMILES, product SMILES when reported, reactive-site atom maps, experimental ee/yield, family and scaffold groups, exclusions, source order, and provenance. Missing product structures remain null rather than being computationally reconstructed. Missing ee is not zero and is not replaced by yield. A measured zero-ee outcome remains a valid observation; an unreported reaction is not assigned a failure label.

**S1.1.1 Reaction sources and curation — paragraph 17**

> The independent progression summaries end at 37 revealed Fe(P7)Cl ee labels, 38 yield labels, and 25 Fe(CMC-Por)Cl aryl labels, leaving a route-dependent residual pool. These progression endpoints must not be substituted for the 38-substrate development cohort. Removing only 1ad from 41 records cannot explain a 39-record progression set. The release inventory identifies dataset-id-lists.csv as the explicit reconciliation; its population memberships and exclusion reasons must be used when reproducing each analysis.

**S4.1 Reveal protocol and acquisition scores — paragraph 119**

> Independent progression begins from a central-plus-diverse two-substrate seed, then reveals one recorded label at a time. The initial seed is held fixed within deterministic route/estimator comparisons. At each prefix, feature processing and model fitting use only revealed labels; predictions and selection quantities are recorded before the next label is exposed. After revealing the selected substrate, the model is refitted and evaluated on the remaining unrevealed pool. These post-refit pool metrics and the pre-reveal selected-substrate error are distinct.

**S4.1 Reveal protocol and acquisition scores — paragraph 124**

> Two retrospective acquisition experiments are reported. The dedicated matched comparison reproduces archived route-specific progressions and compares mean-prefix MAE at equivalent numbers of revealed labels; “matched” therefore denotes matched label budgets rather than identical initial substrate identities. The independent robustness experiment instead uses the separately documented central-plus-diverse seed protocol, multiple estimators, and trajectory-level AUC-MAE. The two experiments test related but distinct questions and their numerical summaries are not pooled.

**S4.3 Complete independent-progression summaries — paragraph 136**

> Tables S9–S12 present all 56 documented independent route/estimator rows. The representation is fixed at rdkit_morgan_stage2p: 15 RDKit descriptors, 1,024 Morgan bits, and 248 Stage 2p fields (1,287 columns, P2 composition). This does not imply that Tanimoto-kNN uses non-fingerprint columns. Its matrix and settings must not be substituted for the separate dedicated comparison.

**S4.3 Complete independent-progression summaries — paragraph 137**

> Route codes D, H, P, R, and U mean diversity-first, reported order, performance-first, random, and uncertainty–diversity. Model codes EN, R, and K mean Elastic Net, Ridge, and Tanimoto-kNN. NA means the threshold was not reached. Final n is the number of revealed labels, not the number of test predictions. The reference MAE and Δ (final minus reference) are documented summary values; discrepancies of 0.001 from subtraction of rounded MAEs are retained. Final-prefix MAEs concern route-dependent remaining substrates and cannot establish superiority on a common test set.

**S4.3 Complete independent-progression summaries — paragraph 140**

> Table S10. Fe(P7)Cl isolated yield: independent-progression summaries.

**S4.3 Complete independent-progression summaries — paragraph 144**

> Table S12. Fe(CMC-Por)Cl isolated yield: independent-progression summaries.

**S4.3 Complete independent-progression summaries — paragraph 146**

> Uncertainty–diversity minimises ee AUC-MAE for all three Fe(P7)Cl estimators and for Fe(CMC-Por)Cl Elastic Net/Ridge, but diversity-first gives lower Fe(CMC-Por)Cl Tanimoto-kNN AUC (171.515 versus 175.443). The latter estimator also reaches n₉0 earlier under reported order than under uncertainty–diversity (7 versus 14 labels). Thus threshold convergence and integrated error can disagree.

**S4.3 Complete independent-progression summaries — paragraph 147**

> Yield was evaluated as a separate secondary endpoint rather than as part of a composite acquisition objective. For Fe(CMC-Por)Cl, the reported-order and uncertainty–diversity AUC-MAE values were 457.616/467.958 for Elastic Net, 474.511/479.375 for Ridge, and 398.990/368.317 for Tanimoto-kNN, respectively (Figure S5). Thus, uncertainty–diversity gave marginally higher integrated errors with Elastic Net and Ridge but a lower error with Tanimoto-kNN. Fe(P7)Cl yield performance was likewise estimator-dependent. Table S12 reports the final-prefix values for completeness; because these values derive from route-dependent residual pools, they are not interpreted as common-test-set comparisons. Collectively, these analyses qualify the ee findings by demonstrating that acquisition performance depends on both the endpoint and estimator. The retrospective records do not include unreported failures or fully reconstruct the historical sequence of experimental decisions.

**S4.3 Complete independent-progression summaries — paragraph 149**

> Figure S5. Endpoint-dependent acquisition behaviour for Fe(CMC-Por)Cl. Integrated yield AUC-MAE is shown for reported-order and uncertainty–diversity (U–D) trajectories using Elastic Net (EN), Ridge, and Tanimoto-kNN; lower values indicate lower integrated error. Unlike the more consistent ee results, yield performance is estimator-dependent.

**S4.3 Complete independent-progression summaries — paragraph 152**

> Figure S6. Independent acquisition analyses, retained as corroboration rather than the source of the main-text 55.3% and 33.2% reductions. (A) Fe(P7)Cl Ridge ee-learning trajectories. The displayed legend uses “reported_order” for the source record's “historical_order”; only the legend wording has changed, not the curves or data. Reported order is not verified laboratory chronology. Random curves show the mean and 25th/75th percentiles. (B) Reported-order versus uncertainty–diversity integrated ee error for three estimators in each catalyst domain. These trapezoidal AUC-MAE results are distinct from the dedicated mean-prefix comparison in Table S8 and the main-text matched-acquisition table. Panel B does not display every competing route; Tables S9–S12 give complete comparisons, including the Fe(CMC-Por)Cl Tanimoto-kNN exception.

**S6.1 Feature groups, populations, and retrospective replay — paragraph 192**

> The supplied configuration description specifies the P7 active scope excluding 1ad and the CMC-Por primary aryl scope excluding seven locked audit records (2y, 2z, 4a, 4b, 4c, 4d, and 4e) from route fitting. Each domain is evaluated separately for ee and isolated yield, giving four domain–endpoint cells. Missing outcomes are excluded per endpoint, not replaced by zero. The original configuration and filtered snapshots were not supplied with this trace, so exact population membership and endpoint counts cannot be verified here or substituted from the other SI cohorts.

**Table 11 in document order — Table S10. Fe(P7)Cl isolated yield: independent-progression summaries.**

- Route | Model | Final n | Final MAE | AUC-MAE | n₉0 | Ref. MAE | Δ
- D | EN | 38 | 15.999 | 561.248 | 2 | 14.742 | 1.258
- D | R | 38 | 16.006 | 570.357 | 2 | 14.742 | 1.265
- D | K | 38 | 0.509 | 469.261 | 12 | 14.742 | -14.232
- H | EN | 38 | 22.180 | 908.899 | 2 | 14.742 | 7.438
- H | R | 38 | 23.917 | 913.166 | 2 | 14.742 | 9.176
- H | K | 38 | 16.019 | 633.651 | 37 | 14.742 | 1.278
- P | EN | 38 | 15.999 | 657.697 | 2 | 14.742 | 1.258
- P | R | 38 | 16.006 | 666.479 | 2 | 14.742 | 1.265
- P | K | 38 | 0.509 | 513.326 | 15 | 14.742 | -14.232
- R | R | 38 | 18.447 | 639.424 | 4 | 14.742 | 3.705
- R | K | 38 | 13.461 | 484.752 | 26 | 14.742 | -1.281
- U | EN | 38 | 15.999 | 547.182 | 2 | 14.742 | 1.258
- U | R | 38 | 16.007 | 554.164 | 2 | 14.742 | 1.265
- U | K | 38 | 0.509 | 452.942 | 15 | 14.742 | -14.232

**Table 13 in document order — Table S12. Fe(CMC-Por)Cl isolated yield: independent-progression summaries.**

- Route | Model | Final n | Final MAE | AUC-MAE | n₉0 | Ref. MAE | Δ
- D | EN | 25 | 35.582 | 453.058 | 6 | 15.000 | 20.582
- D | R | 25 | 35.032 | 467.224 | 6 | 15.000 | 20.032
- D | K | 25 | 26.904 | 354.284 | 2 | 15.000 | 11.904
- H | EN | 25 | 8.173 | 457.616 | 6 | 15.000 | -6.827
- H | R | 25 | 10.244 | 474.511 | 6 | 15.000 | -4.756
- H | K | 25 | 3.045 | 398.990 | 4 | 15.000 | -11.955
- P | EN | 25 | 8.173 | 613.981 | 9 | 15.000 | -6.827
- P | R | 25 | 10.244 | 616.732 | 9 | 15.000 | -4.756
- P | K | 25 | 6.276 | 312.254 | 2 | 15.000 | -8.724
- R | R | 25 | 21.604 | 518.475 | 24 | 15.000 | 6.604
- R | K | 25 | 18.131 | 390.508 | 2 | 15.000 | 3.131
- U | EN | 25 | 35.582 | 467.958 | 6 | 15.000 | 20.582
- U | R | 25 | 35.032 | 479.375 | 6 | 15.000 | 20.032
- U | K | 25 | 26.904 | 368.317 | 2 | 15.000 | 11.904

## Revision analysis and response

The user-confirmed plan is recorded in `analysis_plan.md`; new common-test yield and paired ee findings, score diagnostics, validation and writing adjustments are recorded in `results_and_adjustments.md`. A point-by-point response is in `reviewer_response_draft.md`; full predictions, selections, seeds, inputs and validation are under `results/` and `validation_report.txt`. The analysis does not identify a chemical mechanism or support a universal yield advantage.
