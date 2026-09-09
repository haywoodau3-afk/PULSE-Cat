# Results

This section reports the frozen aggregate numerical results for checkpoints
1–9. Individual substrate predictions, every progressive prefix, selection
events, replicate-level values, and pose-array values are retained in the
machine-readable Supporting Information rather than reproduced as prose.

## Dataset assembly and analysis coverage

The frozen analysis comprised two independently curated iron-porphyrin
datasets. The P7 collection contained 41 reaction records. Of these, 39 entered
the progressive-learning input set, 38 had usable ee values, and 39 had usable
isolated-yield values after the recorded exclusions. The CMC-Por collection
contained 50 reaction records, including 33 aryl C–H amination records in the
primary transfer cohort and 17 sulfonyl C–H amination records retained as a
pathway control. The aryl-domain identity ledger contained 13 canonical
substrate pairs shared between P7 and CMC-Por. These overlaps were excluded
from the source set in cold-start transfer calculations.

The consolidated substrate table contained 91 records. Starting-material
SMILES were present for all 91 records. Product SMILES were present for all 50
CMC-Por records and for 12 of the 41 P7 records; the remaining 29 P7 product
mappings were null in the curated source data. Pose-density artifacts comprised
41 P7 and 50 CMC-Por substrate-level records, for 91 numerical/view pairs in
total. The matched overlay analysis contained all 13 canonical aryl pairs.

Eleven representation arms were defined: the no-feature B0 reference, five
two-dimensional arms B1–B5, and five pose-related arms P0–P4. Ten
feature-bearing arms were evaluated in each transfer direction. Five supervised
estimator families were used across the complete study: Ridge regression,
Elastic Net, Tanimoto-k-nearest neighbours, LightGBM, and Gaussian-process
regression.

## Two-dimensional and pose-representation progression

The B1 representation contained six RDKit descriptors; B2 contained 15 RDKit
descriptors; B3, B4, and B5 contained the 15 descriptors plus 128-, 256-, and
1,024-bit radius-2 Morgan fingerprints, respectively. Their total feature
counts were 6, 15, 143, 271, and 1,039. P0 contained 248 pose features, P1
contained 254 features, P2 contained 1,287 features, P3 contained 1,083
features, and P4 contained 1,099 features.

For CMC-Por→P7, the B1 target-only MAE was 12.895 ee points, the target-only
AUC-MAE was 470.723, and the guarded MAE was 12.802. The corresponding B2
values were 12.714, 466.054, and 12.529; B3 values were 11.941, 436.753, and
11.612; B4 values were 12.165, 435.505, and 11.964; and B5 values were 11.815,
424.292, and 11.654. Relative to B1, B5 reduced target-only MAE by 1.079 ee
points, or 8.4%. Across B1–B5, the guarded-minus-target-only MAE differences
were −0.092, −0.185, −0.329, −0.201, and −0.162 ee points, respectively.

For the same CMC-Por→P7 direction, P0 produced a target-only MAE of 19.317,
an AUC-MAE of 695.948, and a guarded MAE of 16.528. P1 produced 19.355,
697.280, and 16.425; P2 produced 16.953, 606.210, and 14.457; P3 produced
11.276, 397.809, and 10.973; and P4 produced 11.061, 390.619, and 10.741.
The guarded-minus-target-only MAE differences for P0–P4 were −2.789, −2.930,
−2.496, −0.303, and −0.320 ee points. P4 had the lowest target-only MAE,
guarded MAE, and target-only AUC-MAE in this direction.

For P7→CMC-Por, B1 gave a target-only MAE of 14.243, an AUC-MAE of 430.423,
and a guarded MAE of 13.053. B2 gave 14.100, 426.091, and 12.955; B3 gave
12.563, 379.429, and 12.083; B4 gave 12.578, 378.166, and 11.781; and B5 gave
12.234, 372.493, and 11.702. Relative to B1, B5 reduced target-only MAE by
2.009 ee points, or 14.1%. The guarded-minus-target-only differences for
B1–B5 were −1.190, −1.144, −0.480, −0.797, and −0.532 ee points.

