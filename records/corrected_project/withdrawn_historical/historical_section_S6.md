# Withdrawn historical SI section: exploratory hierarchical Bayesian optimisation

This material was removed from the revised Supporting Information because the original configuration, input snapshots, and imported project modules needed to reproduce its 66-evaluation trace were unavailable. The search also consumed pose-derived Stage 2p features that were affected by the nitrene atom-mapping error. Its historical values are retained below for audit only; they are not corrected results and are not used to support any manuscript claim.

Source: Supporting_Information_corrected_working.docx, former Section S6.

S6 Exploratory hierarchical Bayesian optimisation of substrate-selection weights

This exploratory study examines whether reweighting chemically grouped rule features can improve retrospective substrate selection in the P7 and CMC-Por domains. The search first selects weights within V4, then within V6, and finally a V4/V6 mixing coefficient with both sets of group weights fixed. The methods below describe the supplied implementation; the numerical results are taken from the supplied 66-evaluation aggregate trace rather than a new execution during manuscript preparation.

S6.1 Feature groups, populations, and retrospective replay

V4 weights three named rule-feature groups: bde, electronic, and reaction_contrast. V6 additionally weights path_accessibility and local_regime. These are group-level acquisition parameters, not coefficients fitted to individual predictor columns. The supplied study description places each version at roughly 150–200 scalar columns but only tens of active substrates; reducing the search to interpretable groups limits its dimensionality without eliminating overfitting. Exact rule definitions and scaling are delegated to scripts/rule_based_diversity.py; the group names alone do not establish mechanistic or quantum-chemical interpretations.

The supplied configuration description specifies the P7 active scope excluding 1ad and the CMC-Por primary aryl scope excluding seven locked audit records (2y, 2z, 4a, 4b, 4c, 4d, and 4e) from route fitting. Each domain is evaluated separately for ee and isolated yield, giving four domain–endpoint cells. Missing outcomes are excluded per endpoint, not replaced by zero. The original configuration and filtered snapshots were not supplied with this trace, so exact population membership and endpoint counts cannot be verified here or substituted from the other SI cohorts.

The predictor contract is rdkit_morgan_stage2p, imported from scripts/scope_progression.py. Ridge predictions determine learning error; disagreement between Ridge and Tanimoto-kNN predictions contributes to acquisition. Elastic Net is disabled in this study. Each replay starts with two substrates selected by the existing diversity-first seed procedure, using random.Random(0). Remaining-pool Ridge MAE is evaluated at labelled prefixes from 2 to Nc-1, where Nc is the active population for cell c; one substrate remains unrevealed at the end. At each acquisition step, the highest-scoring whole substrate is selected, ties favour earlier source order, and the recorded outcome is revealed before refitting. Only revealed outcomes enter the within-route model fitting and acquisition calculation; the outer weight search nevertheless uses retrospective prediction errors from the full replay.

S6.2 Executable acquisition equations

For candidate i, revealed set L, and group g containing pg scaled features zᵢgk, group novelty is the nearest revealed-substrate distance within that group:

dg(i| L)=j∈ L(1)/(pg)∑k=1pg|zᵢgk-zjgk|, Nᵥ(i| L)=∑g∈ Gᵥwᵥgdg(i| L),

where v∈4,6, wᵥg≥0, and ∑g wᵥg=1. The nearest neighbour is determined separately within each group, before summing weighted distances.

Let Mt denote min–max normalisation across the current candidate pool, returning zero for a constant vector. Model disagreement D is Mt applied to the population standard deviation of the Ridge and Tanimoto-kNN predictions. Coverage Cᵥ averages family coverage and the version-specific rule-coverage score. The executable uncertainty and acquisition terms are

Uᵥ = 0.5Mt(Nᵥ)+0.5D,

Aᵥ = 0.4Nᵥ+0.4Uᵥ+0.2Cᵥ

= 0.4Nᵥ+0.2Mt(Nᵥ)+0.2D+0.2Cᵥ.

Only the group weights in novelty are searched within each version; the outer coefficients are fixed at their supplied default values. With the selected V4 and V6 equations fixed, the final stage searches 0≤λ≤1 in

Amix=λ A₄+(1-λ)A₆.

The supplied overview and equation-export strings omit Mt from the novelty contribution to uncertainty. Equations S8 and S9 instead follow the executable calculation. Although mixed novelty has group weights λ w₄g+(1-λ)w₆g, the full score also retains separate normalisation and version-specific coverage. It cannot generally be replaced by the exported shorthand 0.6Nmix+0.2D+0.2C. The supplied source is retained unchanged so this distinction remains auditable.

S6.3 Error and stability objective

For cell c, let ect be the remaining-pool Ridge MAE at prefix nt, with mc evaluated prefixes. Define Rc=(y̅c,10⁻12), where y̅c is the mean observed outcome over the endpoint-specific active pool, and Ec=(mc⁻1∑t ect,10⁻12). The three dimensionless components are

Bc = trapz(ect,nt)(nmc-n₁)Rc,

Fc = ∑t=1mc-1|ec,t+1-ect|(mc-1)Ec,

Hc = t|ec,t+1-ect|Rc.

Here Bc is the budget-normalised MAE area divided by the target mean, Fc is the normalised mean absolute curve change, and Hc is the normalised largest jump. The objective equally weights the four cells:

J=(1)/(4)∑c=1⁴(0.60Bc+0.25Fc+0.15Hc).

Lower J is preferred. Absolute-change penalties apply to both increases and decreases in error; they encourage smoother curves rather than measuring uncertainty calibration. The source field reference_intercept_mae stores y̅c, not the MAE of an intercept-only predictor. This composite objective is distinct from both the central mean-prefix MAE and the separate acquisition AUC-MAE in Section S4; its values cannot be interpreted as the main-text percentage reductions or experiments saved.

S6.4 Hierarchical search and recorded budgets

Initial group weights are sampled from a Dirichlet distribution with all concentration parameters equal to one; initial mixing coefficients are uniform on [0,1]. Bayesian proposals use a Gaussian-process surrogate with a Matern kernel (=2.5), an additive white-noise kernel initially set to 10⁻5, and normalised objective values. Group weights are encoded as log ratios to the final component, giving two surrogate coordinates for V4 and four for V6; the mixing stage has one coordinate. The source clips weights at 10⁻8 before normalising and encoding them.

At each Bayesian step, expected improvement for minimising J is evaluated over 2,048 proposals. Of these, approximately 65% perturb one of the eight best observed encoded vectors with Gaussian noise of standard deviation 0.8; the remainder are fresh global draws. The surrogate uses random_state=0, no additional hyperparameter-optimisation restarts, and suppressed convergence warnings. Mixing proposals from local perturbations may fall outside [0,1] and are clipped only after expected-improvement ranking. Duplicate decoded proposals are replaced by random draws but retain the trace label bayesian. Thus, the reported search is a finite proposal procedure, not a guaranteed global or strictly bounded acquisition-function optimum.

The supplied/default search seed is 20260914; the initial replay selector and Gaussian process separately use zero as described above. The aggregate trace has no seed field or accompanying original manifest. Table S13 therefore distinguishes the observed counts from the larger supplied defaults rather than claiming an independently verified original command.

Table S13. Recorded search budgets versus supplied defaults. Counts are random plus Bayesian objective evaluations, not laboratory experiments.

Stage | Recorded random | Recorded Bayesian | Default random + Bayesian
V4 | 12 | 8 | 24 + 16
V6 | 16 | 10 | 32 + 20
V4/V6 mixture | 12 | 8 | 24 + 16
Total | 40 | 26 | 80 + 52

S6.5 Best observed equations and search trace

Across the 66 supplied evaluations, the best observed objectives were 0.136810 for V4, 0.133336 for V6, and 0.131367 for the mixture (Table S14). The selected mixing coefficient was λ=0.3530403716, giving V4 and V6 score contributions of approximately 35.3% and 64.7%, respectively. Table S15 records the selected group weights and the corresponding mixed-novelty weights; Section S6.7 gives every evaluated parameter vector and objective component at the supplied numerical precision, including the selected observations, directly in this SI.

Table S14. Best observations in the supplied trace. Iterations are zero-based within each method. B̅, F̅ and H̅ average the components over the four cells.

Stage | Selected observation | J | B̅ | F̅ | H̅
V4 | Bayesian 2 | 0.136810 | 0.146871 | 0.139084 | 0.092775
V6 | Random 13 | 0.133336 | 0.150387 | 0.121231 | 0.085310
Mixture | Bayesian 7 | 0.131367 | 0.141656 | 0.134309 | 0.085310

