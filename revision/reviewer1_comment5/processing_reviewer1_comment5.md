# Reviewer 1, comment 5: Aryl and sulfonyl populations

## Reviewer comment

For the Fe(CMC-Por)Cl system, only aryl substrates are used in the acquisition analysis; sulfonyl substrates are excluded. Since the original study includes both classes with different reactivities, excluding half the dataset may bias the learning problem and limit the generality of the conclusions for this catalyst.

## Highlighted material

The quoted text below is highlighted in yellow in the corresponding document copy. Figure captions identify the adjacent artwork. Table entries reproduce the highlighted cells.

### Manuscript

**2.1 Catalytic chemistry — paragraph 18**

> The experimental basis comprises two independently published iron-porphyrin scopes. Lee and co-workers reported Fe(P7)Cl-catalysed asymmetric C–H amination, while Wang and co-workers reported visible-light-driven Fe(CMC-Por)Cl catalysis.[19,20] In both systems, a tethered organic azide undergoes intramolecular C(sp3)–H amination with loss of dinitrogen to form an enantioenriched N-heterocyclic product. The source studies report enantiomeric excess and isolated yield. Curated records retain starting-azide identity, product identity where reported, the experimentally assigned reactive site, measured outcomes, chemical-family labels, source order, and literature provenance. Thus, the chemistry considered here is a specific scope-learning problem for intramolecular nitrene transfer, rather than a general dataset of iron-catalysed C–H functionalisation.

**2.1 Catalytic chemistry — paragraph 19**

> The principal literature conditions also distinguish the two domains. The Fe(P7)Cl scope used 2 mol% catalyst in diethyl ether at 60 °C for 18 h with 4 Å molecular sieves, with selected less reactive substrates examined at 80 or 100 °C.[19] The principal aryl-azide protocol for Fe(CMC-Por)Cl used 2 mol% catalyst and di-tert-butyl dicarbonate in toluene under 410 nm irradiation at -10 °C.[20] That study includes both aryl azides forming indolines and arylsulfonyl azides forming cyclic sulfonamides, with substrate-class-specific protocol differences. These conditions describe the source datasets; no literature reactions were repeated in the present study. The transformation and catalyst structures are summarised in Fig. 1.

**2.1 Catalytic chemistry — paragraph 21**

> Figure 1. Catalytic systems and transformation studied. The scheme summarises the reported intramolecular C(sp3)–H amination of tethered azides and the two independently reported iron-porphyrin catalysts; substrate-specific structures and conditions remain documented in the source studies and SI.

**2.2 Dataset populations — paragraph 23**

> The numerical populations used for curation, representation development, progression, and cross-catalyst visualisation are distinct (Table 1). The retained ledgers contain 41 Fe(P7)Cl and 50 Fe(CMC-Por)Cl records; the latter comprise 33 aryl substrates and 17 sulfonyl controls. The principal PULSE-Pose development comparison uses 38 Fe(P7)Cl substrates from 17 families. Independent Fe(CMC-Por)Cl progression uses 26 active aryl labels per endpoint rather than the complete retained ledger, and the exact remaining pool depends on the reveal route. Only 13 exact canonical aryl identities are shared between catalyst domains and eligible for paired geometry comparison. These counts describe different analysis inputs and must not be treated as interchangeable versions of one dataset.

**2.2 Dataset populations — paragraph 24**

> Table 1. Analysis populations used in the main comparisons. Counts describe distinct inputs rather than successive filters of a single common cohort.

**2.3 Endpoints and curation — paragraph 27**

> The principal selectivity endpoint is the magnitude of reported enantiomeric excess; signed stereochemical direction is not modelled. Because the target is |ee|, the present models predict the strength of stereochemical discrimination rather than its direction. Substrates giving equal-magnitude but opposite enantiomeric preferences are therefore equivalent under this target, and prospective prediction of absolute stereochemical preference would constitute a distinct modelling problem. Isolated yield is analysed separately rather than combined with ee into a composite outcome. Missing ee is not interpreted as zero and is not replaced by yield. Conversely, an experimentally measured zero-ee result remains a valid observation. Missing or unreported outcomes are retained as missing and are not assigned failure labels. The curation specification also preserves starting-material azide SMILES, free-nitrene structures used for pose construction, product SMILES when reported, reactive-site atom maps, family and scaffold groups, exclusions, source order, and provenance. Full row-level definitions and reconciliation of the analysis-specific populations are provided in SI Section S1.

