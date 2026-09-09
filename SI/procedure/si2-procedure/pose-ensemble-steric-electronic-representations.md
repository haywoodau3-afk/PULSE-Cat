# Probability-weighted steric–electronic pose representations

_Research and development note, 2026-09-07_

## Decision

The best next representation is a **Boltzmann-weighted, reaction-frame steric–electronic pose field**. For each catalyst–substrate pose, it should encode:

1. steric occupancy and free volume around the Fe–nitrene attack corridor;
2. pose-specific electrostatics, polarization, dispersion, and local bond/reactivity descriptors from GFN2-xTB;
3. the pose's probability within a deduplicated, consistently scored low-energy ensemble; and
4. the weighted probability that the pose is geometrically ready to react, including a signed pro-R/pro-S or attack-face contrast where that assignment is available without using the outcome label.

This is a new combination relative to the current repository features, which mostly summarize geometric distributions uniformly or compare selected low- and high-energy buckets. It is not yet an empirical result. Its value must be established by the ablations and family-held-out tests below.

The most important correction is conceptual: **the existing highest-energy MMFF94 poses are not probable conformers**. Under a physical Boltzmann model, their weights should normally be negligible. They remain useful as a separately labelled stress/accessibility set, but should not be mixed into an equilibrium ensemble or described as thermodynamic probabilities.

## Why this is the leading candidate

There is unusually direct primary evidence for all parts of the proposal:

