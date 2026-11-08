# Reviewer 1, comment 4: Family held out extrapolation

## Reviewer comment

The family-held-out validation shows only a 10.3% improvement with PULSE-Pose, compared to 31.9% for target-held-out. This large gap suggests that the catalyst-contextual representation adds little value when extrapolating to unseen chemical families, which is precisely the scenario most relevant for real catalyst development. The manuscript does not adequately discuss this limitation.

## Highlighted material

The quoted text below is highlighted in yellow in the corresponding document copy. Figure captions identify the adjacent artwork. Table entries reproduce the highlighted cells.

### Manuscript

**3.2 Model fitting and validation — paragraph 39**

> Target-held-out validation and family-held-out validation address different questions. Target holdout asks whether a specific substrate can be predicted from the remaining scope, whereas family holdout removes every member of a chemical family and tests extrapolation across that family boundary. The matched Fe(P7)Cl development cohort contains 38 substrates from 17 families. Results from the two protocols are reported separately and are not numerically conflated; complete split memberships and inner-validation sizes remain in SI Section S3.

**4.1 Catalyst-referenced representations — paragraph 54**

> In the matched 38-substrate Fe(P7)Cl comparison (Fig. 3), adding selected pose descriptors to the structure-only Elastic Net model reduced target-held-out MAE from 12.612 to 8.583 ee percentage points, a 31.9% reduction. With complete families withheld, MAE decreased from 10.406 to 9.334, a smaller 10.3% improvement.

**4.1 Catalyst-referenced representations — paragraph 56**

> Figure 3. Selected catalyst-referenced descriptors improve prediction in the matched 38-substrate Fe(P7)Cl comparison using Elastic Net. Errors are ee percentage points. Target- and family-held-out validation answer different questions; SI Section S3 provides full metrics and split definitions.

**4.1 Catalyst-referenced representations — paragraph 57**

> The smaller family-held-out improvement indicates that catalyst-referenced geometry supplies useful information within the studied chemical domain but is less powerful when extrapolating across complete substrate families. The two protocols therefore support different levels of inference: the target-held-out result quantifies interpolation among represented chemistry, whereas the family-held-out result provides the more demanding test of transfer across family boundaries.

**4.1 Catalyst-referenced representations — paragraph 58**

> Larger spatial representations did not automatically improve prediction. Adding 655 occupancy and flexibility fields to the corresponding local-geometry reference worsened MAE from 10.281 to 14.132 ee points and changed R² from 0.311 to -0.175. Later descriptor additions produced only small or inconsistent changes across MAE, RMSE, and R² (SI Section S3). The observed pose benefit is therefore not explained simply by increasing descriptor dimensionality.

**4.1 Catalyst-referenced representations — paragraph 59**

> Isolated-substrate conformational and electronic additions also failed to improve the separately locked nested-family reference. MAE was 8.498 for the locked 248-field geometry, 8.858 after adding CREST geometry, 8.610 after adding GFN2-xTB electronic features, and 8.876 with both blocks.[36,37] No addition improved MAE, RMSE, or R². This comparison does not imply that CREST or GFN2-xTB are generally inferior; rather, isolated-substrate conformational or electronic information was insufficient to replace the catalyst-contextual representation in this dataset.

**4.1 Catalyst-referenced representations — paragraph 60**

> These results illustrate an important distinction between descriptor richness and usable information in the small-data regime. A representation can contain chemically meaningful spatial, conformational, or electronic quantities without improving prediction if the number of labelled substrates is insufficient to estimate their contributions reliably. Increasing representation dimensionality can therefore add variance, redundancy, or poorly constrained correlations rather than predictive information. The design objective is to identify representations that express chemically relevant distinctions at a complexity commensurate with the available data. In this sense, molecular representation and experimental acquisition address the same underlying limitation from opposite directions: one determines which information is encoded from each substrate, while the other determines which substrates are measured to provide that information.

**4.3 Information content of molecular representations — paragraph 80**

> Representation is a chemical design choice encompassing both information content and computational complexity.[39] The occupancy and CREST/GFN2-xTB ablations show that adding more spatial, conformational, or electronic variables does not automatically improve prediction. Catalyst-contextual descriptors allow chemists to encode system-specific information and test its predictive value,[25,26,40] consistent with the broader use of steric and electrostatic descriptors in catalyst-library screening.[41]

**4.4 From retrospective analysis to experimental scope design — paragraph 87**