**2.4 Study boundary — paragraph 29**

> This work is a retrospective analysis of two published reaction scopes. Computational poses are representations of measured substrate records and do not constitute additional experiments: the 41 and 50 retained records generate many geometries, but the statistical observations remain the measured substrates. The study does not attempt prospective reaction-site discovery, prospective laboratory acquisition, or validation across unrelated catalytic families. It instead tests representation and reveal-order questions within two related iron-porphyrin systems for which outcomes and reactive-site assignments are already available.

**4.2 Information-guided substrate acquisition — paragraph 65**

> The dedicated matched Ridge comparison measures learning by mean-prefix ee MAE. Uncertainty–diversity reduced this error from 21.672 to 9.684 for Fe(P7)Cl and from 13.155 to 8.787 for the Fe(CMC-Por)Cl aryl population relative to reported order, corresponding to 55.3% and 33.2% reductions (Table 2). It also outperformed diversity-first, random, and performance-first selection in both matched comparisons.

**4.2 Information-guided substrate acquisition — paragraph 67**

> Table 2. Central matched acquisition comparison: mean-prefix ee MAE (ee percentage points) using Ridge. Lower values indicate more accurate learning at the evaluated label budgets; the Fe(CMC-Por)Cl population is aryl-only.

**4.2 Information-guided substrate acquisition — paragraph 69**

> An independent robustness analysis used a fixed molecular-plus-pose representation and three estimators. Uncertainty–diversity gave the lowest ee AUC-MAE for Elastic Net, Ridge, and Tanimoto-kNN in Fe(P7)Cl, and for Elastic Net and Ridge in Fe(CMC-Por)Cl. Diversity-first was slightly better for Fe(CMC-Por)Cl Tanimoto-kNN (171.515 versus 175.443 AUC-MAE). The result is therefore robust across several estimator/domain combinations but is not universal (Table 3 and Fig. 5).

**4.4 From retrospective analysis to experimental scope design — paragraph 87**

> The experimental-design question is not intrinsically specific to iron porphyrins, but the present empirical validation is. Using two related but independently reported catalyst systems provides an intermediate validation level: the acquisition principle can be examined across distinct catalyst environments and substrate scopes without implying transfer across fundamentally different reaction classes. The results show that informative ordering can alter retrospective learning trajectories in both studied systems, but they do not establish that the same acquisition weights, candidate definitions, or magnitude of improvement will persist elsewhere. In particular, the observed advantage may depend on the initial measured panel, the estimator used to quantify uncertainty, the endpoint being learned, and the composition of the available candidate pool.

**4.4 From retrospective analysis to experimental scope design — paragraph 89**

> The principal limitations accordingly apply to both components of the framework. For PULSE-Pose, the present analysis assumes a known reactive site and a fixed catalyst reference geometry; substantially flexible catalysts or reactions with competing unknown sites may require catalyst-ensemble sampling, joint catalyst–substrate conformational treatment, or an upstream site-selectivity model. For PULSE-Acquire, the analyses remain retrospective, different acquisition routes can leave different remaining prediction pools, sensitivity to the exact initial measured panel has not been exhaustively characterised, and the preferred policy is not universal across estimators or endpoints. No prospective laboratory loop or cross-reaction validation is reported. These boundaries define the next validation tasks: testing acquisition robustness to different starting scopes, determining whether acquisition rules require system-specific recalibration, evaluating chemically distinct catalyst families, and ultimately measuring whether information-guided substrate selection improves prospective experimental scope construction.

**Table 1 in document order — Table 1. Analysis populations used in the main comparisons. Counts describe distinct inputs rather than successive filters of a single common cohort.**

- Population | Count | Primary purpose
- Fe(P7)Cl retained records | 41 | Curated substrate ledger, including a measured zero-ee record
- Fe(P7)Cl matched ee development | 38 / 17 families | PULSE-Pose prediction and matched validation
- Fe(CMC-Por)Cl retained records | 50 | Curated ledger: 33 aryl and 17 sulfonyl records
- Fe(CMC-Por)Cl aryl progression subset | 26 active labels per endpoint | Analysis-specific PULSE-Acquire progression
- Shared canonical aryl identities | 13 | Cross-catalyst geometry comparison