Table S15. Selected group weights, rounded to six decimal places. Zeros denote groups absent from V4. The final column combines novelty weights only, not the complete acquisition equation.

Rule-feature group | V4 | V6 | Mixed novelty
BDE rule | 0.451395 | 0.070945 | 0.205259
Electronic | 0.094759 | 0.102770 | 0.099942
Reaction contrast | 0.453847 | 0.248608 | 0.321065
Path accessibility | 0.000000 | 0.371888 | 0.240596
Local regime | 0.000000 | 0.205790 | 0.133138

Bayesian evaluations improved the best initial random objective from 0.137351 to 0.136810 in V4 and from 0.131865 to 0.131367 in the mixing stage. V6's best weights came from random iteration 13; its Bayesian trials did not improve that result. The mixture reduced the composite objective and normalised area relative to selected V6, but had a higher mean-change penalty and the same largest-jump penalty. The result therefore represents a trade-off under the specified objective, not uniform improvement in all measures of stability. A single finite trace also does not establish the superiority of Bayesian optimisation over an equal-budget random-only search.

Figure S7. Hierarchical acquisition-weight search, rendered from the supplied aggregate trace. Points show individual objective evaluations; the black line shows the best value observed so far within each stage. Dashed lines separate random initialisation from Bayesian-labelled evaluations. The horizontal axis is search-evaluation order, not substrate label budget, and these are not learning curves.

 

Table S16. Complete supplied optimisation trace. Component means refer to the same four cells in every row; values are rounded here for readability. Section S6.7 provides the full-precision numerical record and all parameter vectors within this SI.

Stage | Method | Iteration | J | B̅ | F̅ | H̅
V4 | Random | 0 | 0.159730 | 0.157432 | 0.157699 | 0.172303
V4 | Random | 1 | 0.160949 | 0.165548 | 0.149905 | 0.160960
V4 | Random | 2 | 0.156274 | 0.157051 | 0.153277 | 0.158159
V4 | Random | 3 | 0.158956 | 0.157016 | 0.155656 | 0.172221
V4 | Random | 4 | 0.137428 | 0.147907 | 0.139071 | 0.092775
V4 | Random | 5 | 0.143055 | 0.146505 | 0.155569 | 0.108398
V4 | Random | 6 | 0.137351 | 0.147647 | 0.139385 | 0.092775
V4 | Random | 7 | 0.157158 | 0.157858 | 0.154879 | 0.158159
V4 | Random | 8 | 0.155783 | 0.156744 | 0.152051 | 0.158159
V4 | Random | 9 | 0.140982 | 0.146195 | 0.148907 | 0.106918
V4 | Random | 10 | 0.138027 | 0.147721 | 0.141911 | 0.092775
V4 | Random | 11 | 0.146652 | 0.152398 | 0.145425 | 0.125711
V4 | Bayesian | 0 | 0.158563 | 0.167021 | 0.153317 | 0.133473
V4 | Bayesian | 1 | 0.137337 | 0.147633 | 0.139365 | 0.092775
V4 | Bayesian | 2 | 0.136810 | 0.146871 | 0.139084 | 0.092775
V4 | Bayesian | 3 | 0.146701 | 0.152432 | 0.145541 | 0.125711
V4 | Bayesian | 4 | 0.139106 | 0.153031 | 0.139405 | 0.082907
V4 | Bayesian | 5 | 0.143280 | 0.149129 | 0.140338 | 0.124786
V4 | Bayesian | 6 | 0.155643 | 0.158332 | 0.147680 | 0.158159
V4 | Bayesian | 7 | 0.138440 | 0.147809 | 0.143356 | 0.092775
V6 | Random | 0 | 0.139190 | 0.147720 | 0.131299 | 0.118221
V6 | Random | 1 | 0.139042 | 0.149605 | 0.134436 | 0.104467
V6 | Random | 2 | 0.134817 | 0.147026 | 0.126381 | 0.100042
V6 | Random | 3 | 0.148848 | 0.152416 | 0.145682 | 0.139854
V6 | Random | 4 | 0.166217 | 0.170623 | 0.150048 | 0.175540
V6 | Random | 5 | 0.134949 | 0.144490 | 0.137616 | 0.092338
V6 | Random | 6 | 0.138628 | 0.153932 | 0.128633 | 0.094070
V6 | Random | 7 | 0.144295 | 0.152252 | 0.136348 | 0.125711
V6 | Random | 8 | 0.141083 | 0.152289 | 0.127627 | 0.118683
V6 | Random | 9 | 0.143530 | 0.150519 | 0.137447 | 0.125711
V6 | Random | 10 | 0.162397 | 0.165037 | 0.155109 | 0.163986
V6 | Random | 11 | 0.144440 | 0.152840 | 0.135519 | 0.125711
V6 | Random | 12 | 0.157042 | 0.152934 | 0.158144 | 0.171632
V6 | Random | 13 | 0.133336 | 0.150387 | 0.121231 | 0.085310
V6 | Random | 14 | 0.159855 | 0.166216 | 0.141047 | 0.165759
V6 | Random | 15 | 0.136126 | 0.141865 | 0.133094 | 0.118221
V6 | Bayesian | 0 | 0.134073 | 0.148583 | 0.128508 | 0.085310
V6 | Bayesian | 1 | 0.140019 | 0.148983 | 0.126859 | 0.126094
V6 | Bayesian | 2 | 0.143755 | 0.149238 | 0.141190 | 0.126094
V6 | Bayesian | 3 | 0.139433 | 0.148102 | 0.137538 | 0.107914
V6 | Bayesian | 4 | 0.135069 | 0.148099 | 0.124814 | 0.100042
V6 | Bayesian | 5 | 0.139211 | 0.150172 | 0.129891 | 0.110900
V6 | Bayesian | 6 | 0.139294 | 0.152139 | 0.129363 | 0.104467
V6 | Bayesian | 7 | 0.139415 | 0.152186 | 0.129732 | 0.104467
V6 | Bayesian | 8 | 0.141253 | 0.153315 | 0.126123 | 0.118221
V6 | Bayesian | 9 | 0.139036 | 0.149115 | 0.131728 | 0.110900
Mixed | Random | 0 | 0.135737 | 0.148292 | 0.132837 | 0.090349
Mixed | Random | 1 | 0.136603 | 0.146151 | 0.139984 | 0.092775
Mixed | Random | 2 | 0.137063 | 0.151087 | 0.131436 | 0.090349
Mixed | Random | 3 | 0.131865 | 0.141521 | 0.136626 | 0.085310
Mixed | Random | 4 | 0.136097 | 0.149564 | 0.131226 | 0.090349
Mixed | Random | 5 | 0.132192 | 0.141756 | 0.137367 | 0.085310
Mixed | Random | 6 | 0.135570 | 0.148611 | 0.131405 | 0.090349
Mixed | Random | 7 | 0.136224 | 0.147478 | 0.135481 | 0.092447
Mixed | Random | 8 | 0.133537 | 0.150820 | 0.120996 | 0.085310
Mixed | Random | 9 | 0.135736 | 0.148251 | 0.132930 | 0.090349
Mixed | Random | 10 | 0.132341 | 0.141816 | 0.137818 | 0.085310
Mixed | Random | 11 | 0.132208 | 0.141880 | 0.137134 | 0.085310
Mixed | Bayesian | 0 | 0.132208 | 0.141880 | 0.137134 | 0.085310
Mixed | Bayesian | 1 | 0.131975 | 0.141750 | 0.136514 | 0.085310
Mixed | Bayesian | 2 | 0.132013 | 0.141533 | 0.137184 | 0.085310
Mixed | Bayesian | 3 | 0.133336 | 0.150387 | 0.121231 | 0.085310
Mixed | Bayesian | 4 | 0.131975 | 0.141750 | 0.136514 | 0.085310
Mixed | Bayesian | 5 | 0.136858 | 0.150559 | 0.131882 | 0.090349
Mixed | Bayesian | 6 | 0.132571 | 0.142060 | 0.138151 | 0.085310
Mixed | Bayesian | 7 | 0.131367 | 0.141656 | 0.134309 | 0.085310

S6.6 Interpretation, records, and reproduction limits

The selected equations are retrospective development results. Their weights were chosen using the same domain–endpoint curves on which the objectives are reported; there is no independent outer test of the selected weights. In addition, the supplied code constructs and scales rule-feature matrices over filtered records including the locked audit rows. Although audit outcomes are excluded from route fitting and the objective, fully isolated audit preprocessing cannot be assumed without inspecting the imported feature and coverage routines. No audit-panel or prospective laboratory performance is supplied. An outcome-blind evaluation after freezing the equations is required before claiming general substrate-expansion performance.