For P7→CMC-Por, P0 produced a target-only MAE of 18.326, an AUC-MAE of
551.216, and a guarded MAE of 15.578. P1 produced 20.412, 612.226, and
18.015; P2 produced 17.659, 533.867, and 14.239; P3 produced 12.205, 373.801,
and 11.480; and P4 produced 12.208, 373.214, and 11.509. The corresponding
guarded-minus-target-only differences were −2.748, −2.397, −3.420, −0.725,
and −0.699 ee points. P3 had the lowest target-only and guarded MAE in this
direction, while B5 had the lowest target-only AUC-MAE.

## Independent P7 held-out model results

The independent P7 held-out comparison used 39 modelable ee records and four
estimators. The structure-only matrix contained 547 features. The
structure-plus-pose matrix contained 1,241 features. Results below report MAE
with its 95% Bayesian-bootstrap interval, RMSE with its 95% interval, R², and
the fractions within 10 and 20 ee points.

In target-held-out validation, structure-only Elastic Net gave MAE 15.436
(95% interval 11.977–20.498), RMSE 20.677 (14.853–29.001), R² −0.065,
38.5% within 10 ee points, and 79.5% within 20 ee points. Structure-only
Gaussian process gave MAE 16.257 (13.160–21.064), RMSE 20.640
(15.223–29.127), R² −0.061, 17.9% within 10, and 84.6% within 20.
Structure-only LightGBM gave MAE 12.236 (8.402–17.533), RMSE 19.124
(13.071–26.993), R² 0.089, 61.5% within 10, and 79.5% within 20.
Structure-only Ridge gave MAE 14.160 (10.396–19.506), RMSE 20.487
(14.090–29.271), R² −0.046, 53.8% within 10, and 79.5% within 20.

In the same target-held-out validation, structure-plus-pose Elastic Net gave
MAE 11.649 (7.765–17.925), RMSE 20.154 (12.042–30.726), R² −0.012,
66.7% within 10, and 84.6% within 20. Its MAE difference from structure-only
Elastic Net was −3.787 ee points. Structure-plus-pose Gaussian process gave
MAE 16.257 (13.160–21.064), RMSE 20.640 (15.223–29.127), R² −0.061,
17.9% within 10, and 84.6% within 20; its MAE difference was +0.0001.
Structure-plus-pose LightGBM gave MAE 13.369 (9.378–19.117), RMSE 20.617
(13.895–29.937), R² −0.059, 53.8% within 10, and 76.9% within 20; its MAE
difference was +1.133. Structure-plus-pose Ridge gave MAE 15.434
(10.951–21.735), RMSE 23.156 (16.040–32.560), R² −0.336, 53.8% within 10,
and 74.4% within 20; its MAE difference was +1.274.

In family-held-out validation, structure-only Elastic Net gave MAE 14.221
(10.987–19.153), RMSE 19.301 (13.707–27.768), R² 0.072, 43.6% within 10,
and 82.1% within 20. Structure-only Gaussian process gave MAE 16.862
(13.752–21.679), RMSE 21.109 (15.874–29.447), R² −0.110, 20.5% within 10,
and 79.5% within 20. Structure-only LightGBM gave MAE 12.675
(8.640–18.538), RMSE 20.271 (13.440–30.056), R² −0.024, 64.1% within 10,
and 74.4% within 20. Structure-only Ridge gave MAE 15.611
(12.079–20.590), RMSE 20.673 (15.227–28.729), R² −0.065, 33.3% within 10,
and 79.5% within 20.

For the family-held-out structure-plus-pose models, Elastic Net gave MAE
12.390 (8.610–17.975), RMSE 19.546 (12.844–29.335), R² 0.048, 61.5% within
10, and 79.5% within 20. Its MAE difference from structure-only Elastic Net
was −1.831 ee points. Gaussian process gave MAE 16.862 (13.752–21.679), RMSE
21.109 (15.874–29.447), R² −0.110, 20.5% within 10, and 79.5% within 20;
its MAE difference was less than 0.001. LightGBM gave MAE 16.313
(12.100–22.243), RMSE 23.033 (16.531–32.434), R² −0.322, 48.7% within 10,
and 69.2% within 20; its MAE difference was +3.637. Ridge gave MAE 17.440
(13.686–22.541), RMSE 22.435 (17.128–30.687), R² −0.254, 30.8% within 10,
and 61.5% within 20; its MAE difference was +1.829.