> The experimental-design question is not intrinsically specific to iron porphyrins, but the present empirical validation is. Using two related but independently reported catalyst systems provides an intermediate validation level: the acquisition principle can be examined across distinct catalyst environments and substrate scopes without implying transfer across fundamentally different reaction classes. The results show that informative ordering can alter retrospective learning trajectories in both studied systems, but they do not establish that the same acquisition weights, candidate definitions, or magnitude of improvement will persist elsewhere. In particular, the observed advantage may depend on the initial measured panel, the estimator used to quantify uncertainty, the endpoint being learned, and the composition of the available candidate pool.

**4.4 From retrospective analysis to experimental scope design — paragraph 88**

> Transferability should therefore be considered separately for the representation and acquisition components. Catalyst-referenced descriptors such as PULSE-Pose are intrinsically dependent on the geometry and chemistry of the catalytic environment; extension to a different catalyst or transformation may require redefining the reactive frame, interaction features, or conformational treatment. PULSE-Acquire, by contrast, operates at a more abstract experimental-design level and may not require the same molecular representation to be retained. Its broader principle—balancing what the model does not yet know with what regions of chemical space remain poorly represented—could be implemented using different reaction-appropriate descriptors, uncertainty estimates, and chemical groupings. Future cross-reaction studies should therefore distinguish representation transfer, in which a molecular encoding remains predictive in a new system, from acquisition transfer, in which an information-guided selection strategy remains beneficial after the representation and acquisition components have been adapted to the new chemistry. The present work establishes neither form of transfer across unrelated catalytic classes.

**4.4 From retrospective analysis to experimental scope design — paragraph 89**

> The principal limitations accordingly apply to both components of the framework. For PULSE-Pose, the present analysis assumes a known reactive site and a fixed catalyst reference geometry; substantially flexible catalysts or reactions with competing unknown sites may require catalyst-ensemble sampling, joint catalyst–substrate conformational treatment, or an upstream site-selectivity model. For PULSE-Acquire, the analyses remain retrospective, different acquisition routes can leave different remaining prediction pools, sensitivity to the exact initial measured panel has not been exhaustively characterised, and the preferred policy is not universal across estimators or endpoints. No prospective laboratory loop or cross-reaction validation is reported. These boundaries define the next validation tasks: testing acquisition robustness to different starting scopes, determining whether acquisition rules require system-specific recalibration, evaluating chemically distinct catalyst families, and ultimately measuring whether information-guided substrate selection improves prospective experimental scope construction.

**5 Conclusions — paragraph 91**

> Selected catalyst-referenced descriptors added predictive value for Fe(P7)Cl, while information-guided ordering lowered retrospective learning error in both studied systems. The strongest and most consistent acquisition support was observed for ee; the advantage was neither estimator- nor endpoint-universal. Together, the results support substrate order as an experimental-design variable for learning data-limited catalyst scopes and position catalyst-contextual representation and acquisition as complementary, separately tested components.

### Supporting information

**S2.1 Molecular connectivity and feature definitions — paragraph 26**

> C1 contains 44 retained geometry summaries; C2 contains 16 explicit catalyst-interaction summaries. Their functional categories include attack-corridor geometry, directed fields, stratum contrasts/stability, catalyst contacts, pocket crowding, and corridor obstruction. Exact selected column names are referred to the released feature manifests, data dictionary, and feature source described in Section S5.5. Repeated numeric interaction values are averaged by substrate before selecting C2; missing required interactions cause failure, not zero imputation. A separate legacy candidate-site builder uses a chirality-aware 2,048-bit fingerprint and is not B5. Literature on cavity descriptors motivates catalyst-aware representations but does not validate this study's feature selection [6,10].

**S3.1 Leakage controls and protocol separation — paragraph 77**

> A substrate, not a pose, is the statistical observation. All of its poses remain in the same split. Standardisation, constant-feature filtering, and any learned feature selection or projection must use training data only, separating model selection from performance evaluation [23]. Family and scaffold exclusions are separate tests; ordinary sequential replay is not relabelled as a scaffold-held-out evaluation.

**S3.1 Leakage controls and protocol separation — paragraph 78**