**Table 2 in document order — Table 2. Central matched acquisition comparison: mean-prefix ee MAE (ee percentage points) using Ridge. Lower values indicate more accurate learning at the evaluated label budgets; the Fe(CMC-Por)Cl population is aryl-only.**

- Acquisition route | Fe(P7)Cl | Fe(CMC-Por)Cl
- Reported order | 21.672 | 13.155
- Diversity-first | 11.197 | 9.842
- Random | 11.261 | 13.654
- Performance-first | 11.716 | 14.514
- Uncertainty–diversity | 9.684 | 8.787

### Supporting information

**S1 Study scope, datasets, and analysis populations — paragraph 8**

> All analyses are retrospective. Experimental outcomes originate from the two cited literature datasets, whereas computational poses are molecular representations rather than additional measured substrates. The selectivity target is unsigned enantiomeric excess (ee), reported in percent; MAE and RMSE are therefore expressed in ee percentage points. Yield is analysed separately. Missing labels, measured zero-ee outcomes, and protocol-specific analysis populations remain distinct.

**S1.1.1 Reaction sources and curation — paragraph 13**

> The experimental domains are Fe(P7)Cl and Fe(CMC-Por)Cl intramolecular C(sp3)–H amination, as reported independently by Lee and co-workers and Wang and co-workers, respectively [1,2]. The curation specification records reaction and substrate identifiers, catalyst and condition identifiers, starting-material azide SMILES, free-nitrene SMILES, product SMILES when reported, reactive-site atom maps, experimental ee/yield, family and scaffold groups, exclusions, source order, and provenance. Missing product structures remain null rather than being computationally reconstructed. Missing ee is not zero and is not replaced by yield. A measured zero-ee outcome remains a valid observation; an unreported reaction is not assigned a failure label.

**S1.1.1 Reaction sources and curation — paragraph 15**

> Table S2. Reported populations. Counts describe different analysis inputs, not successive interchangeable versions of one dataset.

**S1.1.1 Reaction sources and curation — paragraph 17**

> The independent progression summaries end at 37 revealed Fe(P7)Cl ee labels, 38 yield labels, and 25 Fe(CMC-Por)Cl aryl labels, leaving a route-dependent residual pool. These progression endpoints must not be substituted for the 38-substrate development cohort. Removing only 1ad from 41 records cannot explain a 39-record progression set. The release inventory identifies dataset-id-lists.csv as the explicit reconciliation; its population memberships and exclusion reasons must be used when reproducing each analysis.

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

**S4.3 Complete independent-progression summaries — paragraph 137**

> Route codes D, H, P, R, and U mean diversity-first, reported order, performance-first, random, and uncertainty–diversity. Model codes EN, R, and K mean Elastic Net, Ridge, and Tanimoto-kNN. NA means the threshold was not reached. Final n is the number of revealed labels, not the number of test predictions. The reference MAE and Δ (final minus reference) are documented summary values; discrepancies of 0.001 from subtraction of rounded MAEs are retained. Final-prefix MAEs concern route-dependent remaining substrates and cannot establish superiority on a common test set.

**S4.3 Complete independent-progression summaries — paragraph 142**

> Table S11. Fe(CMC-Por)Cl enantioselectivity: independent-progression summaries.

**S4.3 Complete independent-progression summaries — paragraph 144**

> Table S12. Fe(CMC-Por)Cl isolated yield: independent-progression summaries.

**S4.3 Complete independent-progression summaries — paragraph 146**

> Uncertainty–diversity minimises ee AUC-MAE for all three Fe(P7)Cl estimators and for Fe(CMC-Por)Cl Elastic Net/Ridge, but diversity-first gives lower Fe(CMC-Por)Cl Tanimoto-kNN AUC (171.515 versus 175.443). The latter estimator also reaches n₉0 earlier under reported order than under uncertainty–diversity (7 versus 14 labels). Thus threshold convergence and integrated error can disagree.

**S4.3 Complete independent-progression summaries — paragraph 147**