The Stage 2pp occupancy/flexibility branch was evaluated on 39 P7 records.
Stage 2p with Elastic Net gave MAE 12.533, RMSE 18.546, and 34/39 predictions
within 20 ee points. Stage 2p plus Stage 2pp gave 21.454, 29.667, and 25/39;
Stage 2-alt gave 14.986, 20.645, and 30/39; Stage 2-alt plus Stage 2pp gave
15.111, 21.073, and 31/39; and Stage 2pp alone gave 16.021, 21.950, and 28/39.
The paired Stage 2p-to-augmented MAE difference was +8.921 ee points, with a
95% interval of +4.749 to +13.659. The Stage 2-alt-to-augmented difference was
+0.126, with an interval of −2.641 to +2.738. Neither augmentation met the
predeclared 1-ee-point improvement criterion.

The separate Stage 2p publication-readiness benchmark used 38 fixed-catalyst
P7 ee records. Elastic Net produced MAE 9.627, RMSE 12.991, 25/38 predictions
within 10 ee points, 28/38 within 15, and 32/38 within 20. Precision at the
80-ee threshold was 0.875. The empirical interval coverages were 0.816 at the
nominal 80% level and 0.974 at the nominal 95% level.

## Progressive rule-feature versions

Seven hard-rule feature definitions, V0–V6, were retained. The initial
uncertainty–diversity acquisition comparison evaluated V0–V3 with 10 random
replicates. Relative to V0, the V1 Ridge AUC-MAE changed from 337.18 to 286.95
for P7 ee, from 554.16 to 498.95 for P7 isolated yield, from 307.50 to 293.87
for CMC-Por ee, and from 512.50 to 465.43 for CMC-Por isolated yield. The
corresponding relative changes were −14.9%, −10.0%, −4.4%, and −9.2%.

The P7 V0, V4, and V6 prediction matrices contained 1,039, 1,196, and 1,236
columns, respectively, and were evaluated by leave-one-out prediction on 38
records. For V0, Ridge, Elastic Net, and Tanimoto-kNN gave MAE/RMSE/Spearman
values of 8.449/12.301/0.571, 8.438/12.266/0.569, and
8.115/11.868/0.521. For V4, the corresponding values were
7.746/10.902/0.531, 7.709/10.881/0.519, and 8.115/11.868/0.521. For V6,
they were 7.749/10.896/0.519, 7.633/10.799/0.535, and
8.115/11.868/0.521. Five unlabelled P7 candidates were scored with V0, V4,
and V6; no experimental labels were available for those five records.

The interim rule-BDE calibration joined 119 candidate-site pairs from 38 P7
substrates to GFN2-xTB/ALPB(ether) calculations. Raw rule values gave MAE
24.927 kcal mol−1, RMSE 25.314 kcal mol−1, bias −24.881 kcal mol−1, and
Pearson correlation 0.803. Exact within-substrate rank agreement was 45.4%,
and 84.0% of sites were within one rank. The leave-one-substrate-out affine
correction gave MAE 2.713 kcal mol−1, RMSE 4.783 kcal mol−1, bias 0.004
kcal mol−1, and Pearson correlation 0.791. The in-sample affine fit used an
intercept of 22.931 and slope of 1.0218 and gave MAE 2.677 and RMSE 4.658
kcal mol−1. A 12-site panel was selected for a higher-level reference
calculation; no higher-level reference results were available.

## Independent progressive learning

Five substrate-selection policies were evaluated: historical order,
diversity-first, performance-first, uncertainty–diversity, and random order.
Three estimators were evaluated on the deterministic routes. The random route
included Ridge and Tanimoto-k-nearest neighbours and was averaged over 500
replicates. P7 ee curves ended at 37 labelled substrates, P7 yield curves at
38, and CMC-Por aryl ee and yield curves at 25.