This SI includes the 66-evaluation numerical record (Section S6.7), selected-weight summaries (Tables S14 and S15), the trace figure (Fig. S7), and the full supplied implementation (Section S6.8); no separate acquisition-study folder is needed to read these records. Arithmetic checking recomputed 0.60B̅+0.25F̅+0.15H̅ for every observation and compared it with the reported J, with maximum absolute discrepancy below 10⁻12. Each V4, V6, and mixed parameter vector was checked to contain three, five, and one entries, respectively, with all entries in [0,1] and each V4/V6 vector summing to one within 10⁻12. Iterations were verified as consecutive and zero-based within each stage and method, and every observation records four cells. These checks validate the transcription and arithmetic, not the original model calculations. A file-hash inventory prepared during transcription is not an original run manifest and does not establish execution provenance.

The implementation is designed to write filtered input snapshots, stage-specific search records, per-cell objectives, selected mixed-route learning curves and substrate sequences, equation exports, and a provenance manifest. Those original outputs, the configuration, and the two imported project modules were not supplied with the aggregate trace. Their absence prevents a complete replay or verification that the supplied source generated this trace. In particular, full prefix-level curves and selected routes cannot be reconstructed from aggregate objective rows alone. Figure S7 is derived solely from the supplied aggregate numerical trace.

The recorded random/Bayesian evaluation counts are 12/8 for V4, 16/10 for V6, and 12/8 for the mixture. The supplied/default seed is 20260914, but the original run seed is not independently documented. These settings alone do not provide an exact-regeneration recipe without the missing configuration, modules, inputs, and compatible software environment.

The supplied default command instead specifies 24/16, 32/20, and 24/16 random/Bayesian trials, respectively, giving 132 evaluations. Reproduction should retain the executable normalisation in Section S6.2, rather than the simplified equation-export strings.

S6.7 Full-precision numerical record

The following record reproduces all 66 supplied evaluations at their supplied decimal precision, without requiring an external CSV. Each observation is identified by stage, method, and zero-based iteration; cells is the number of domain–endpoint cells. For V4, w1–w3 denote BDE, electronic, and reaction-contrast weights. For V6, w1–w5 denote BDE, electronic, reaction-contrast, path-accessibility, and local-regime weights. For the mixed stage, lambda is the V4 score fraction; the V6 score fraction is 1-λ. All mixed evaluations hold the selected V4 (Bayesian iteration 2) and V6 (random iteration 13) vectors fixed. The fields J, B, F, and H are the composite objective and the four-cell means B̅, F̅, and H̅ defined in Section S6.3. Numerical precision reflects the supplied aggregate record, not measurement accuracy. No prefix-level or per-cell results can be inferred uniquely from these means.

v4 | random | iteration 0 | cells=4.0
w1=0.22662253039954267  w2=0.4548715942966364  w3=0.3185058753038209
J=0.15972961683391700  B=0.15743249623622700
F=0.15769884862591500  H=0.17230271290467800

v4 | random | iteration 1 | cells=4.0
w1=0.5319260746028258  w2=0.3391913590744131  w3=0.12888256632276096
J=0.1609487936100080  B=0.16554758669016500
F=0.14990525905005000  H=0.16095951222264600

v4 | random | iteration 2 | cells=4.0
w1=0.4398902551566529  w2=0.5277224642202236  w3=0.032387280623123356
J=0.1562738057700280  B=0.15705102060674300
F=0.15327707493652000  H=0.15815949781234800

v4 | random | iteration 3 | cells=4.0
w1=0.11302846372719985  w2=0.6066354358475254  w3=0.28033610042527485
J=0.1589564044057630  B=0.1570155531096670
F=0.15565564347259500  H=0.17222107781209500

v4 | random | iteration 4 | cells=4.0
w1=0.3965885043494749  w2=0.2784731192277408  w3=0.3249383764227844
J=0.13742819854865800  B=0.1479070584398810
F=0.13907083008757800  H=0.09277503975223440

v4 | random | iteration 5 | cells=4.0
w1=0.27078804280672436  w2=0.15823127375725934  w3=0.5709806834360162
J=0.14305492418159700  B=0.1465049335978260
F=0.15556914584495800  H=0.10839785041108500

v4 | random | iteration 6 | cells=4.0
w1=0.36719613251391187  w2=0.2993562880324468  w3=0.3334475794536414
J=0.13735094092708900  B=0.14764728546630800
F=0.13938525473787800  H=0.09277503975223440

v4 | random | iteration 7 | cells=4.0
w1=0.3036131112187801  w2=0.6017908471612071  w3=0.09459604162001282
J=0.15715837770201500  B=0.15785770935681200
F=0.1548793096643  H=0.15815949781234800

v4 | random | iteration 8 | cells=4.0
w1=0.3708959066556543  w2=0.5812209529345094  w3=0.04788314040983636
J=0.1557834078057420  B=0.15674446810657200
F=0.15205120907978500  H=0.15815949781234800

v4 | random | iteration 9 | cells=4.0
w1=0.33344329050655863  w2=0.2640676302415475  w3=0.40248907925189387
J=0.14098174978908900  B=0.1461952611499940
F=0.14890741948963300  H=0.10691825484456500

v4 | random | iteration 10 | cells=4.0
w1=0.4136021101696464  w2=0.2404333945350469  w3=0.3459644952953067
J=0.1380265779308160  B=0.14772109233282400
F=0.14191066627314400  H=0.09277503975223440

v4 | random | iteration 11 | cells=4.0
w1=0.4696369976499641  w2=0.207079545139819  w3=0.32328345721021684
J=0.14665160025292300  B=0.15239774315597000
F=0.14542507160440000  H=0.12571124305494100

v4 | bayesian | iteration 0 | cells=4.0
w1=0.8650091666986803  w2=0.12624083952507711  w3=0.008749993776242714
J=0.15856312287550200  B=0.16702148301694500
F=0.1533168671382880  H=0.1334734418717520

v4 | bayesian | iteration 1 | cells=4.0
w1=0.3793221260769476  w2=0.3193843598327563  w3=0.30129351409029614
J=0.1373374493148110  B=0.14763317556173300
F=0.13936515205974300  H=0.09277503975223440

v4 | bayesian | iteration 2 | cells=4.0
w1=0.45139491142158755  w2=0.09475858677269065  w3=0.4538465018057219
J=0.13680987846740800  B=0.1468710588069650
F=0.13908394888157300  H=0.09277503975223440

v4 | bayesian | iteration 3 | cells=4.0
w1=0.5048995145072868  w2=0.18170843313806773  w3=0.31339205235464557
J=0.1467012138810970  B=0.1524323063504080
F=0.14554057445044400  H=0.12571124305494100

v4 | bayesian | iteration 4 | cells=4.0
w1=0.6858343402596399  w2=0.09685091270402818  w3=0.2173147470363319
J=0.13910595624112900  B=0.15303105921894100
F=0.13940486786329500  H=0.08290735829294130

v4 | bayesian | iteration 5 | cells=4.0
w1=0.10024330725916387  w2=0.29811291476257384  w3=0.6016437779782623
J=0.14328015638017500  B=0.14912949658081100
F=0.14033818863040500  H=0.12478607516058100

v4 | bayesian | iteration 6 | cells=4.0
w1=0.27672186881657784  w2=0.4810034089602657  w3=0.24227472222315646
J=0.15564293696126000  B=0.15833164176710900
F=0.14768010891657000  H=0.15815949781234800

v4 | bayesian | iteration 7 | cells=4.0
w1=0.47436735419553094  w2=0.15054912455438635  w3=0.3750835212500827
J=0.13844041846753900  B=0.14780855403593200
F=0.14335612033257700  H=0.09277503975223440

v6 | random | iteration 0 | cells=4.0
w1=0.060798454146137035  w2=0.43028350917545477  w3=0.14731610284844227
w4=0.1852471904111201  w5=0.17635474341884586
J=0.1391901960564670  B=0.1477204041698300
F=0.1312989774957880  H=0.11822139453747900

v6 | random | iteration 1 | cells=4.0
w1=0.03869647952592901  w2=0.01816199167455803  w3=0.15489075342528338
w4=0.3495887166982978  w5=0.43866205867593194
J=0.13904220428773800  B=0.14960539036096400
F=0.13443581454719900  H=0.1044667762290690

v6 | random | iteration 2 | cells=4.0
w1=0.0005624710019175985  w2=0.02555184737945818  w3=0.1534553628178725
w4=0.3736749454235442  w5=0.44675537337720744
J=0.134817248591137  B=0.14702621454777500
F=0.1263808347033130  H=0.10004207457762600