> In target-held-out development, one of the 38 Fe(P7)Cl substrates is withheld. MaxMin Morgan/Tanimoto selection chooses 29 training substrates from the other 37; eight form a validation set for model selection. For held-out families of size 1, 2, 3, or 12, documented training/validation counts are respectively 30/7, 29/7, 28/7, and 21/5. The release inventory identifies the model-report split files for family assignments and split membership (Section S5.2). The matched structure-only and structure-plus-pose matrices contain 547 and 1,241 columns: they are not B5 and P2. Their ordered feature lists, selected parameters, and fitting settings should be matched to the released feature/report trees and source code, rather than inferred from dimensions alone.

**S3.1 Leakage controls and protocol separation — paragraph 79**

> Later Stage 3 and CREST comparisons use the same 38 substrates from 17 families with outer and inner leave-one-family-out evaluation, but a different validation implementation and locked 248-column geometry reference. The separate occupancy comparison uses its own reported local-geometry reference. No row in Table S5 should be compared across protocol blocks as if it were a paired ablation.

**S3.2 Prediction metrics and uncertainty — paragraph 90**

> Bootstrap resampling estimates sampling variability by drawing observations with replacement [29]. Confidence intervals are limited to those documented for the corresponding analysis. CREST paired bootstraps resample substrate IDs with replacement using identical indices for both models, 20,000 draws, and NumPy seed 20260907. The statistic is baseline MAE minus augmentation MAE, so positive values favour augmentation. This is not a family-cluster bootstrap, a posterior probability, or prospective experimental confidence.

**S3.3 Protocol-matched development results — paragraph 92**

> Table S5. Fe(P7)Cl ee development on the matched 38-substrate cohort. Each block is a separate validation experiment; all rows are Elastic Net results.

**S3.3 Protocol-matched development results — paragraph 94**

> The target- and family-holdout pose gains are 4.029 and 1.072 ee points, or 31.9% and 10.3%, respectively. The occupancy augmentation worsens MAE by 3.851 points (37.5%). Stage 3a-alt changes MAE by only -0.030 points; the combined Stage 3 block lowers MAE by 0.087 but worsens RMSE and R². No paired uncertainty interval for these small Stage 3 changes is available. These comparisons support selective retention of information, not a universal advantage of larger representations. The published descriptor literature provides methodological context, not evidence for these specific gains [6,30].

**S3.4 CREST/GFN2-xTB scope and execution — paragraph 98**

> S3.4 CREST/GFN2-xTB scope and execution

**S3.5 Population weights and descriptor definitions — paragraph 114**

> Table S7. Reported paired-bootstrap MAE improvement intervals (baseline minus augmentation). Positive values favour augmentation.

**S3.5 Population weights and descriptor definitions — paragraph 116**

> The unrounded combined improvement is reported as -0.377 points, with 0.107 of bootstrap draws above zero. Subtracting the displayed rounded MAEs gives -0.378; the rounding difference is retained rather than silently corrected. No addition improves the locked reference on MAE, RMSE, or R². No corresponding CREST yield experiment was reported.

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

**Table 7 in document order — Table S6. Nested-family CREST ablations, same 38 Fe(P7)Cl substrates. Dimensions are before fold-local filtering.**

- Representation | Columns | MAE | RMSE | R²
- Locked geometry | 248 | 8.498 | 11.357 | 0.476
- +CREST geometry | 258 | 8.858 | 11.578 | 0.455
- +xTB electronic | 261 | 8.610 | 11.745 | 0.440
- +Both blocks | 271 | 8.876 | 11.860 | 0.429

**Table 8 in document order — Table S7. Reported paired-bootstrap MAE improvement intervals (baseline minus augmentation). Positive values favour augmentation.**

- Augmentation | 95% percentile interval (ee points)
- CREST geometry | [-0.733,-0.009]
- xTB electronic | [-0.691,0.423]
- Combined | [-1.000,0.212]

## Family-held-out follow-up

The pre-analysis plan is in `analysis_plan.md`; paired archived-prediction diagnostics, limitations and validation are in `family_findings.md`, `results/` and `validation_report.txt`. The paired family MAE favoured pose in 11 of 17 families, but the largest (12-substrate) family favoured structure-only. Revised claims and the complete table must preserve the limitations of this small, imbalanced, retrospective cohort. The draft response is `reviewer_response_draft.md`.

The cumulative highlighted Word documents are `Manuscript_comment4_revised.docx` and `Supporting_Information_comment4_revised.docx`. They incorporate comments 1–3 and add the discussion and SI Table S20 for comment 4. An editorial assessment is recorded in `editorial_assessment.md`.