For P7 ee, the diversity-first Elastic Net, Ridge, and Tanimoto-kNN curves had
final-prefix MAE/AUC-MAE/`n90` values of 4.454/343.044/4,
3.772/391.662/24, and 1.215/368.284/19, respectively. Historical-order values
were 8.838/741.152/not reached, 9.719/757.662/not reached, and
3.969/601.044/37. Performance-first values were 16.511/403.781/not reached,
18.224/403.093/7, and 27.543/525.131/not reached. Random-route Ridge and
Tanimoto-kNN values were 8.122/355.527/29 and 8.344/337.493/27.
Uncertainty–diversity Elastic Net, Ridge, and Tanimoto-kNN values were
4.454/325.119/16, 3.772/337.181/16, and 1.215/306.116/17.

For CMC-Por aryl ee, diversity-first Elastic Net, Ridge, and Tanimoto-kNN gave
4.111/217.781/13, 4.141/221.203/14, and 2.089/171.515/13 for final-prefix
MAE/AUC-MAE/`n90`. Historical-order values were 5.352/292.463/12,
8.773/297.250/16, and 1.482/238.721/7. Performance-first values were
5.352/336.989/23, 8.773/331.021/23, and 1.482/187.666/6. Random Ridge and
Tanimoto-kNN values were 10.644/274.596/19 and 9.781/225.759/12.
Uncertainty–diversity values were 4.111/193.940/6, 4.141/195.890/8, and
2.089/175.443/14 for Elastic Net, Ridge, and Tanimoto-kNN, respectively.

In the dedicated historical-versus-AI route-comparison artifact, the mean
prefix MAE for P7 Ridge was 9.684 for
uncertainty–diversity, 11.197 for diversity-first, 11.261 for random order,
11.716 for performance-first, and 21.672 for historical order. The associated
Ridge AUC-MAE values were 348.624, 403.104, 405.388, 421.761, and 780.199.
For CMC-Por aryl, the Ridge mean prefix MAE values were 8.787 for
uncertainty–diversity, 9.842 for diversity-first, 13.155 for historical order,
13.654 for random order, and 14.514 for performance-first; the corresponding
AUC-MAE values were 210.884, 236.196, 315.717, 327.707, and 348.330.

For P7 isolated yield, diversity-first Elastic Net, Ridge, and Tanimoto-kNN
gave final-prefix MAE/AUC-MAE/`n90` values of 15.999/561.248/2,
16.006/570.357/2, and 0.509/469.261/12. Historical-order values were
22.180/908.899/2, 23.917/913.166/2, and 16.019/633.651/37.
Performance-first values were 15.999/657.697/2, 16.006/666.479/2, and
0.509/513.326/15. Random Ridge and Tanimoto-kNN values were
18.447/639.424/4 and 13.461/484.752/26. Uncertainty–diversity Elastic Net,
Ridge, and Tanimoto-kNN values were 15.999/547.182/2, 16.007/554.164/2,
and 0.509/452.942/15.

For CMC-Por aryl isolated yield, diversity-first Elastic Net, Ridge, and
Tanimoto-kNN gave 35.582/453.058/6, 35.032/467.224/6, and
26.904/354.284/2 for final-prefix MAE/AUC-MAE/`n90`. Historical-order values
were 8.173/457.616/6, 10.244/474.511/6, and 3.045/398.990/4.
Performance-first values were 8.173/613.981/9, 10.244/616.732/9, and
6.276/312.254/2. Random Ridge and Tanimoto-kNN values were
21.604/518.475/24 and 18.131/390.508/2. Uncertainty–diversity Elastic Net,
Ridge, and Tanimoto-kNN values were 35.582/467.958/6, 35.032/479.375/6,
and 26.904/368.317/2.

## Guarded transfer, route replication, and pose controls

For ee under the fixed reciprocal replay, the B5 guarded model reduced MAE
from 11.815 to 11.654 for CMC-Por→P7 and from 12.234 to 11.702 for
P7→CMC-Por. P3 reduced MAE from 11.276 to 10.973 and from 12.205 to 11.480,
respectively. P4 reduced MAE from 11.061 to 10.741 and from 12.208 to 11.509.
The scored prefix counts were 37 for CMC-Por→P7 and 31 for P7→CMC-Por.