v6 | random | iteration 3 | cells=4.0
w1=0.28181377368419347  w2=0.31361014194471243  w3=0.25617498337525046
w4=0.07117815236970766  w5=0.07722294862613595
J=0.14884803640012000  B=0.1524155300354720
F=0.14568219862698600  H=0.13985445814727100

v6 | random | iteration 4 | cells=4.0
w1=0.6928157110590618  w2=0.0022252298783172427  w3=0.18645493513457048
w4=0.07340895003498475  w5=0.04509517389306592
J=0.1662169084086600  B=0.17062290748727600
F=0.15004836848413800  H=0.17554047863506200

v6 | random | iteration 5 | cells=4.0
w1=0.1740126618973145  w2=0.02990828229797676  w3=0.6939782520356229
w4=0.07865119529533653  w5=0.023449608473749377
J=0.13494872499623100  B=0.14449029328805900
F=0.13761550385167700  H=0.09233782040317350

v6 | random | iteration 6 | cells=4.0
w1=0.1575797550703232  w2=0.02697805592963248  w3=0.1669385981099203
w4=0.4796993986388395  w5=0.16880419225128465
J=0.1386276867769910  B=0.15393162189063200
F=0.12863282258456400  H=0.09407005330980120

v6 | random | iteration 7 | cells=4.0
w1=0.09990193109612783  w2=0.10665174597292283  w3=0.36163541706711566
w4=0.16756409591975627  w5=0.2642468099440774
J=0.14429480623810000  B=0.15225169677477500
F=0.13634840685997600  H=0.12571124305494100

v6 | random | iteration 8 | cells=4.0
w1=0.17923638587586  w2=0.4657470534191553  w3=0.025991475857415413
w4=0.2996164431589098  w5=0.029408641688659573
J=0.14108260645388  B=0.15228871072340000
F=0.12762744414755600  H=0.11868345988634100

v6 | random | iteration 9 | cells=4.0
w1=0.20843005628775463  w2=0.25383332312478996  w3=0.3030112161602841
w4=0.09842206548012515  w5=0.1363033389470462
J=0.14353013483485300  B=0.1505194083593490
F=0.1374472134440120  H=0.12571124305494100

v6 | random | iteration 10 | cells=4.0
w1=0.44963807177968  w2=0.1112554527547685  w3=0.0033394494704463255
w4=0.4019678752047494  w5=0.03379915079035576
J=0.16239706877517200  B=0.16503665626390400
F=0.15510897410366700  H=0.1639855432727560

v6 | random | iteration 11 | cells=4.0
w1=0.2054093379488451  w2=0.14953911506554457  w3=0.278879344971712
w4=0.1459659791417343  w5=0.22020622287216413
J=0.14444040368509700  B=0.15283987356431300
F=0.13551917235307400  H=0.12571124305494100

v6 | random | iteration 12 | cells=4.0
w1=0.00861628400619884  w2=0.6160008886944278  w3=0.20470498189955016
w4=0.042102811277916  w5=0.12857503412190716
J=0.157041512606351  B=0.15293423721551500
F=0.15814444684595100  H=0.17163239043702600

v6 | random | iteration 13 | cells=4.0
w1=0.07094468637064832  w2=0.10277007913969302  w3=0.24860758432871893
w4=0.37188790552302214  w5=0.20578974463791747
J=0.13333614370779200  B=0.15038655989868500
F=0.12123080873358300  H=0.0853100372345731

v6 | random | iteration 14 | cells=4.0
w1=0.3345052660849171  w2=0.060640198734329895  w3=0.07783897936137303
w4=0.23502146839361648  w5=0.2919940874257633
J=0.1598553660735300  B=0.16621606606297800
F=0.14104747414050700  H=0.16575905267077400

v6 | random | iteration 15 | cells=4.0
w1=0.04233737810049633  w2=0.08294580416123082  w3=0.04864190595124049
w4=0.17396053196029915  w5=0.6521143798267333
J=0.136125703750629  B=0.14186518990192800
F=0.13309352251540300  H=0.11822139453747900

v6 | bayesian | iteration 0 | cells=4.0
w1=0.019934596576399444  w2=0.015277616763591444  w3=0.19320966057557235
w4=0.5731430720756583  w5=0.19843505400877848
J=0.1340734715571430  B=0.1485834808058910
F=0.1285075099536890  H=0.0853100372345731

v6 | bayesian | iteration 1 | cells=4.0
w1=0.0032456159251477183  w2=0.03292412401040606  w3=0.06910812796050518
w4=0.5049719766073074  w5=0.3897501554966338
J=0.14001859509800400  B=0.14898302620109900
F=0.12685860595176600  H=0.1260941859293530

v6 | bayesian | iteration 2 | cells=4.0
w1=0.03977088450320193  w2=0.2422060213097889  w3=0.1701522151793792
w4=0.4143345456923765  w5=0.13353633331525347
J=0.14375452829473100  B=0.14923799961369500
F=0.14119040254844200  H=0.1260941859293530

v6 | bayesian | iteration 3 | cells=4.0
w1=0.035442417322456  w2=0.010462258766045526  w3=0.2501270018126791
w4=0.43497868826373476  w5=0.2689896338350847
J=0.13943296185158400  B=0.1481024320005290
F=0.1375375752975430  H=0.10791405884586900

v6 | bayesian | iteration 4 | cells=4.0
w1=0.0139699294489297  w2=0.18322380227604854  w3=0.2136984473740009
w4=0.36623751936925775  w5=0.22287030153176304
J=0.13506915642065200  B=0.14809902174932300
F=0.12481372873765700  H=0.10004207457762600

v6 | bayesian | iteration 5 | cells=4.0
w1=0.0006302052573385854  w2=0.010830950378098007  w3=0.15200995961886962
w4=0.5381366304189744  w5=0.2983922543267193
J=0.13921118799453400  B=0.15017240998395000
F=0.12989091807419100  H=0.11090008323743800

v6 | bayesian | iteration 6 | cells=4.0
w1=0.0025063450666493146  w2=0.006834093526438503  w3=0.13042255833953526
w4=0.38341586325731586  w5=0.476821139810061
J=0.13929396760320600  B=0.15213869231619400
F=0.1293629431165150  H=0.1044667762290690

v6 | bayesian | iteration 7 | cells=4.0
w1=0.0016358120201169209  w2=0.008572024049672044  w3=0.21363539609469212
w4=0.3517401814281348  w5=0.4244165864073841
J=0.13941479052717100  B=0.152186300031812
F=0.12973197629489600  H=0.1044667762290690

v6 | bayesian | iteration 8 | cells=4.0
w1=0.0008282147572360037  w2=0.09984177345083593  w3=0.09991331834097092
w4=0.2285860488192671  w5=0.57083064463169
J=0.14125293339999600  B=0.15331493674218100
F=0.1261230486962640  H=0.11822139453747900

v6 | bayesian | iteration 9 | cells=4.0
w1=0.012090813221483566  w2=0.05379714676894787  w3=0.26683179559275777
w4=0.44384556205285314  w5=0.22343468236395778
J=0.13903614723059300  B=0.14911516865880800
F=0.13172813419876900  H=0.11090008323743800

mixed | random | iteration 0 | cells=4.0
lambda=0.2467726210808706
J=0.1357366604588210  B=0.14829189169064300
F=0.13283660618766400  H=0.09034915931679240

mixed | random | iteration 1 | cells=4.0
lambda=0.9519137942931157
J=0.13660283730693100  B=0.14615113313750500
F=0.13998360584637200  H=0.09277503975223440

mixed | random | iteration 2 | cells=4.0
lambda=0.180635034418146
J=0.13706338975468700  B=0.1510866986477670
F=0.13143598667403400  H=0.09034915931679240

mixed | random | iteration 3 | cells=4.0
lambda=0.6144768121150411
J=0.1318653318189530  B=0.1415205447053000
F=0.13662599764234700  H=0.0853100372345731

mixed | random | iteration 4 | cells=4.0
lambda=0.7567553818897509
J=0.13609742108349500  B=0.1495643395007150
F=0.1312257739421880  H=0.09034915931679240

mixed | random | iteration 5 | cells=4.0
lambda=0.39550179600222013
J=0.13219174160745000  B=0.14175584101328200
F=0.13736692565717900  H=0.0853100372345731

mixed | random | iteration 6 | cells=4.0
lambda=0.22414262486435854
J=0.13557022216919300  B=0.14861106800894700
F=0.13140482986522200  H=0.09034915931679240