- Average Steric Occupancy (ASO) showed that aligned, conformer-aware 3D steric occupancy can support out-of-sample enantioselectivity prediction and catalyst discovery. The original study combined ASO with electronic descriptors; a later primary study extended ASO and Average Electronic Indicator Fields (AEIF) to transition-metal catalysts, and the authors' `molli` implementation supports explicit conformer weights. [Zahrt et al., *Science* 2019](https://doi.org/10.1126/science.aau5631); [Zahrt et al., *React. Chem. Eng.* 2021](https://doi.org/10.1039/D1RE00013F); [official `molli` ASO/AEIF documentation](https://molli.readthedocs.io/en/v1.3.0/zenodo/06-gbca-calculation-vis/006-calc.html).
- Boltzmann-weighted Sterimol (`wSterimol`) was developed specifically because a single geometry can misrepresent flexible substituents; the conformer range also exposes a source of prediction uncertainty. [Brethomé et al., *ACS Catal.* 2019](https://doi.org/10.1021/acscatal.8b04043).
- A 2026 sparse-data enantioselectivity study computed conformer ensembles of mechanistically relevant intermediates/transition states, extracted 189 geometric/steric and 75 electronic descriptors, and retained lowest-energy, minimum, maximum, and Boltzmann-weighted values. The study reports that a three-parameter, mechanistically relevant model reached average adjusted \(R^2=0.83\) and mean test RMSE \(0.18\pm0.02\) kcal mol\(^{-1}\) in its benchmark, and later demonstrated prospective ligand improvement. This supports the descriptor strategy, not an expectation that the same accuracy will transfer here. [Estrada et al., *Nature* 2026](https://www.nature.com/articles/s41586-026-10239-7).
- GFN2-xTB supplies atomic charges, coordination numbers, atomic polarizabilities and dispersion coefficients, Wiberg bond orders, molecular multipoles, and orbital gaps from an XYZ geometry. Its Hamiltonian includes anisotropic multipole electrostatics and self-consistent charge-dependent D4 dispersion. [Bannwarth et al., *JCTC* 2019](https://doi.org/10.1021/acs.jctc.8b01176); [official xTB property documentation](https://xtb-docs.readthedocs.io/en/latest/properties.html).
- CREST defines and samples low-energy conformer/rotamer ensembles; its documentation gives the normalized Boltzmann population explicitly. CENSO provides staged higher-level refinement, solvation, thermal corrections, and ensemble sorting. [Pracht et al., *J. Chem. Phys.* 2024](https://doi.org/10.1063/5.0197592); [official CREST ensemble documentation](https://crest-lab.github.io/crest-docs/page/overview/context.html); [Grimme et al., *JPCA* 2021](https://doi.org/10.1021/acs.jpca.1c00971).
- Multi-conformer learning can improve molecular and reaction prediction, but published benchmarks use far more labels than this project. MARCEL reports improvements over single-conformer 3D models in 48 of 54 model/task comparisons, while its datasets contain hundreds to tens of thousands of systems. That supports ensemble information but argues against a new high-capacity 3D neural network at the present sample size. [Zhu et al., ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/hash/7eb6233e02f7d9efbb84acd839a996fb-Abstract-Conference.html).

## Current evidence boundary in this repository

The existing target-holdout ee benchmark gives mixed evidence for pose features:

| Comparison | Best structure-only | Best structure + pose | Interpretation |
| --- | ---: | ---: | --- |
| Full-scope MAE | 12.236 ee points (LightGBM) | 11.649 (Elastic Net) | 0.587-point improvement |
| Full-scope \(R^2\) | 0.089 | -0.012 | worse variance explanation despite lower MAE |
| Family-held-out MAE | 12.675 (LightGBM) | 12.390 (Elastic Net) | 0.285-point improvement |
| Family-held-out \(R^2\) | -0.024 | 0.048 | small improvement, still weak |

These values come from the persisted `data/jacs_2025/stage2/reports` artifacts. They are not new calculations. They show that geometry can help slightly, but not yet significantly or consistently. The Stage 3 seed experiment is also a warning: adding constrained-xTB reference/shell features increased MAE from 14.554 to 22.019 on 12 records. More computed features are therefore not enough; the next block must be compact, pose-local, probability-aware, and validated as a block.

## Proposed representation: BW-RPSE

Working name: **Boltzmann-Weighted Reaction-frame Pose Steric–Electronic representation (BW-RPSE)**.

### 1. Deterministic reaction frame

Use the frozen catalyst core to define one signed frame for every pose:

- origin: nitrene N for attack-corridor features, with a second origin at Fe for pocket features;
- \(\hat z\): Fe \(\rightarrow\) nitrene-N;
- \(\hat x\): projection of a fixed, mapped porphyrin-core vector onto the plane perpendicular to \(\hat z\);
- \(\hat y=\hat z\times\hat x\).

This preserves chemically meaningful directionality and chirality. A global rotation or translation of the XYZ file must not change any descriptor. Reflection should preserve scalar occupancy but reverse explicitly signed attack-face features.

### 2. Pose-level steric channels

Prefer 30–80 predeclared regional summaries over thousands of raw voxels:

- substrate occupancy and free volume in radial shells crossed with quadrants/octants;
- occupancy in a cylinder or cone around the N···H–C attack corridor;
- closest-contact distance, van der Waals overlap, clash count, and smooth overlap penalty;
- percent buried volume at several fixed radii, local SASA/visible volume, and buried Sterimol along the attack axis;
- signed upper/lower and left/right occupancy contrasts for facial discrimination.

A smooth steric field for pose \(i\) can be written

\[
\rho_i^{\mathrm{steric}}(\mathbf r)
=\sum_{a\in\mathrm{substrate}} v_a
\exp\left[-\frac{\lVert\mathbf r-\mathbf r_{ia}\rVert^2}{2\sigma^2}\right],
\]

where \(v_a\) is a fixed van der Waals volume/radius-derived weight. Integrate this field over fixed regions rather than learning arbitrary voxels. ASO is the discrete occupancy analogue; SOAP provides a primary-source precedent for Gaussian-smoothed atomic-density representations that are invariant when converted to an appropriate power spectrum. [Bartók et al., *Phys. Rev. B* 2013](https://doi.org/10.1103/PhysRevB.87.184115).

### 3. Pose-level electronic and interaction channels

Run a consistent GFN2-xTB calculation for every usable assembly pose and retain:

- atomic charges \(q_a\), atomic polarizabilities \(\alpha_a\), and \(C_{6,a}\) coefficients;
- charge and spin-density values on Fe, nitrene N, candidate C, transferred H, and atoms in fixed local shells;
- Wiberg C–H, Fe–N, and relevant N···C bond-order proxies;
- total dipole and its projection onto the Fe–N and N···H axes;
- HOMO, LUMO, gap, and optional condensed Fukui indices for the substrate or consistently defined assembly fragment;
- frozen-geometry interaction energy, with deformation kept separate:

\[
\Delta E_{\mathrm{int},i}
=E_{CS,i}-E_{C,i}^{*}-E_{S,i}^{*}.
\]

Here the starred monomers use the geometry they have in complex \(i\). If relaxed monomers are also calculated, report deformation energy separately rather than folding it silently into interaction energy.

Regional electronic fields mirror the steric regions:

\[
\phi_i(\mathbf r_g)=\sum_a\frac{q_{ia}}
{\sqrt{\lVert\mathbf r_g-\mathbf r_{ia}\rVert^2+\epsilon^2}},
\qquad
D_i(\mathbf r_g)=\sum_a\frac{C_{6,ia}}{(\lVert\mathbf r_g-\mathbf r_{ia}\rVert^2+\epsilon^2)^3}.
\]

Use a documented damping function before treating \(D_i\) as an energetic dispersion proxy. Without damping it is only a descriptor. GFN2-xTB itself is the preferred source of a physical dispersion energy.

### 4. Probabilities and ensemble summaries

For deduplicated conformer/basin \(i\) at the experimental temperature \(T\), use

\[
p_i(T)=\frac{g_i\exp[-(G_i-G_{\min})/(RT)]}
{\sum_j g_j\exp[-(G_j-G_{\min})/(RT)]}.
\]

Set degeneracy \(g_i=1\) unless clustering/sampling provides a defensible basin degeneracy. Duplicate generator outputs must not create extra probability mass.

For each scalar or regional pose descriptor \(f_i\), persist

\[
\mu_f=\sum_i p_i f_i,\qquad
\sigma_f^2=\sum_i p_i(f_i-\mu_f)^2,
\]

plus weighted q10/q50/q90, the lowest-free-energy value, \(p_{\max}\), and the effective ensemble size

\[
N_{\mathrm{eff}}=\exp\left(-\sum_i p_i\ln p_i\right).
\]

The minimum and maximum may remain diagnostics, but should not dominate the model: they are sensitive to one bad geometry.

If only constrained GFN2-xTB electronic energies are available, call \(p_i\) **quasi-Boltzmann plausibility weights**, not conformer populations. Test at the reaction temperature and at \(T\pm25\) K, and propagate energy uncertainty by repeatedly perturbing \(\Delta G_i\) by, for example, 0.5 and 1.0 kcal mol\(^{-1}\). CREST's own documentation notes that observable ensemble averages require the thermally accessible low-energy minima, and CENSO exists to improve the energetic/free-energy ranking.

### 5. Probability of a reaction-ready pose

Define a soft, predeclared near-attack gate \(s_i\in[0,1]\) from the N···H distance, N···H–C angle, approach-face orientation, and clash penalty. For example,

\[
s_i=\operatorname{sigmoid}\!\left(\frac{d_0-d_{N\cdots H,i}}{\tau_d}\right)
\operatorname{sigmoid}\!\left(\frac{\theta_i-\theta_0}{\tau_\theta}\right)
\operatorname{sigmoid}\!\left(\frac{c_0-c_i}{\tau_c}\right).
\]

Then

\[
P_{\mathrm{ready}}=\sum_i p_i s_i.
\]

When a label-free geometric rule can assign attack faces,

\[
A_{\mathrm{face}}=P_R-P_S,\qquad
\Delta G_{\mathrm{access}}=-RT\ln\frac{P_R+\varepsilon}{P_S+\varepsilon}.
\]

These are **pose-accessibility probabilities**, not product probabilities. Under Curtin–Hammett conditions, product ratios are governed by competing transition-state free energies, not ground-state conformer populations alone. [IUPAC Gold Book, Curtin–Hammett principle](https://doi.org/10.1351/goldbook.C01480).

The eventual mechanistic tier, if face-specific barriers can be computed consistently, is

\[
k_e\propto\sum_i p_i\exp[-\Delta G_{i,e}^{\ddagger}/(RT)],\quad e\in\{R,S\},
\]

\[
\Delta\Delta G_{\mathrm{eff}}^{\ddagger}=-RT\ln(k_R/k_S),\qquad
ee_{\mathrm{pred}}=100\frac{k_R-k_S}{k_R+k_S}.
\]

This tier should wait: transition-state ensemble predictions are very sensitive to incomplete pathway enumeration, duplicates, and inconsistent filtering. [Laplaza et al., *J. Phys. Chem. Lett.* 2024](https://doi.org/10.1021/acs.jpclett.4c01657); [Laplaza et al., *Chem. Sci.* 2022](https://doi.org/10.1039/D2SC01714H).

## What to do with the retained low- and high-energy coordinates

1. **Deduplicate first.** Cluster within each substrate using symmetry-aware heavy-atom RMSD plus a reaction-pocket interaction fingerprint. Weight clusters, not raw repeated embeddings.
2. **Rerank all retained poses consistently.** Use constrained GFN2-xTB/ALPB ether with fixed charge, spin, solvent, and constraint policy. The same composition makes within-substrate relative total energies meaningful, subject to the method limitations.
3. **Physical pilot:** use only valid low-energy minima inside a conservative energy window for quasi-Boltzmann summaries.
4. **Stress arm:** keep the current high-energy poses separate and summarize them uniformly as steric failure/accessibility counterfactuals. Do not give them equilibrium population merely because they were deliberately retained.
5. **Production ensemble:** regenerate or recover a representative low-energy ensemble rather than retaining only the 100 lowest and 100 highest of a pool. CREST is preferable because the present selection omits the middle of the energy distribution and is not a probability sample.
6. **Higher-confidence subset:** use CENSO or a small DFT single-point/thermal-correction ladder on representative cluster medoids to measure whether population ordering is stable.

For transition-metal ensembles, energy ranking deserves extra caution; TMCONF40 found conformer energetics of transition-metal complexes challenging and recommends conservative post-processing. [Pracht et al., *PCCP* 2021](https://doi.org/10.1039/D0CP04696E).

## Ranked development plan

| Rank | Development | Expected value | Cost/risk |
| ---: | --- | --- | --- |
| 1 | Compact reaction-frame steric occupancy + xTB charge/polarizability/dispersion fields, quasi-Boltzmann mean/variance/tails, \(N_{\mathrm{eff}}\), and \(P_{\mathrm{ready}}\) | Best match to XYZ, reaction geometry, probability requirement, and small-data regime | Moderate calculation; main risk is invalid energy ranking |
| 2 | Add %Vbur/Sterimol/SASA and explicit \(\Delta E_{\mathrm{int}}\)/deformation blocks | Fast, interpretable check of whether sterics or electronics drive any gain | Descriptor proliferation unless capped |
| 3 | CENSO/DFT refinement of representative cluster medoids | Tests whether weighting is robust enough to call physical | Requires ORCA/Turbomole and much more compute |
| 4 | SOAP/MBTR kernel mean embedding of the weighted pose distribution | More expressive invariant representation | Too many degrees of freedom for ~39 labels unless strongly compressed/frozen |
| 5 | Multi-conformer E(3)-invariant neural/set model or face-specific TS ensemble | Potentially highest ceiling with more data | Defer: current label count and uncertain pose physics make overfitting likely |

The recommended first model remains Elastic Net/ridge or a low-dimensional Gaussian process. A neural pose encoder should not be the first test.

## Feasibility and dependencies

The repository already contains the essential executables and Python stack:

- `.chem-env/bin/xtb`: xTB 6.7.1;
- `.chem-env/bin/crest`: CREST 3.0.2;
- `.venv`: RDKit, NumPy, SciPy, and scikit-learn;
- existing deterministic frozen-core XYZ assemblies and constrained-xTB workflow.

Additional optional packages:

- [`morfeus-ml`](https://digital-chemistry-laboratory.github.io/morfeus/) for buried volume, Sterimol, SASA, visible volume, and dispersion descriptors;
- [`molli`](https://molli.readthedocs.io/en/latest/) if the full ASO/AEIF grid machinery is preferred;
- DScribe/ASE only for the later SOAP/MBTR arm;
- CENSO plus ORCA or Turbomole only for the high-confidence free-energy refinement tier. The local environment currently has no CENSO or ORCA executable.

Before broad execution, benchmark wall time and failure rate on three substrates spanning low, medium, and high atom counts. Persist the exact xTB/CREST versions, solvent, temperature, charge, multiplicity/UHF, constraints, energy components, and calculation status per pose.

## Leakage and validity hazards

1. **Reported-site leakage.** A feature centered on the experimentally reported C–H site is unavailable for a genuinely new substrate unless the site is supplied as part of the prediction question. The primary deployable arm must enumerate all candidate C–H sites and combine them without reading the product label. A reported-site arm can remain a diagnostic upper bound.
2. **Pose-level leakage.** Poses are representations of one labelled reaction, not independent labelled rows. Split by substrate/family before any pose expansion, and return one ensemble row per prediction unit.
3. **Fold leakage.** Scaling, pruning, PCA, field resolution, energy-temperature calibration, near-attack thresholds, feature selection, and model hyperparameters must be fitted inside the training portion of each outer fold. The recent sparse-data *Nature* study used repeated nested cross-validation for feature selection.
4. **Energy-label calibration.** Tuning an effective temperature \(\tau\) in \(p_i\propto e^{-\Delta E_i/\tau}\) is a learned attention model, not thermodynamics. If tested, fit \(\tau\) only inside nested training folds and label the result `calibrated_energy_attention`.
5. **Duplicate microstates.** Multiple embeddings of the same basin will falsely inflate its probability unless structures are clustered before normalization.
6. **Spin, charge, and solvent.** Fe–nitrene state ordering can change with electronic state. Fix and document charge/multiplicity, test the defensible spin states, and do not combine their energies into one partition function unless they are on a comparable free-energy scale with degeneracy handled explicitly.
7. **Frozen-core artifact.** A low substrate strain energy does not imply a stable catalyst–substrate assembly. Population weights must use assembly-aware energies; retain substrate strain, catalyst strain, and interaction energy as separate diagnostics.
8. **Boltzmann collapse.** If \(p_{\max}>0.9\) for nearly every substrate, the weighted ensemble carries little information beyond the lowest pose. Report \(N_{\mathrm{eff}}\), and require lowest-only and uniform-weight controls.
9. **Target transformation.** Signed ee should be modeled through a consistent \(\Delta\Delta G^{\ddagger}\) transform only when absolute configuration is known. Do not mix ee magnitude with signed face features.

## Required ablations

Freeze the same family/scaffold outer folds and compare paired predictions:

| Arm | Features/weights | Question answered |
| --- | --- | --- |
| A0 | Existing structure-only baseline | What does 2D already explain? |
| A1 | Existing structure + current pose summaries | Exact incumbent comparator |
| A2 | Compact steric field, uniform weights | Does the new reaction-frame geometry help? |
| A3 | Same steric field, physical/quasi-Boltzmann weights | Does probability add value? |
| A4 | Electronic fields alone, uniform then weighted | Do pose electronics add independent signal? |
| A5 | Steric + electronic, descriptor-count matched | Is joint information synergistic? |
| A6 | A5 + dispersion and interaction/deformation energies | Do noncovalent interaction terms help? |
| A7 | Mean only versus mean + SD/tails + \(N_{\mathrm{eff}}\) + \(P_{\mathrm{ready}}\) | Does distribution shape help beyond the average? |
| A8 | MMFF94 weights versus xTB electronic-energy versus solvent/free-energy weights | Is the result robust to energy fidelity? |
| A9 | Reaction \(T\), \(T\pm25\) K, and 0.5/1.0 kcal mol\(^{-1}\) energy-noise bootstrap | Is probability stable? |
| A10 | Candidate-site deployable arm versus reported-site diagnostic | How much is genuine versus label-assisted? |

Negative controls:

- permute energies among poses of the same substrate;
- permute complete pose blocks among substrates;
- add an equal number of random features;
- lowest-pose only;
- uniform weights;
- reverse/reflection and global rotation invariance tests;
- pose-count convergence at fixed cluster coverage.

## Evaluation and promotion gate

Use nested family-held-out evaluation, preserving the exact current outer folds. Report MAE, RMSE, \(R^2\), and per-family errors for every arm. Compute paired bootstrap confidence intervals on \(\Delta\mathrm{MAE}\) and \(\Delta R^2\) from out-of-fold predictions; do not compare unrelated “best model” rows without a paired prediction analysis.

Predeclare the following promotion rule before looking at results:

- primary: mean paired MAE improves by at least 2.0 ee points versus A1 and the 95% interval excludes zero;
- co-primary: \(R^2\) improves and does not become negative in the family-held-out aggregate;
- robustness: improvement is not carried by one family, survives the energy-noise/temperature analysis, and beats the uniform-weight and lowest-only ablations;
- deployability: the candidate-site arm retains most of the gain seen in the reported-site diagnostic.

This is intentionally demanding. The present full-scope pose improvement of 0.587 ee point and family-held-out improvement of 0.285 do not pass it.

## Result that would justify the development

A successful result is not merely that xTB or more 3D features reduce training error. It is:

> A compact, label-free reaction-frame representation combining steric occupancy, local electronic/dispersion interactions, and uncertainty-aware pose accessibility produces a reproducible paired reduction in family-held-out MAE and increase in \(R^2\), beyond both uniform pose summaries and the lowest-pose-only baseline.

If only the uniform steric/electronic arm improves, keep the new fields but reject the probability claim. If Boltzmann weighting is unstable to plausible energy error, retain ensemble uncertainty features and label the weights as model attention rather than physical populations. If the candidate-site arm loses the gain, the feature is not deployable and the apparent result is probably reported-site leakage.

## Primary sources

1. Zahrt, A. F. et al. Prediction of higher-selectivity catalysts by computer-driven workflow and machine learning. *Science* **2019**, 363, eaau5631. [DOI](https://doi.org/10.1126/science.aau5631).
2. Zahrt, A. F. et al. Computational methods for training set selection and error assessment applied to catalyst design. *React. Chem. Eng.* **2021**, 6, 694–708. [DOI](https://doi.org/10.1039/D1RE00013F).
3. Brethomé, A. V.; Fletcher, S. P.; Paton, R. S. Conformational effects on physical-organic descriptors: the case of Sterimol steric parameters. *ACS Catal.* **2019**, 9, 2313–2323. [DOI](https://doi.org/10.1021/acscatal.8b04043).
4. Estrada, J. G. et al. Transferable enantioselectivity models from sparse data. *Nature* **2026**. [Article](https://www.nature.com/articles/s41586-026-10239-7).
5. Bannwarth, C.; Ehlert, S.; Grimme, S. GFN2-xTB—an accurate and broadly parametrized self-consistent tight-binding quantum chemical method with multipole electrostatics and density-dependent dispersion contributions. *J. Chem. Theory Comput.* **2019**, 15, 1652–1671. [DOI](https://doi.org/10.1021/acs.jctc.8b01176).
6. Pracht, P. et al. CREST—a program for the exploration of low-energy molecular chemical space. *J. Chem. Phys.* **2024**, 160, 114110. [DOI](https://doi.org/10.1063/5.0197592).
7. Grimme, S. et al. Efficient quantum chemical calculation of structure ensembles and free energies for nonrigid molecules. *J. Phys. Chem. A* **2021**, 125, 4039–4054. [DOI](https://doi.org/10.1021/acs.jpca.1c00971).
8. Pracht, P.; Bohle, F.; Grimme, S. Automated exploration of the low-energy chemical space with fast quantum chemical methods. *Phys. Chem. Chem. Phys.* **2020**, 22, 7169–7192. [DOI](https://doi.org/10.1039/C9CP06869D).
9. Pracht, P.; Grimme, S. Calculation of absolute molecular entropies and heat capacities made simple. *Chem. Sci.* **2021**, 12, 6551–6568. [DOI](https://doi.org/10.1039/D1SC00621E).
10. Pracht, P. et al. The topology of the potential energy surface of transition metal complexes. *Phys. Chem. Chem. Phys.* **2021**, 23, 6852–6864. [DOI](https://doi.org/10.1039/D0CP04696E).
11. Bartók, A. P.; Kondor, R.; Csányi, G. On representing chemical environments. *Phys. Rev. B* **2013**, 87, 184115. [DOI](https://doi.org/10.1103/PhysRevB.87.184115).
12. Zhu, Y. et al. Learning over molecular conformer ensembles: datasets and benchmarks. ICLR **2024**. [Proceedings](https://proceedings.iclr.cc/paper_files/paper/2024/hash/7eb6233e02f7d9efbb84acd839a996fb-Abstract-Conference.html).
13. Laplaza, R.; Wodrich, M. D.; Corminboeuf, C. Overcoming the pitfalls of computing reaction selectivity from ensembles of transition states. *J. Phys. Chem. Lett.* **2024**, 15, 7363–7370. [DOI](https://doi.org/10.1021/acs.jpclett.4c01657).
14. Laplaza, R. et al. The (not so) simple prediction of enantioselectivity—a pipeline for high-fidelity computations. *Chem. Sci.* **2022**, 13, 6858–6864. [DOI](https://doi.org/10.1039/D2SC01714H).

Official implementation documentation used for feasibility: [xTB properties](https://xtb-docs.readthedocs.io/en/latest/properties.html), [xTB Fukui/ESP commands](https://xtb-docs.readthedocs.io/en/latest/commandline.html), [CREST ensemble probabilities](https://crest-lab.github.io/crest-docs/page/overview/context.html), [CENSO source and requirements](https://github.com/grimme-lab/censo), [`molli` weighted ASO/AEIF](https://molli.readthedocs.io/en/v1.3.0/zenodo/06-gbca-calculation-vis/006-calc.html), and [`morfeus` steric/dispersion API](https://digital-chemistry-laboratory.github.io/morfeus/api/morfeus.html).