Across 500 randomized routes, B5 produced mean guarded and target-only AUC-MAE
values of 446.054 and 453.560 for CMC-Por→P7, and 386.411 and 397.759 for
P7→CMC-Por. P3 produced 432.871 and 442.672 for CMC-Por→P7, and 373.060 and
385.327 for P7→CMC-Por. P4 produced 426.875 and 440.725 for CMC-Por→P7,
and 380.428 and 393.896 for P7→CMC-Por.

The randomized-route guarded-minus-target MAE deltas were −0.230 for B5,
−0.311 for P3, and −0.417 for P4 in CMC-Por→P7; their 95% bootstrap intervals
were −0.254 to −0.205, −0.345 to −0.279, and −0.451 to −0.382. In
P7→CMC-Por, the deltas were −0.399, −0.460, and −0.501, with intervals of
−0.443 to −0.356, −0.499 to −0.421, and −0.533 to −0.466. The associated
guarded-minus-target AUC-MAE deltas were −7.505 (−8.331 to −6.633), −9.803
(−11.007 to −8.691), and −13.838 (−15.057 to −12.671) for CMC-Por→P7, and
−11.344 (−12.627 to −10.089), −12.266 (−13.399 to −11.207), and −13.453
(−14.366 to −12.505) for P7→CMC-Por.

In matched-route pose-versus-B5 bootstraps, P3 changed MAE by −0.342 ee points
(95% interval −0.400 to −0.282) and AUC-MAE by −13.191 (−15.094 to −11.303)
for CMC-Por→P7. Its P7→CMC-Por changes were −0.347 (−0.415 to −0.280) and
−13.373 (−15.191 to −11.682). P4 changed MAE and AUC-MAE by −0.489
(−0.550 to −0.432) and −19.183 (−21.147 to −17.225) for CMC-Por→P7, and
by −0.099 (−0.177 to −0.020) and −6.014 (−8.035 to −3.933) for
P7→CMC-Por.

In the scaffold-held-out replay, B5 used 12 scaffold groups and 636 predictions
for P7→CMC-Por and produced target-only, combined, and guarded MAEs of 24.103,
18.223, and 18.382. In the reciprocal direction, B5 used 22 groups and 1,202
predictions and produced 14.816, 13.267, and 10.643. P3 produced 20.968,
19.028, and 18.073 for P7→CMC-Por and 14.541, 12.981, and 11.289 for
CMC-Por→P7. P4 produced 22.236, 19.402, and 18.531 for P7→CMC-Por and
14.240, 11.920, and 10.215 for CMC-Por→P7.

The scaffold-bootstrap guarded-minus-target mean was −2.208 ee points for
P7→CMC-Por, with a 95% interval of −4.567 to −0.644. The reciprocal mean was
−4.596, with an interval of −7.848 to −1.888. The combined-minus-target means
were −1.503 (−4.928 to 1.878) and −2.875 (−6.698 to 0.433), while the
active-source-minus-target means were +1.376 (−3.388 to 6.274) and +1.169
(−6.415 to 7.517).

In scaffold-level incremental pose bootstraps, P3 changed target-only and
guarded MAE relative to B5 by −2.171 (−4.603 to −0.012) and −1.826
(−3.968 to 0.272) for P7→CMC-Por, and by −0.133 (−1.837 to 1.456) and
+0.666 (−0.589 to 1.856) for CMC-Por→P7. P4 changed target-only and guarded
MAE by −0.914 (−2.900 to 0.848) and −1.804 (−5.290 to 1.543) for
P7→CMC-Por, and by −0.778 (−2.988 to 1.129) and −0.942
(−3.310 to 1.036) for CMC-Por→P7.

The raw 248-feature P2 pose concatenation produced guarded MAEs of 14.457 for
CMC-Por→P7 and 14.239 for P7→CMC-Por. The P2 permuted-pose control produced
13.793 and 17.289, and the P2 random-feature control produced 12.162 and
14.468. For P3, the observed guarded MAEs were 10.973 and 11.480; permuted-P3
values were 11.623 and 12.373, and random-P3 values were 11.891 and 13.357.
The B5 guarded reference values were 11.654 and 11.702.