mixed | random | iteration 7 | cells=4.0
lambda=0.8452554357990352
J=0.1362243790548530  B=0.14747842023467000
F=0.13548109969063600  H=0.0924470132759497

mixed | random | iteration 8 | cells=4.0
lambda=0.028027860704177066
J=0.13353748490821400  B=0.15082009940788300
F=0.12099567871319100  H=0.0853100372345731

mixed | random | iteration 9 | cells=4.0
lambda=0.2317997510976677
J=0.13573551637403900  B=0.1482511973085850
F=0.13292969636547600  H=0.09034915931679240

mixed | random | iteration 10 | cells=4.0
lambda=0.48570999677202276
J=0.13234073950629900  B=0.14181637212415500
F=0.13781764258647800  H=0.0853100372345731

mixed | random | iteration 11 | cells=4.0
lambda=0.4704096172771579
J=0.13220780677231600  B=0.14187984431841300
F=0.13713357838433000  H=0.0853100372345731

mixed | bayesian | iteration 0 | cells=4.0
lambda=0.47037512214525945
J=0.13220780677231600  B=0.14187984431841300
F=0.13713357838433000  H=0.0853100372345731

mixed | bayesian | iteration 1 | cells=4.0
lambda=0.5777387539236132
J=0.13197509020303700  B=0.14175012441490400
F=0.13651403987563400  H=0.0853100372345731

mixed | bayesian | iteration 2 | cells=4.0
lambda=0.4282824752029448
J=0.13201250496716600  B=0.14153331634829100
F=0.1371840382920210  H=0.0853100372345731

mixed | bayesian | iteration 3 | cells=4.0
lambda=0.0
J=0.13333614370779200  B=0.15038655989868500
F=0.12123080873358300  H=0.0853100372345731

mixed | bayesian | iteration 4 | cells=4.0
lambda=0.598192428664409
J=0.13197509020303700  B=0.14175012441490400
F=0.13651403987563400  H=0.0853100372345731

mixed | bayesian | iteration 5 | cells=4.0
lambda=0.6499405288608749
J=0.13685831907137400  B=0.15055923653512400
F=0.1318816130111240  H=0.09034915931679240

mixed | bayesian | iteration 6 | cells=4.0
lambda=0.542733985535668
J=0.13257057780746900  B=0.14206043876590900
F=0.13815123585095000  H=0.0853100372345731

mixed | bayesian | iteration 7 | cells=4.0
lambda=0.3530403715697483
J=0.13136722403126500  B=0.14165590263939000
F=0.13430870744978000  H=0.0853100372345731

S6.8 Supplied implementation

The full supplied optimisation implementation follows, embedded directly in this SI. Code identifiers, comments, and computational behaviour are preserved, including the equation-export and normalisation-field qualifications discussed above. This listing depends on the original project modules and configuration; it is not a standalone reproduction package.

