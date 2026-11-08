# Corrected point-by-point response working draft

**Working draft for author review.** The atom-mapping correction changes several results previously cited in earlier responses. This draft reflects the corrected independent AUC-MAE progression (500 random continuations per endpoint) and the complete corrected scan of all 13 shared identities. The 1i/2r pair ranks first by Jensen–Shannon divergence (0.030961 bits; TV 0.171882; Bhattacharyya overlap 0.978082). The revised manuscript and SI in this folder use the corrected results. The original historical run tree is incomplete for exact bitwise reconstruction of every pre-correction pose-derived calculation; that reproducibility limit should be retained in any final response.

## Reviewer 1

### Comment 1: confidence intervals and starting-pair stability

We corrected the pose-feature mapping and repeated the shared-start and common-test analyses using the same starts and test memberships. In 50 starting pairs, the mean source-order-minus-uncertainty–diversity difference is 9.83 ee points for Fe(P7)Cl and 4.84 for the Fe(CMC-Por)Cl aryl cohort; all 50 P7 starts and 45/50 CMC starts favour uncertainty–diversity. In the 20-split common-test analysis, mean differences are 6.99 and 2.50 points, favouring uncertainty–diversity in 19/20 and 11/20 splits. These are conditional analyses of overlapping starts/splits and do not support inference to new catalyst populations. The seven-record CMC audit changes direction from the archived result and is reported as such in the revised SI.

### Comment 2: justification and sensitivity of the acquisition weights

The 21-setting grid has been repeated with corrected features. The default ranks 8/21 for Fe(P7)Cl and 11/21 for Fe(CMC-Por)Cl by mean split MAE; it is not an established optimum. The weights remain a fixed heuristic and are described accordingly. Corrected grid tables must be checked against the final manuscript figures before submission.

### Comment 3: representation and acquisition interaction

The corrected factorial analysis preserves the same splits, starts and budgets. Mean MAEs for structure/source, structure/uncertainty–diversity, pose/source and pose/uncertainty–diversity are 11.34, 12.07, 20.71 and 13.72 ee points for Fe(P7)Cl, and 9.62, 10.77, 16.33 and 13.83 for Fe(CMC-Por)Cl. The combination does not outperform the structure-only cells on average. This is an interaction diagnostic within retrospective overlapping splits, not a population-level interaction test.

### Comment 4: family-held-out generalisation

After correction, Fe(P7)Cl family-held-out Elastic Net MAE is 10.406 for structure-only and 8.538 for structure plus pose, a 17.9% reduction. Pose error is lower for 11/17 families and 23/38 substrates, while the largest family favours structure-only. We now describe the result as modest and heterogeneous and do not claim reliable extrapolation to new chemical families.

### Comment 5: exclusion of sulfonyl substrates in CMC analysis

The corrected aryl-only acquisition result remains specific to the 26-record aryl cohort. The mixed-pool and sulfonyl-only analyses have been rerun with corrected features; sulfonyl-only mean ee MAE is 17.98 for source order, 19.22 for uncertainty–diversity and 19.63 for random continuation. Because class and experimental protocol differ, these analyses do not establish transfer across substrate classes. The manuscript and SI state this limitation.

### Comment 6: inconsistent isolated-yield performance

The corrected common-test yield analysis gives source-order / uncertainty–diversity / random MAEs of 25.36 / 18.38 / 20.93 for Fe(P7)Cl and 25.48 / 23.49 / 24.53 for the CMC aryl cohort. The average CMC direction differs from the previous draft, and split-level results remain mixed. The manuscript no longer attributes the outcome to a demonstrated mechanism; endpoint-specific algorithmic behaviour and unmeasured conversion or isolation effects remain possible explanations rather than established causes.

### Comment 7: established active-learning baselines

With corrected inputs, common-test mean ee MAEs for uncertainty–diversity / query by committee / expected improvement / Thompson sampling are 13.72 / 13.08 / 13.90 / 14.42 for Fe(P7)Cl and 13.83 / 13.40 / 16.41 / 15.33 for the CMC aryl cohort. Query by committee has lower mean error in both datasets. In the separate corrected independent progression (500 random continuations per endpoint), uncertainty–diversity has lower ee AUC-MAE than reported order for all three estimators in both cohorts. On CMC ee with Tanimoto-kNN, however, diversity-first is lower than uncertainty–diversity (171.515 vs 199.611). The comparison evaluates fixed retrospective implementations and does not establish a general ranking or state-of-the-art competitiveness.

## Reviewer 2

### Comment 1: low- and zero-ee outcomes

The source outcomes and cohort membership are unchanged by the geometry correction. The manuscript retains the source-verified low-ee inclusion counts, while prediction-dependent residual summaries have been recalculated. The four low-ee P7 examples remain in both validation protocols; their corrected mean signed errors are +17.85 and +18.56 ee points for target and family holdout. Zero-ee inclusion should be stated only where source records confirm it; no zero-ee result is inferred from a missing value.

### Comment 2: chemically interpretable substrate examples

The manuscript retains substrates 1a and 1ah with source-reported products 2a and 2ah at 92% and 50% ee and the corrected sampled structures. Their target-held-out corrected structure-plus-pose predictions are 90.2% and 58.7%; the geometric descriptor comparison is illustrative and not a causal or mechanistic explanation. The structures are sampled UFF assemblies, not transition states or measured conformational populations.

## Correction disclosure

An atom-index error affected pose-dependent values and downstream results using those features. We preserved the source records and archived coordinates, corrected the nitrene mapping, and regenerated the analyses identified above. Corrected AUC-MAE tables/plots, the complete 13-pair occupancy scan, the Stage 1-v2/Stage 2-v2/Stage 3a seed-pilot comparison, and the CREST/GFN2-xTB family ablation are included in the revised SI and correction package. The seed pilot no longer supports an accuracy gain from Stage 1-v2 pose filtering or the reference/shell features. The CREST/xTB point estimates favour augmentation, but paired substrate-bootstrap intervals include zero. The original historical run tree lacks complete records for exact bitwise reconstruction of every pre-correction pose-derived result. The authors should review the corrected response and complete the journal repository deposit before submission.