For isolated-yield transfer, B5 target-only and guarded MAEs were 13.762 and
13.537 for CMC-Por→P7, and 16.194 and 15.675 for P7→CMC-Por. P3 values were
15.377 and 14.903, and 17.367 and 16.464. P4 values were 15.216 and 14.503,
and 18.473 and 17.109. The isolated-yield prefix counts were 38 and 31,
respectively. The target-only AUC-MAE values for B5, P3, and P4 were 502.544,
559.533, and 553.847 for CMC-Por→P7, and 489.654, 536.040, and 570.645 for
P7→CMC-Por.

The prespecified transfer criterion required a reduction of at least 10% in
early-prefix AUC-MAE together with preservation of the full curve and the
specified negative-transfer controls. This criterion was not met in both
directions.

Feature assembly times ranged from 0.0164 to 0.0166 s per recorded CMC-Por
arm and from 0.0201 to 0.0208 s per recorded P7 arm. Peak resident memory in
the resource ledger was 459,112,448 bytes for every recorded B1, B5, P0, P2,
P3, and P4 feature assembly.

## Pose-density and overlay outputs

Stage 2p produced 248 pose features per substrate. Stage 2pp produced 655
occupancy and flexibility features per substrate. Each retained substrate pose
ensemble contained 200 poses divided into 100 low-UFF and 100 high-UFF valid
poses. The complete two-system density collection contained 91 substrate-level
NPZ arrays and 91 corresponding SVG views. Thirteen paired-substrate overlays
were assembled from the canonical P7/CMC-Por overlap ledger. These outputs
were calculated in reaction-centered coordinate frames and contained low-UFF,
high-UFF, combined, and difference fields.

## Generative substrate search

The generative run used five fixed seeds and produced 10,112 strings per seed,
for 50,560 raw strings. The original requested total was 50,000; all 560 excess
batch records were retained. Canonicalization produced 9,184 unique structures,
and 41,269 records were marked as duplicates in the frozen summary. The
structural-contract funnel retained 563 candidates, of which 483 were inside
the applicability-domain threshold of 0.35.

The deterministic enumeration comparator used the same 50,560-record budget
and a vocabulary of 38 fragments. It produced 25,955 unique canonical
structures and 24,605 duplicates. The structural contract retained 18,545
candidates, and 18,350 were inside the applicability domain.

For the 500-candidate comparison samples, the generator had mean pairwise
Tanimoto similarity 0.312, mean pairwise distance 0.688, mean maximum
similarity to the 91-reference set 0.487, and novelty proxy 0.513. The
enumeration sample had mean pairwise Tanimoto similarity 0.412, mean pairwise
distance 0.588, mean maximum reference similarity 0.457, and novelty proxy
0.543.

The frozen development Morgan–Ridge predictor scored 483 generator candidates
and 18,223 enumerated candidates. Generator predictions had mean 56.017,
standard deviation 7.459, median 55.637, 90th percentile 64.934, maximum
83.302, and top-10 mean 69.411 ee. Enumeration predictions had mean 75.305,
standard deviation 6.569, median 75.824, 90th percentile 83.280, maximum
96.452, and top-10 mean 85.806 ee.

The 483 in-domain generator candidates were assigned to five morphology
classes: 192 heteroatom-rich, 117 flexible sp3-rich, 113 fused or polycyclic,
34 diaryl or bicyclic, and 27 simple aryl-tether candidates. Round-robin
morphology balancing produced a 16-member intermediate panel. The final frozen
proposal files contained a sealed 16-member computational panel divided into
an eight-member copilot branch and an eight-member comparator branch. Each
branch contained four round-A and four round-B candidates. No prospective
experimental outcomes were present in the frozen candidate records.

## Artifact inventory and checkpoint boundary

The supporting-data deposit contained 30,118 non-XYZ scientific files totaling
567,855,166 bytes. The file types included 29,140 SDF conformers, 116 NPZ
arrays, 231 SVG files, 122 CSV files, 49 JSONL streams, 328 JSON files, 14
SMILES streams, 12 MOL files, 36 logs, and one model checkpoint. SHA-256 and
byte-size validation returned zero missing files and zero hash mismatches.

The results above cover frozen checkpoints 1–9. No third-system catalyst
records, reference geometry, pose features, or experimental labels were
available for checkpoint 10; no third-system result was calculated.