#!/usr/bin/env python3
"""Hierarchically optimize V4/V6 rule-feature weights for scope expansion.

The optimization is deliberately kept in this folder so the methods, input
snapshot, search trace, and selected equations can be audited together. It
does not alter the established V0--V6 implementation.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
from scipy.stats import norm
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, WhiteKernel
from sklearn.exceptions import ConvergenceWarning


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import rule_based_diversity as rules  # noqa: E402
import scope_progression as baseline  # noqa: E402


SCHEMA_VERSION = "acquire-v1"
TARGETS = ("ee_percent", "isolated_yield_percent")
VERSION_BLOCKS = {
    "v4": ("bde", "electronic", "reaction_contrast"),
    "v6": ("bde", "electronic", "reaction_contrast", "path_accessibility", "local_regime"),
}
DEFAULT_SEED = 20260914
DEFAULT_RANDOM_V4 = 24
DEFAULT_BAYES_V4 = 16
DEFAULT_RANDOM_V6 = 32
DEFAULT_BAYES_V6 = 20
DEFAULT_RANDOM_MIX = 24
DEFAULT_BAYES_MIX = 16
DEFAULT_OBJECTIVE = {
    "auc_weight": 0.60,
    "fluctuation_weight": 0.25,
    "max_jump_weight": 0.15,
    "acquisition_weights": {"novelty": 0.40, "uncertainty": 0.40, "coverage": 0.20},
}


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    rows = list(rows)
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        for field in row:
            if field not in fields:
                fields.append(field)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def finite(value: float | None) -> float | None:
    if value is None or not math.isfinite(float(value)):
        return None
    return float(value)


def minmax(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    if len(values) == 0:
        return values
    low = float(np.min(values))
    high = float(np.max(values))
    if high <= low:
        return np.zeros_like(values)
    return (values - low) / (high - low)


@dataclass
class DomainData:
    name: str
    records_path: Path
    stage2p_path: Path
    rows: list[baseline.ScopeRow]
    table: baseline.FeatureTable
    rule_table: rules.RuleFeatureTable
    active_indices: list[int]
    audit_indices: list[int]
    block_matrices: dict[str, np.ndarray]
    prediction_cache: dict[tuple[str, tuple[int, ...]], dict[str, dict[int, float]]]

    @property
    def active_ids(self) -> list[str]:
        return [self.rows[index].substrate_id for index in self.active_indices]

    def target_values(self, target: str) -> np.ndarray:
        return np.asarray(
            [
                baseline.outcome_value(row.record, target)
                if baseline.outcome_value(row.record, target) is not None
                else np.nan
                for row in self.rows
            ],
            dtype=float,
        )

    def target_active_indices(self, target: str) -> list[int]:
        values = self.target_values(target)
        return [index for index in self.active_indices if not np.isnan(values[index])]

    def predictions(self, target: str, selected: Sequence[int], test: Sequence[int]) -> dict[str, np.ndarray]:
        """Cache all-model predictions for a selected prefix.

        The prediction model is fixed to the established rdkit/morgan/Stage 2p
        representation. The optimized rule weights determine the acquisition
        order; they are not allowed to alter the already-frozen predictor
        contract during this retrospective acquisition study.
        """
        selected_key = tuple(sorted(int(index) for index in selected))
        key = (target, selected_key)
        cached = self.prediction_cache.get(key)
        if cached is None:
            values = self.target_values(target)
            pool = self.target_active_indices(target)
            held_out = [index for index in pool if index not in selected_key]
            raw = baseline.fit_predict_models(
                self.table.matrix("rdkit_morgan_stage2p"),
                self.table.fingerprint_matrix,
                list(selected_key),
                held_out,
                values,
                include_elastic_net=False,
            )
            cached = {
                model: {index: float(prediction) for index, prediction in zip(held_out, prediction_values, strict=True)}
                for model, prediction_values in raw.items()
            }
            self.prediction_cache[key] = cached
        output: dict[str, np.ndarray] = {}
        for model, by_index in cached.items():
            output[model] = np.asarray([by_index[index] for index in test if index in by_index], dtype=float)
        return output


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"unsupported config schema: {config.get('schema_version')}")
    return config


def resolve_path(value: str, config_path: Path) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else (config_path.parent.parent / candidate).resolve()


def load_domains(config: dict[str, Any], config_path: Path) -> list[DomainData]:
    domains: list[DomainData] = []
    for spec in config["domains"]:
        records_path = resolve_path(spec["records_path"], config_path)
        stage2p_path = resolve_path(spec["stage2p_features_path"], config_path)
        rows = baseline.load_scope_rows(records_path, spec.get("catalyst_id"))
        excluded = set(spec.get("exclude_ids", []))
        rows = [row for row in rows if row.substrate_id not in excluded]
        family_ids = set(spec.get("family_ids", []))
        if family_ids:
            rows = [row for row in rows if row.family_id in family_ids]
        if not rows:
            raise ValueError(f"{spec['name']}: no rows after filtering")
        table = baseline.build_feature_table(rows, stage2p_path)
        rule_table = rules.build_rule_feature_table([row.record for row in rows])
        audit_ids = set(spec.get("audit_ids", []))
        unknown_audits = sorted(audit_ids - set(table.ids))
        if unknown_audits:
            raise ValueError(f"{spec['name']}: audit IDs not found: {', '.join(unknown_audits)}")
        audit_indices = [index for index, row in enumerate(rows) if row.substrate_id in audit_ids]
        active_indices = [index for index in range(len(rows)) if index not in audit_indices]
        if len(active_indices) < 4:
            raise ValueError(f"{spec['name']}: fewer than four active records")
        block_matrices = {
            block: rules.scale_matrix(
                np.asarray(
                    [[row.blocks.get(block, {}).get(name, 0.0) for name in rule_table.block_names[block]] for row in rule_table.rows],
                    dtype=float,
                ),
                rule_table.block_names[block],
            )
            for block in rules.ALL_BLOCKS
        }
        domains.append(
            DomainData(
                name=str(spec["name"]),
                records_path=records_path,
                stage2p_path=stage2p_path,
                rows=rows,
                table=table,
                rule_table=rule_table,
                active_indices=active_indices,
                audit_indices=audit_indices,
                block_matrices=block_matrices,
                prediction_cache={},
            )
        )
    return domains


def snapshot_inputs(domains: Sequence[DomainData], output_dir: Path) -> None:
    """Write the exact filtered retrospective input snapshot used by acquire."""
    records: list[dict[str, Any]] = []
    metadata: list[dict[str, Any]] = []
    rule_rows: list[dict[str, Any]] = []
    stage2p_rows: list[dict[str, Any]] = []
    for domain in domains:
        stage2p_by_id = {
            baseline.record_id(record): record
            for record in baseline.read_jsonl(domain.stage2p_path)
            if baseline.record_id(record) in {row.substrate_id for row in domain.rows}
        }
        for row in domain.rows:
            if row.substrate_id in stage2p_by_id:
                serialized_stage2p = dict(stage2p_by_id[row.substrate_id])
                serialized_stage2p["acquire_domain"] = domain.name
                stage2p_rows.append(serialized_stage2p)
        for index, row in enumerate(domain.rows):
            record = dict(row.record)
            record["acquire_domain"] = domain.name
            record["acquire_is_locked_audit"] = index in domain.audit_indices
            records.append(record)
            metadata.append(
                {
                    "domain": domain.name,
                    "substrate_id": row.substrate_id,
                    "family_id": row.family_id,
                    "source_order": row.source_order,
                    "is_locked_audit": index in domain.audit_indices,
                    "is_active": index in domain.active_indices,
                    "ee_percent": baseline.outcome_value(row.record, "ee_percent"),
                    "isolated_yield_percent": baseline.outcome_value(row.record, "isolated_yield_percent"),
                }
            )
            serialized = domain.rule_table.rows[index].as_json(version="v6")
            serialized["acquire_domain"] = domain.name
            rule_rows.append(serialized)
    data_dir = output_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    with (data_dir / "scope-input-records.jsonl").open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    write_csv(data_dir / "candidate-metadata.csv", metadata)
    with (data_dir / "stage2p-features.jsonl").open("w", encoding="utf-8") as handle:
        for row in stage2p_rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    with (data_dir / "rule-features-v6.jsonl").open("w", encoding="utf-8") as handle:
        for row in rule_rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def simplex_from_logits(logits: np.ndarray) -> np.ndarray:
    logits = np.asarray(logits, dtype=float)
    shifted = logits - np.max(logits)
    values = np.exp(shifted)
    return values / np.sum(values)


def random_weights(rng: np.random.Generator, dimension: int) -> np.ndarray:
    return rng.dirichlet(np.ones(dimension, dtype=float))


def weighted_novelty(
    domain: DomainData,
    candidates: Sequence[int],
    selected: Sequence[int],
    block_weights: dict[str, float],
) -> np.ndarray:
    if not candidates:
        return np.asarray([], dtype=float)
    if not selected:
        return np.ones(len(candidates), dtype=float)
    candidate_array = np.asarray(candidates, dtype=int)
    selected_array = np.asarray(selected, dtype=int)
    score = np.zeros(len(candidates), dtype=float)
    weight_total = 0.0
    for block, weight in block_weights.items():
        if weight <= 0.0:
            continue
        matrix = domain.block_matrices[block]
        differences = np.abs(matrix[candidate_array][:, None, :] - matrix[selected_array][None, :, :])
        distances = np.min(np.mean(differences, axis=2), axis=1)
        score += float(weight) * distances
        weight_total += float(weight)
    return score / weight_total if weight_total else np.zeros(len(candidates), dtype=float)


def weighted_components(
    domain: DomainData,
    target: str,
    selected: Sequence[int],
    candidates: Sequence[int],
    block_weights: dict[str, float],
    acquisition_weights: dict[str, float] | None = None,
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    acquisition_weights = acquisition_weights or DEFAULT_OBJECTIVE["acquisition_weights"]
    novelty = weighted_novelty(domain, candidates, selected, block_weights)
    family_coverage = baseline.family_coverage(domain.table, candidates, selected)
    version = "v6" if "path_accessibility" in block_weights else "v4"
    rule_coverage = rules.rule_coverage_scores(domain.rule_table, candidates, selected, version)
    coverage = 0.5 * family_coverage + 0.5 * rule_coverage
    predictions = domain.predictions(target, selected, candidates)
    disagreement_values: list[np.ndarray] = []
    for model in ("ridge", "tanimoto_knn"):
        if model in predictions:
            disagreement_values.append(predictions[model])
    if len(disagreement_values) > 1:
        disagreement = minmax(np.std(np.vstack(disagreement_values), axis=0))
    else:
        disagreement = np.zeros(len(candidates), dtype=float)
    uncertainty = 0.5 * minmax(novelty) + 0.5 * disagreement
    score = (
        float(acquisition_weights["novelty"]) * novelty
        + float(acquisition_weights["uncertainty"]) * uncertainty
        + float(acquisition_weights["coverage"]) * coverage
    )
    return score, {
        "weighted_novelty": novelty,
        "model_disagreement": disagreement,
        "uncertainty": uncertainty,
        "coverage": coverage,
    }


def make_block_weights(version: str, values: Sequence[float]) -> dict[str, float]:
    blocks = VERSION_BLOCKS[version]
    weights = np.asarray(values, dtype=float)
    if len(weights) != len(blocks) or np.any(weights < 0.0) or not np.isfinite(weights).all():
        raise ValueError(f"invalid {version} weights")
    total = float(np.sum(weights))
    if total <= 0.0:
        raise ValueError(f"{version} weights sum to zero")
    normalized = weights / total
    return {block: float(value) for block, value in zip(blocks, normalized, strict=True)}


def mixed_block_weights(v4: dict[str, float], v6: dict[str, float], mix_v4: float) -> dict[str, float]:
    """Represent the mixed distance as a block-level equation for reporting."""
    output = {block: (float(mix_v4) * v4.get(block, 0.0) + (1.0 - float(mix_v4)) * v6.get(block, 0.0)) for block in VERSION_BLOCKS["v6"]}
    return output


def route_and_curves(
    domains: Sequence[DomainData],
    stage: str,
    v4_weights: dict[str, float],
    v6_weights: dict[str, float],
    mix_v4: float,
    record_routes: bool = False,
    objective_config: dict[str, Any] | None = None,
) -> tuple[dict[str, float], list[dict[str, Any]], list[dict[str, Any]]]:
    objective_config = objective_config or DEFAULT_OBJECTIVE
    acquisition_weights = objective_config.get("acquisition_weights", DEFAULT_OBJECTIVE["acquisition_weights"])
    auc_weight = float(objective_config.get("auc_weight", DEFAULT_OBJECTIVE["auc_weight"]))
    fluctuation_weight = float(objective_config.get("fluctuation_weight", DEFAULT_OBJECTIVE["fluctuation_weight"]))
    max_jump_weight = float(objective_config.get("max_jump_weight", DEFAULT_OBJECTIVE["max_jump_weight"]))
    cell_metrics: list[dict[str, Any]] = []
    curve_rows: list[dict[str, Any]] = []
    route_rows: list[dict[str, Any]] = []
    for domain in domains:
        for target in TARGETS:
            target_pool = domain.target_active_indices(target)
            if len(target_pool) < 4:
                continue
            if stage == "v4":
                novelty_weights = v4_weights
            elif stage == "v6":
                novelty_weights = v6_weights
            else:
                novelty_weights = None
            values = domain.target_values(target)
            seed = baseline.seed_indices(domain.table, target_pool, "diversity_first", random.Random(0))
            selected = list(seed)
            if record_routes:
                for step, index in enumerate(selected, start=1):
                    route_rows.append(
                        {
                            "stage": stage,
                            "domain": domain.name,
                            "target": target,
                            "step": step,
                            "selected_substrate_id": domain.rows[index].substrate_id,
                            "selection_phase": "initial_seed",
                            "selection_score": None,
                        }
                    )
            for n_labeled in range(2, len(target_pool)):
                train = list(selected)
                test = [index for index in target_pool if index not in selected]
                predictions = domain.predictions(target, train, test)
                ridge_predictions = predictions.get("ridge")
                if ridge_predictions is not None and len(ridge_predictions):
                    observed = values[np.asarray(test, dtype=int)]
                    mae = float(np.mean(np.abs(observed - ridge_predictions)))
                    curve_rows.append(
                        {
                            "stage": stage,
                            "domain": domain.name,
                            "target": target,
                            "n_labeled": n_labeled,
                            "model": "ridge",
                            "mae": mae,
                        }
                    )
                if n_labeled == len(target_pool) - 1:
                    break
                candidates = [index for index in target_pool if index not in selected]
                if stage == "v4":
                    score, components = weighted_components(domain, target, selected, candidates, v4_weights, acquisition_weights)
                elif stage == "v6":
                    score, components = weighted_components(domain, target, selected, candidates, v6_weights, acquisition_weights)
                else:
                    v4_score, v4_components = weighted_components(domain, target, selected, candidates, v4_weights, acquisition_weights)
                    v6_score, v6_components = weighted_components(domain, target, selected, candidates, v6_weights, acquisition_weights)
                    score = mix_v4 * v4_score + (1.0 - mix_v4) * v6_score
                    components = {
                        key: mix_v4 * v4_components[key] + (1.0 - mix_v4) * v6_components[key]
                        for key in v4_components
                    }
                chosen_position = max(
                    range(len(candidates)),
                    key=lambda position: (float(score[position]), -domain.rows[candidates[position]].source_order),
                )
                chosen = candidates[chosen_position]
                selected.append(chosen)
                if record_routes:
                    route_rows.append(
                        {
                            "stage": stage,
                            "domain": domain.name,
                            "target": target,
                            "step": n_labeled + 1,
                            "selected_substrate_id": domain.rows[chosen].substrate_id,
                            "selection_phase": "sequential",
                            "selection_score": float(score[chosen_position]),
                            "weighted_novelty": float(components["weighted_novelty"][chosen_position]),
                            "model_disagreement": float(components["model_disagreement"][chosen_position]),
                            "uncertainty": float(components["uncertainty"][chosen_position]),
                            "coverage": float(components["coverage"][chosen_position]),
                        }
                    )
            curve = [
                row
                for row in curve_rows
                if row["stage"] == stage and row["domain"] == domain.name and row["target"] == target and row["model"] == "ridge"
            ]
            curve = sorted(curve, key=lambda row: int(row["n_labeled"]))
            y = np.asarray([float(row["mae"]) for row in curve], dtype=float)
            x = np.asarray([float(row["n_labeled"]) for row in curve], dtype=float)
            reference = float(np.mean(values[np.asarray(target_pool, dtype=int)]))
            if len(y) > 1:
                auc = float(np.trapezoid(y, x) / (x[-1] - x[0]))
                deltas = np.abs(np.diff(y))
                fluctuation = float(np.mean(deltas) / max(float(np.mean(y)), 1e-12))
                max_jump = float(np.max(deltas) / max(reference, 1e-12))
            else:
                auc = float(np.mean(y)) if len(y) else float("nan")
                fluctuation = 0.0
                max_jump = 0.0
            auc_normalized = auc / max(reference, 1e-12)
            cell_metrics.append(
                {
                    "stage": stage,
                    "domain": domain.name,
                    "target": target,
                    "n_curve_points": len(y),
                    "reference_intercept_mae": reference,
                    "auc_mae": auc,
                    "auc_mae_normalized": auc_normalized,
                    "mean_absolute_curve_change_normalized": fluctuation,
                    "largest_curve_jump_normalized": max_jump,
                    "objective": auc_weight * auc_normalized + fluctuation_weight * fluctuation + max_jump_weight * max_jump,
                }
            )
    if not cell_metrics:
        raise ValueError("no domain-target cells were evaluable")
    summary = {
        "objective": float(np.mean([row["objective"] for row in cell_metrics])),
        "mean_auc_mae_normalized": float(np.mean([row["auc_mae_normalized"] for row in cell_metrics])),
        "mean_absolute_curve_change_normalized": float(np.mean([row["mean_absolute_curve_change_normalized"] for row in cell_metrics])),
        "mean_largest_curve_jump_normalized": float(np.mean([row["largest_curve_jump_normalized"] for row in cell_metrics])),
        "cells": float(len(cell_metrics)),
    }
    return summary, cell_metrics, route_rows


def encode_parameters(stage: str, parameters: np.ndarray) -> np.ndarray:
    if stage == "mixed":
        return np.asarray(parameters, dtype=float).reshape(1)
    weights = np.asarray(parameters, dtype=float)
    weights = np.clip(weights, 1e-8, 1.0)
    weights = weights / np.sum(weights)
    return np.log(weights[:-1] / weights[-1])


def decode_parameters(stage: str, encoded: np.ndarray) -> np.ndarray:
    if stage == "mixed":
        return np.asarray([float(np.clip(encoded[0], 0.0, 1.0))])
    # The final simplex component is the log-ratio reference and therefore has
    # an implicit zero logit in the reduced GP coordinate system.
    return simplex_from_logits(np.concatenate([np.asarray(encoded, dtype=float), np.asarray([0.0])]))


def propose_bayesian(
    stage: str,
    observations: Sequence[dict[str, Any]],
    rng: np.random.Generator,
    count: int = 2048,
) -> np.ndarray:
    if stage == "v4":
        dimension = 3
    elif stage == "v6":
        dimension = 5
    else:
        dimension = 1
    if len(observations) < max(6, dimension + 2):
        if stage == "mixed":
            return np.asarray([rng.uniform()], dtype=float)
        return random_weights(rng, dimension)
    encoded = np.asarray([encode_parameters(stage, np.asarray(row["parameters"], dtype=float)) for row in observations], dtype=float)
    y = np.asarray([float(row["objective"]) for row in observations], dtype=float)
    kernel = Matern(length_scale=np.ones(encoded.shape[1]), nu=2.5) + WhiteKernel(noise_level=1e-5)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        model = GaussianProcessRegressor(kernel=kernel, normalize_y=True, random_state=0, n_restarts_optimizer=0)
        model.fit(encoded, y)
    candidates: list[np.ndarray] = []
    best_positions = np.argsort(y)[: min(8, len(y))]
    for _ in range(count):
        if rng.random() < 0.65:
            center = encoded[int(rng.choice(best_positions))]
            candidate = center + rng.normal(0.0, 0.8, size=encoded.shape[1])
        else:
            if stage == "mixed":
                candidate = np.asarray([rng.uniform(0.0, 1.0)])
            else:
                candidate = encode_parameters(stage, random_weights(rng, dimension))
        candidates.append(candidate)
    candidate_matrix = np.asarray(candidates, dtype=float)
    means, standard_deviations = model.predict(candidate_matrix, return_std=True)
    best = float(np.min(y))
    improvement = best - means
    z = improvement / np.maximum(standard_deviations, 1e-12)
    expected_improvement = improvement * norm.cdf(z) + standard_deviations * norm.pdf(z)
    chosen = candidate_matrix[int(np.argmax(expected_improvement))]
    return decode_parameters(stage, chosen)


def same_parameters(first: Sequence[float], second: Sequence[float]) -> bool:
    return bool(np.allclose(np.asarray(first, dtype=float), np.asarray(second, dtype=float), atol=1e-9, rtol=0.0))


def optimize_stage(
    stage: str,
    domains: Sequence[DomainData],
    v4_weights: dict[str, float],
    v6_weights: dict[str, float],
    random_count: int,
    bayes_count: int,
    rng: np.random.Generator,
    objective_config: dict[str, Any],
) -> tuple[dict[str, float] | float, list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    observations: list[dict[str, Any]] = []
    cell_rows: list[dict[str, Any]] = []
    route_rows: list[dict[str, Any]] = []

    def evaluate(parameters: np.ndarray, method: str, iteration: int) -> None:
        if stage == "v4":
            local_v4 = make_block_weights("v4", parameters)
            local_v6 = v6_weights
            mix = 1.0
        elif stage == "v6":
            local_v4 = v4_weights
            local_v6 = make_block_weights("v6", parameters)
            mix = 0.0
        else:
            local_v4 = v4_weights
            local_v6 = v6_weights
            mix = float(parameters[0])
        summary, cells, _ = route_and_curves(domains, stage, local_v4, local_v6, mix, objective_config=objective_config)
        observations.append(
            {
                "stage": stage,
                "method": method,
                "iteration": iteration,
                "parameters": [float(value) for value in parameters],
                "objective": summary["objective"],
                **summary,
            }
        )
        cell_rows.extend(
            {
                "stage": stage,
                "method": method,
                "iteration": iteration,
                "parameters": json.dumps([float(value) for value in parameters]),
                **row,
            }
            for row in cells
        )

    dimension = 3 if stage == "v4" else 5 if stage == "v6" else 1
    for iteration in range(random_count):
        parameters = random_weights(rng, dimension) if dimension > 1 else np.asarray([rng.uniform()], dtype=float)
        evaluate(parameters, "random", iteration)
    for iteration in range(bayes_count):
        parameters = propose_bayesian(stage, observations, rng)
        while any(same_parameters(parameters, row["parameters"]) for row in observations):
            parameters = random_weights(rng, dimension) if dimension > 1 else np.asarray([rng.uniform()], dtype=float)
        evaluate(parameters, "bayesian", iteration)
    best = min(observations, key=lambda row: float(row["objective"]))
    if stage == "v4":
        selected: dict[str, float] | float = make_block_weights("v4", best["parameters"])
    elif stage == "v6":
        selected = make_block_weights("v6", best["parameters"])
    else:
        selected = float(best["parameters"][0])
    return selected, observations, cell_rows, route_rows


def best_observation(observations: Sequence[dict[str, Any]]) -> dict[str, Any]:
    return dict(min(observations, key=lambda row: float(row["objective"])))


def run(args: argparse.Namespace) -> dict[str, Any]:
    config_path = args.config.resolve()
    config = load_config(config_path)
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    domains = load_domains(config, config_path)
    snapshot_inputs(domains, output_dir)
    rng = np.random.default_rng(args.seed)
    objective_config = config.get("objective", DEFAULT_OBJECTIVE)
    v4, v4_trace, v4_cells, _ = optimize_stage(
        "v4", domains, {}, {}, args.random_v4, args.bayes_v4, rng, objective_config
    )
    assert isinstance(v4, dict)
    v6, v6_trace, v6_cells, _ = optimize_stage(
        "v6", domains, v4, {}, args.random_v6, args.bayes_v6, rng, objective_config
    )
    assert isinstance(v6, dict)
    mix, mix_trace, mix_cells, _ = optimize_stage(
        "mixed", domains, v4, v6, args.random_mix, args.bayes_mix, rng, objective_config
    )
    assert isinstance(mix, float)
    traces = v4_trace + v6_trace + mix_trace
    cells = v4_cells + v6_cells + mix_cells
    final_stage_metrics, final_cells, final_routes = route_and_curves(
        domains, "mixed", v4, v6, mix, record_routes=True, objective_config=objective_config
    )
    all_cells = cells + [
        {"method": "selected", "iteration": None, **row}
        for row in final_cells
    ]
    write_csv(output_dir / "results" / "optimization-trace.csv", traces)
    write_csv(output_dir / "results" / "random-search.csv", [row for row in traces if row["method"] == "random"])
    write_csv(output_dir / "results" / "bayesian-search.csv", [row for row in traces if row["method"] == "bayesian"])
    write_csv(output_dir / "results" / "objective-by-cell.csv", all_cells)
    # Recreate selected curves once and retain their full prefix-level data.
    _, _, selected_route_rows = route_and_curves(
        domains, "mixed", v4, v6, mix, record_routes=True, objective_config=objective_config
    )
    # The route function stores curves internally for metrics; produce a compact
    # replay file from the same selected route and cached predictions.
    curve_output: list[dict[str, Any]] = []
    for domain in domains:
        for target in TARGETS:
            pool = domain.target_active_indices(target)
            if len(pool) < 4:
                continue
            selected = baseline.seed_indices(domain.table, pool, "diversity_first", random.Random(0))
            values = domain.target_values(target)
            for n_labeled in range(2, len(pool)):
                test = [index for index in pool if index not in selected]
                predictions = domain.predictions(target, selected, test).get("ridge")
                if predictions is not None and len(predictions):
                    curve_output.append(
                        {
                            "stage": "mixed",
                            "domain": domain.name,
                            "target": target,
                            "n_labeled": n_labeled,
                            "model": "ridge",
                            "mae": float(np.mean(np.abs(values[np.asarray(test)] - predictions))),
                        }
                    )
                if n_labeled < len(pool) - 1:
                    candidates = [index for index in pool if index not in selected]
                    v4_score, v4_components = weighted_components(
                        domain, target, selected, candidates, v4, objective_config.get("acquisition_weights")
                    )
                    v6_score, v6_components = weighted_components(
                        domain, target, selected, candidates, v6, objective_config.get("acquisition_weights")
                    )
                    score = mix * v4_score + (1.0 - mix) * v6_score
                    chosen_position = max(
                        range(len(candidates)),
                        key=lambda position: (float(score[position]), -domain.rows[candidates[position]].source_order),
                    )
                    selected.append(candidates[chosen_position])
    write_csv(output_dir / "results" / "progression-curves.csv", curve_output)
    write_csv(output_dir / "results" / "selected-routes.csv", selected_route_rows)
    equations = {
        "v4": {"feature_group_weights": v4, "objective": best_observation(v4_trace)},
        "v6": {"feature_group_weights": v6, "objective": best_observation(v6_trace)},
        "mixed": {
            "v4_mix_weight": mix,
            "v6_mix_weight": 1.0 - mix,
            "v4_feature_group_weights": v4,
            "v6_feature_group_weights": v6,
            "mixed_feature_group_weights": mixed_block_weights(v4, v6, mix),
            "objective": best_observation(mix_trace),
            "equation": {
                "weighted_novelty": "lambda_v4 * N_v4 + (1 - lambda_v4) * N_v6",
                "acquisition_score": "0.4 * N_mix + 0.4 * (0.5 * N_mix + 0.5 * model_disagreement) + 0.2 * coverage",
                "expanded_acquisition_score": "0.6 * N_mix + 0.2 * model_disagreement + 0.2 * coverage",
            },
        },
    }
    write_json(output_dir / "results" / "best-equations.json", equations)
    source_files = []
    for domain in domains:
        source_files.extend(
            [
                {"path": str(domain.records_path), "sha256": file_sha256(domain.records_path)},
                {"path": str(domain.stage2p_path), "sha256": file_sha256(domain.stage2p_path)},
            ]
        )
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "config_path": str(config_path),
        "seed": args.seed,
        "source_files": source_files,
        "domains": [
            {
                "name": domain.name,
                "input_records": len(domain.rows),
                "active_records": len(domain.active_indices),
                "locked_audit_ids": [domain.rows[index].substrate_id for index in domain.audit_indices],
                "active_ids": domain.active_ids,
                "targets": {target: len(domain.target_active_indices(target)) for target in TARGETS},
            }
            for domain in domains
        ],
        "hierarchy": [
            "optimize V4 feature-group weights",
            "optimize V6 feature-group weights",
            "optimize V4/V6 mixing coefficient with the two previous equations fixed",
        ],
        "versions": VERSION_BLOCKS,
        "search": {
            "v4": {"random": args.random_v4, "bayesian": args.bayes_v4},
            "v6": {"random": args.random_v6, "bayesian": args.bayes_v6},
            "mixed": {"random": args.random_mix, "bayesian": args.bayes_mix},
            "bayesian_method": "Gaussian process with Matern kernel and expected improvement",
            "random_method": "Dirichlet simplex sampling for group weights; uniform sampling for the mixing coefficient",
        },
        "objective_definition": objective_config,
        "selected_equation_metrics": final_stage_metrics,
        "outputs": {
            "scope_snapshot": "data/scope-input-records.jsonl",
            "candidate_metadata": "data/candidate-metadata.csv",
            "stage2p_features": "data/stage2p-features.jsonl",
            "rule_features": "data/rule-features-v6.jsonl",
            "optimization_trace": "results/optimization-trace.csv",
            "objective_by_cell": "results/objective-by-cell.csv",
            "progression_curves": "results/progression-curves.csv",
            "selected_routes": "results/selected-routes.csv",
            "best_equations": "results/best-equations.json",
        },
    }
    write_json(output_dir / "results" / "manifest.json", manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path(__file__).with_name("config.json"))
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parent)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--random-v4", type=int, default=DEFAULT_RANDOM_V4)
    parser.add_argument("--bayes-v4", type=int, default=DEFAULT_BAYES_V4)
    parser.add_argument("--random-v6", type=int, default=DEFAULT_RANDOM_V6)
    parser.add_argument("--bayes-v6", type=int, default=DEFAULT_BAYES_V6)
    parser.add_argument("--random-mix", type=int, default=DEFAULT_RANDOM_MIX)
    parser.add_argument("--bayes-mix", type=int, default=DEFAULT_BAYES_MIX)
    args = parser.parse_args()
    manifest = run(args)
    print(json.dumps(manifest["selected_equation_metrics"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