> Yield was evaluated as a separate secondary endpoint rather than as part of a composite acquisition objective. For Fe(CMC-Por)Cl, the reported-order and uncertainty–diversity AUC-MAE values were 457.616/467.958 for Elastic Net, 474.511/479.375 for Ridge, and 398.990/368.317 for Tanimoto-kNN, respectively (Figure S5). Thus, uncertainty–diversity gave marginally higher integrated errors with Elastic Net and Ridge but a lower error with Tanimoto-kNN. Fe(P7)Cl yield performance was likewise estimator-dependent. Table S12 reports the final-prefix values for completeness; because these values derive from route-dependent residual pools, they are not interpreted as common-test-set comparisons. Collectively, these analyses qualify the ee findings by demonstrating that acquisition performance depends on both the endpoint and estimator. The retrospective records do not include unreported failures or fully reconstruct the historical sequence of experimental decisions.

**S5.1 Curated substrate datasets — paragraph 156**

> curated-datasets/p7-records.jsonl and curated-datasets/cmcpor-records.jsonl are the designated ledgers for the 41 retained Fe(P7)Cl and 50 Fe(CMC-Por)Cl records, respectively. The latter comprise 33 aryl substrates and 17 sulfonyl controls. Records include substrate IDs, starting-material SMILES, experimental ee/yield, reaction information, and literature provenance.

**S5.1 Curated substrate datasets — paragraph 157**

> The curated-datasets/ directory indexes starting-material tables, candidate sites, atom mappings, reaction-centre decisions, and validation records. Family/scaffold assignments, shared identities, and exclusion reasons are associated with the relevant ledgers and analysis-specific splits. dataset-id-lists.csv identifies membership of the distinct development, CREST, and progression cohorts summarised in Table S2.

**S5.1 Curated substrate datasets — paragraph 158**

> curated-datasets/p7-optimization-conditions.csv contains the P7 reaction conditions and 16-condition optimisation table. Source fields and linked source-ledger/SMILES tables identify document and page/table locations for the reported experimental outcomes.

**S5.1 Curated substrate datasets — paragraph 159**

> Twenty-nine P7 records lack curated product mapping. Their starting structures and experimental labels are retained, while product fields remain null. Exclusions of 1z, 1ad, and 1an have distinct reasons; exclusion is not equivalent to zero ee, and a measured zero-ee outcome remains valid.

**S5.3 Central matched acquisition replay: provenance and reproducibility — paragraph 167**

> The recorded initial substrate pairs are 1a/1b for the Fe(P7)Cl reported-order route and 1a/1am for uncertainty–diversity; for Fe(CMC-Por)Cl they are 2aa/2ab and 2b/2ac, respectively. These are route-specific initial substrate selections, distinct from the pseudorandom seed used by code. Acquisition sequences are retained in selection-events.csv, and the learning curves report MAE, RMSE, and Spearman statistics at each evaluated prefix. Re-averaging the recorded prefix MAEs reproduces 21.672 and 9.684 for Fe(P7)Cl and 13.155 and 8.787 for Fe(CMC-Por)Cl (reported order and uncertainty–diversity, respectively), at the precision reported in the main-text matched-acquisition table. The remaining six policy means are reproduced from their corresponding learning-curve records by the same arithmetic averaging convention.

**S6.1 Feature groups, populations, and retrospective replay — paragraph 192**

> The supplied configuration description specifies the P7 active scope excluding 1ad and the CMC-Por primary aryl scope excluding seven locked audit records (2y, 2z, 4a, 4b, 4c, 4d, and 4e) from route fitting. Each domain is evaluated separately for ee and isolated yield, giving four domain–endpoint cells. Missing outcomes are excluded per endpoint, not replaced by zero. The original configuration and filtered snapshots were not supplied with this trace, so exact population membership and endpoint counts cannot be verified here or substituted from the other SI cohorts.

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

## Revision analysis and proposed response

The agreed plan is in `analysis_plan.md`; source reconciliation, mixed-pool and sulfonyl-only results, and required writing/system changes are recorded in `results_and_adjustments.md`. A proposed point-by-point reply is in `reviewer_response_draft.md`. The revised cumulative manuscript and SI highlight the new text. The original distributed ledger still needs its sulfonyl conditions and 6q yield qualifier corrected before submission, and the new artifacts must be included in the release.
