# Supporting Information: feature-generation methods, provenance, and data availability

## Purpose and recommended use

This document is a proposed feature-focused section for the Supporting
Information of the retrospective computational study of Fe(P7)Cl (P7) and
CMC-Por-FeCl (CMC-Por). It is written to be sufficiently detailed for a reader
to understand what was calculated, how the calculations were performed, what
was used in modelling, and where the machine-readable evidence is deposited.
Large coordinate collections, repeated JSONL records, full fingerprint
vectors, and raw program logs should remain in the data deposit rather than
being reproduced in the narrative SI.

The accompanying package is [`SI2/`](README.md). The file-level SHA-256
manifest is [`manifest.json`](manifest.json). Paths below are relative to the
SI2 directory unless they begin with `repository/`; the latter identify the
original repository locations retained for operational reproducibility.

---

## S1. Computational data set and prediction unit

Two independently curated iron-porphyrin reaction domains were analysed.
The P7 domain contains 41 reaction records, and the CMC-Por domain contains 50
records. The CMC-Por records comprise 33 aryl C–H amination substrates in the
primary transfer domain and 17 sulfonyl substrates retained as a pathway
control. The primary endpoint is unsigned enantiomeric excess (ee, percent);
isolated yield (percent) is analysed separately as a secondary endpoint.

Each record contains, where available, a substrate identifier, reaction and
catalyst identifiers, fixed reaction conditions, starting-material and
free-nitrene SMILES, atom-mapped SMILES, product SMILES, candidate C–H sites,
reported reaction-site metadata, experimental outcomes, curation status, and
source provenance. Missing product structures are retained as missing values;
they are not reconstructed or imputed.

The unit of prediction is one substrate/reaction record. Conformers and poses
are representations of that substrate and are not independent labelled
observations. All pose-level features are therefore aggregated back to one
substrate row before model fitting or validation.

Thirteen canonical aryl substrate identities are shared between the two
domains. These identities are recorded in the overlap/provenance records and
are excluded from the source training set in cold-start transfer experiments.
This prevents direct compound leakage while preserving their target-domain
measurements for evaluation.

### S1.1 Data boundaries

The following boundaries should be stated explicitly in the manuscript SI:

- reported ee and yield values are retrospective measurements from the curated
  source records;
- generated substrates and proposal-panel records have predicted values only;
- no availability, route-feasibility, safety, or experimental-success claim is
  assigned to generated candidates;
- product atom maps are incomplete for a subset of P7 records and are not
  silently inferred in the structure-only branch;
- all structure, pose, CREST, and xTB features are provenance-tracked and
  label-blind unless a feature arm is explicitly identified as a reported-site
  diagnostic;
- the CMC-Por CREST run is incomplete and must not be described as a complete
  50-substrate conformer survey.

The source records and schema are deposited at:

- [`data/inputs/p7-curated-reaction-records.jsonl`](data/inputs/p7-curated-reaction-records.jsonl)
- [`data/inputs/cmcpor-curated-reaction-records.jsonl`](data/inputs/cmcpor-curated-reaction-records.jsonl)
- [`data/inputs/reaction-record.schema.json`](data/inputs/reaction-record.schema.json)

## S2. Software, environments, and executable provenance

The primary analysis environment used Python 3.14.6, RDKit 2026.3.4,
SciPy 1.18.0, scikit-learn 1.9.0, LightGBM 4.7.0, and NumPy. Candidate
generation used a separate Python 3.11.16 environment with PyTorch 2.13.0,
RDKit 2026.3.5, SMILES-RNN, and PromptSMILES. The external quantum-chemistry
tools used in the feature-generation work were xTB 6.7.1 and CREST 3.0.2.

The package retains the environment declarations in
[`requirements.txt`](requirements.txt) and
[`requirements-generator.txt`](requirements-generator.txt). The source
programs are grouped as follows:

| Function | SI2 source location | Main outputs |
| --- | --- | --- |
| RDKit/Tier 1 descriptors and candidate-site features | [`source/rdkit/build_tier1_features.py`](source/rdkit/build_tier1_features.py) | Tier 1 JSONL feature records |
| Record-level RDKit/Morgan table | [`source/rdkit/build_feature_table.py`](source/rdkit/build_feature_table.py) | 91-row B5-compatible feature table |
| Stage 1 pose generation and validation | [`source/pose/stage1_contract.py`](source/pose/stage1_contract.py) | UFF-scored reports and retained XYZ/SDF files |
| Stage 2 pose summaries/interactions | [`source/pose/stage2_pose_summary.py`](source/pose/stage2_pose_summary.py), [`source/pose/stage2_pose_interaction.py`](source/pose/stage2_pose_interaction.py) | pose-summary and pose-interaction JSONL |
| Stage 2p/2pp representations | [`source/pose/stage2p_representation.py`](source/pose/stage2p_representation.py), [`source/pose/stage2pp_representation.py`](source/pose/stage2pp_representation.py) | 248- and 655-feature representations |
| CREST ensemble generation | [`source/crest/generate_crest_ensembles.py`](source/crest/generate_crest_ensembles.py) | conformer ensembles, reranks, weights, logs |
| CREST/xTB ablation | [`source/crest/p7_crest_xtb_benchmark.py`](source/crest/p7_crest_xtb_benchmark.py) | features, predictions, metrics, bootstrap |
| xTB reference features | [`source/xtb/stage3a_run_xtb_references.py`](source/xtb/stage3a_run_xtb_references.py), [`source/xtb/stage3a_reference_features.py`](source/xtb/stage3a_reference_features.py) | constrained reference summaries |
| Local shell and intrinsic BDE features | [`source/xtb/stage3a_local_shell_features.py`](source/xtb/stage3a_local_shell_features.py), [`source/xtb/stage3b_intrinsic_bde.py`](source/xtb/stage3b_intrinsic_bde.py) | local 3D shells and BDE JSONL |

The exact frozen input/reference files are:

- P7 manual substrate table, optimization conditions, constraint profile, and
  reference geometry;
- CMC-Por manual substrate table, constraint profile, and reference geometry;
- reaction-record schema and source/remapping validation records.

They are collected under [`data/inputs/`](data/inputs/).

## S3. Input curation and molecular preparation

Starting-material identities were parsed with RDKit and stored in both
unmapped and atom-mapped form. The unmapped aryl-azide SMILES is the input to
structure-only descriptors and Morgan fingerprints. Atom-mapped SMILES are
used where reaction-centre and candidate-site information is required.

For every record, candidate C–H sites are represented with an atom-map ID,
site ID, site type, hydrogen count, and the curation status of the reported
site. Site types include aryl, benzylic, aliphatic, benzylic-adjacent,
carbonyl-alpha, cycloalkyl, heteroaryl-adjacent, silylalkyl-substituted, and
thioether-benzylic categories where applicable.

Reported-site information is retained for auditing and for explicitly named
diagnostic arms. A deployable structure-only feature row does not use the
reported product-forming atom. For full-scope records where the product atom
map was not manually reviewed, the reaction-centre assignment is labelled as
inferred and remains separate from a confirmed product mapping.

## S4. RDKit descriptors and Morgan fingerprints

### S4.1 Descriptor calculation

RDKit sanitizes each unmapped aryl-azide molecule before feature calculation.
The 15-descriptor structure table contains:

1. heavy atom count;
2. molecular weight;
3. Crippen logP;
4. topological polar surface area;
5. formal charge;
6. fraction sp3;
7. rotatable bond count;
8. total ring count;
9. aromatic ring count;
10. hydrogen-bond acceptor count;
11. hydrogen-bond donor count;
12. heteroatom count;
13. aliphatic ring count;
14. spiro-atom count; and
15. atom-centre count for specified or unspecified tetrahedral chirality.

Descriptor values are stored as numeric columns. Descriptor scaling,
constant-feature removal, and any model selection are fitted within the
training portion of each validation split; no fold-level transformation uses
the held-out target substrate.

### S4.2 Representation ladder

The frozen structure representation ladder should be reported compactly as
follows:

| Arm | Features | Count | Role |
| --- | --- | ---: | --- |
| B0 | Training-fold mean | 0 | No-feature reference |
| B1 | Molecular weight, logP, TPSA, fraction sp3, rotatable bonds, and ring count | 6 | Minimal 2D baseline |
| B2 | Fifteen RDKit descriptors | 15 | Descriptor baseline |
| B3 | B2 + radius-2 Morgan fingerprint | 143 | 128-bit reduced fingerprint |
| B4 | B2 + radius-2 Morgan fingerprint | 271 | 256-bit dimension-matched control |
| B5 | B2 + radius-2 Morgan fingerprint | 1,039 | Primary structure-only reference |

The B5 fingerprint is generated with RDKit's Morgan generator using radius 2,
1,024 bits, and `includeChirality=False`. The bit columns are ordered
`morgan_r2_bit_0000` through `morgan_r2_bit_1023`. The complete 91-row table
for both domains is [`data/rdkit-morgan/rdkit-morgan-features.csv`](data/rdkit-morgan/rdkit-morgan-features.csv), with its parameters and feature order in
[`data/rdkit-morgan/rdkit-morgan-features-manifest.json`](data/rdkit-morgan/rdkit-morgan-features-manifest.json).

### S4.3 Tier 1 candidate-site artifact

The separate Tier 1 JSONL artifact contains record-level physicochemical
features, candidate-site descriptors, and a 2,048-bit radius-2,
chirality-aware Morgan fingerprint. This artifact is used for candidate-site
auditing and rule-feature construction. It is not the same as the B5 table and
should not be described as a 2,048-bit version of the primary B5 model.

## S5. Canonical Stage 1 pose generation

Pose generation is label-blind. Experimental ee, yield, product identity, and
reported reactive-site labels are not used to generate, filter, rank, or retain
the conformers in the canonical pose pool.

For each substrate, RDKit ETKDGv3 attempts a deterministic 5,000-conformer
pool with random seed `20260730`. Each conformer is optimized and scored with
the Universal Force Field (UFF). The retained pose is then virtually assembled
with the corresponding frozen catalyst reference geometry. The P7 and CMC-Por
reference geometries and their constraint profiles are distinct and are
stored in [`data/inputs/`](data/inputs/).

Each candidate is checked for:

- RDKit parse and conformer-generation success;
- preservation of molecular connectivity;
- consistency of the reaction-site/anchor atoms;
- preservation of the fixed catalyst core and Fe–nitrene distance;
- severe nonbonded clashes using a covalent-radius floor with radius scale
  `0.65`; and
- successful writing of substrate and frozen-core assembly coordinates.

The Fe–N distance tolerance is `1e-5 Å` relative to the catalyst-specific
reference. From the valid, clash-screened pool, 100 lowest-UFF poses and 100
highest-UFF chemically valid poses are retained, giving 200 poses per
substrate. The two strata are kept separate in downstream summaries. UFF is a
ranking/proxy score only; it is not interpreted as a reaction energy,
activation barrier, free energy, or thermodynamic population.

The full reports and retained coordinates are deposited under:

- P7: [`data/pose/p7/stage1-reports/`](data/pose/p7/stage1-reports/) and [`data/pose/p7/geometries/`](data/pose/p7/geometries/)
- CMC-Por: [`data/pose/cmcpor/stage1-reports/`](data/pose/cmcpor/stage1-reports/) and [`data/pose/cmcpor/geometries/`](data/pose/cmcpor/geometries/)

Each Stage 1 report records the run ID, random seed, generated and retained
counts, selection strata, filter settings, toolkit version, input hashes,
reference-geometry hash, and constraint-profile hash. The narrative SI should
report these parameters and point to the reports rather than printing all 200
coordinate blocks per substrate.

## S6. Stage 2 pose-derived representations

### S6.1 Pose summaries and interaction features

The Stage 2 summary block records retained-pose counts, UFF-score summaries,
low/high-stratum counts, clash-screen results, core RMSD summaries, Fe–N and
nitrene-centred geometry summaries, and other quality-control fields. The
pose-interaction block retains pose-level values and aggregates them by
substrate using count, minimum, quantiles, mean, maximum, and standard
deviation where defined.

These fields include Fe–N distance, nitrene-to-carbon and nitrene-to-hydrogen
distances, Fe–N–C and N–C–H angles, substrate-to-catalyst distances, and
contact counts by distance bin. They are geometric descriptors of the frozen
assembly and do not represent electronic density.

### S6.2 Stage 2p reaction-axis representation

Stage 2p converts each 200-pose ensemble into one 248-feature substrate row.
The coordinate convention is an azimuth-free, nitrene-anchored reaction axis
defined from the nitrene nitrogen, transferable hydrogen, and candidate or
reported reaction carbon. The feature families summarize:

- radial distributions around the nitrene and transferred hydrogen;
- angular even/odd moments and directional responses;
- N→H and H→N axial summaries;
- all-heavy, carbon, aromatic, heteroatom, halogen, reactive-carbon, and
  reactive-hydrogen channels;
- low- versus high-UFF-stratum contrasts; and
- distributional relationships such as Wasserstein distance, energy distance,
  Jensen–Shannon angular divergence, and UFF-rank correlations.

Catalyst atoms are excluded from the Stage 2p density fields. All poses from
one substrate remain in one validation unit. The Stage 2p manifest records the
248 feature names, 200-pose strata, reaction-axis convention, radial basis,
and provenance flags.

### S6.3 Stage 2pp persistent occupancy representation

Stage 2pp extends Stage 2p with 655 persistent atomic-occupancy and
reaction-corridor flexibility features. It also writes numerical NPZ density
arrays and SVG views for quality control and visual interpretation. These
arrays are geometric occupancy summaries derived from XYZ coordinates; they
are not electron-density calculations.

The Stage 2p and Stage 2pp features, manifests, model matrices, numerical
arrays, and SVG views are organized under:

- [`data/pose/p7/stage2/`](data/pose/p7/stage2/) and [`data/pose/p7/stage2pp/`](data/pose/p7/stage2pp/)
- [`data/pose/cmcpor/stage2/`](data/pose/cmcpor/stage2/) and [`data/pose/cmcpor/stage2pp/`](data/pose/cmcpor/stage2pp/)

The compact representation arms used in modelling are:

| Arm | Composition | Count | Interpretation |
| --- | --- | ---: | --- |
| P0 | Stage 2p pose block | 248 | Pose-only diagnostic |
| P1 | B1 + Stage 2p | 254 | Minimal 2D plus pose |
| P2 | B5 + raw Stage 2p | 1,287 | Legacy pose diagnostic |
| P3 | B5 + compact C1 geometry | 1,083 | Compact pose upgrade |
| P4 | B5 + C1 + 16-feature C2 interaction block | 1,099 | Transfer-specific pose tier |

## S7. CREST and substrate-only GFN2-xTB generation

CREST was evaluated as an exploratory conformer-generation and electronic
descriptor branch. It must be separated from the canonical frozen-core UFF
pose workflow in the SI because it answers a different question.

The CREST calculation samples the neutral, closed-shell aryl-azide substrate
alone. The porphyrin and Fe–nitrene assembly are not included in the CREST
metadynamics search. Seed geometries are generated with deterministic ETKDGv3
and MMFF94/UFF cleanup. CREST 3.0.2 uses external xTB for quick GFN2 sampling
with ALPB ether, a 30 kcal/mol search window, and genetic crossing disabled for
the rigid one-member cases. CREGEN uniqueness filtering is followed by an
independent GFN2-xTB/ALPB(ether) single-point rerank.

At most ten unique minima were requested per substrate. The run reached the
decision boundary after complete results for all 40 P7 substrates and 16
CMC-Por substrates. Four later CMC-Por directories (`2o`, `2p`, `2q`, and
`2r`) contain partial logs and are retained for audit but are not counted as
completed results. Every one of the 56 completed substrates produced one
unique CREGEN minimum. Consequently, the reported maximum population and
effective conformer count are one for every completed substrate; no duplicate
conformers were added to pad the ensembles.

Each completed record retains the conformer XYZ file, CREST stdout/stderr,
GFN2 rerank data, temperature, relative energies, Boltzmann values, command
provenance, and an XYZ hash. The complete ensemble record is in
[`data/crest/ensembles/`](data/crest/ensembles/).

### S7.1 CREST/xTB ablation result

The matched P7 family-held-out ablation used 38 modelable P7 records and the
same nested Elastic Net procedure for every arm:

| Feature arm | Feature count | MAE | R² | RMSE |
| --- | ---: | ---: | ---: | ---: |
| Matched Stage 2p geometry baseline | 248 | 8.498 | 0.476 | 11.357 |
| Baseline + CREST geometry | 258 | 8.858 | 0.455 | 11.578 |
| Baseline + dense GFN2-xTB electronics | 261 | 8.610 | 0.440 | 11.745 |
| Baseline + CREST geometry + GFN2-xTB | 271 | 8.876 | 0.429 | 11.860 |

The combined arm changed MAE by +0.377 ee points relative to the matched
baseline. A paired 20,000-draw substrate bootstrap gave a reported MAE-change
interval of `[-1.000, 0.212]` ee points and a 0.107 probability of a positive
MAE improvement. Because the conformer distributions collapsed to one state,
the CREST probability block did not provide ensemble information.

The appropriate SI conclusion is that substrate-only CREST/GFN2-xTB did not
pass the prespecified additive-feature gate for P7. This does not rule out
catalyst-pocket or assembly-aware quantum descriptors; it shows that a
free-substrate minimum cannot substitute for a distribution of
catalyst-compatible reactive poses.

The full ablation features, metrics, predictions, and five-pose controls are
deposited under [`data/crest/benchmarks/`](data/crest/benchmarks/), with
procedure and decision history in [`procedure/results.md`](procedure/results.md)
and [`procedure/development-log.md`](procedure/development-log.md).

## S8. xTB reference, local-shell, and BDE features

### S8.1 Constrained Stage 3a reference features

The Stage 3a-lite branch runs constrained xTB reference optimizations for
selected candidate-site assemblies. The catalyst scaffold core is restrained
according to the frozen constraint policy, while candidate-site geometry and
reaction-centre summaries are extracted from the optimized complex.

The reference summary contains, where available, final xTB energy, Fe
displacement, Fe–N–candidate-C angle, nitrene-N to candidate-C distance,
nitrene-N to transferable-H distance, N–C–H angle, and frozen-core RMSD and
displacement statistics. The worklist, constraint policy, optimization
results, raw optimization files, and logs are retained under
[`data/xtb/`](data/xtb/).

### S8.2 Local 3D shell features

The local-shell branch counts and summarizes atoms around three explicit
centres: the nitrene centre, the candidate C–H HAA centre, and the reactive
approach midpoint. The fixed radial shells are 0–3, 3–4, 4–5, 5–6, and 6–8 Å.
Features include atom counts, heteroatom and donor/acceptor counts, nearest
distances, ownership counts, aromatic-centroid proximity, and C–H orientation
quantities where defined.

### S8.3 Intrinsic C–H BDE features

For each selected candidate site, the Stage 3b branch constructs an optimized
neutral substrate and the corresponding doublet carbon radical. Both are
calculated with GFN2-xTB and ALPB ether. Using one fixed hydrogen-atom
reference, the intrinsic C–H bond-dissociation estimate is:

\[
D_\mathrm{C-H} = E(\text{substrate radical}) + E(\text{H atom}) - E(\text{neutral substrate}).
\]

The hydrogen reference energy retained in the output is `-0.391629889244 Eh`.
BDE values are reported in kcal mol⁻¹ using the Hartree-to-kcal mol⁻¹
conversion in the source code. The feature row records the absolute value,
within-substrate rank, competing-site gap, neutral/radical optimization
status, successful and failed site counts, xTB method, solvent, radical state,
and calibration status.

The current BDE values are labelled `uncalibrated_xtb`. An interim comparison
joins 119 candidate-site pairs across 38 P7 substrates to the available
GFN2-xTB/ALPB(ether) calculations. A 12-site higher-level reference panel was
selected, but no higher-level reference results are available; therefore the
BDE block should be presented as a mechanistic ranking/diagnostic feature, not
as a validated activation barrier or quantitative selectivity model.

## S9. Model fitting and validation controls

The supervised estimator families examined were Ridge regression, Elastic Net,
Tanimoto-k-nearest neighbours, LightGBM, and Gaussian-process regression. The
primary progressive and transfer estimator is standardized Ridge regression
with `alpha=10`; predictions are bounded to 0–100%. Progressive Elastic Net
uses `alpha=0.1`, `l1_ratio=0.15`, `max_iter=10000`, and random state 0.

The independent P7 held-out benchmark uses nested selection over prespecified
Ridge, Elastic Net, LightGBM, and Gaussian-process grids. Target-held-out
validation withholds each target substrate in turn. The 38-record P7
benchmark selects 29 structurally diverse training molecules by MaxMin
Morgan/Tanimoto distance and reserves the remaining eight for
validation/hyperparameter selection. Family-held-out analyses withhold entire
curated substrate families.

All preprocessing that can learn from the data—scaling, constant-feature
filtering, feature selection, model selection, and any calibration—is fitted
inside the training partition. Poses from one substrate are never split across
training and validation. Performance is summarized using MAE, RMSE, R², rank
correlation where applicable, and threshold-accuracy fractions. Independent
held-out bootstrap intervals use 20,000 draws and frozen seed `20260731`.

Progressive acquisition compares historical order, diversity-first,
performance-first, uncertainty–diversity, and a 500-route random control. The
uncertainty–diversity score weights uncertainty, molecular diversity, and
family coverage as 0.4, 0.4, and 0.2, respectively. Predictions are made for
unrevealed substrates before the next experimental label is exposed.

Bidirectional transfer is evaluated for P7 → CMC-Por and CMC-Por → P7. The
guarded transfer procedure limits early source weight, updates expert trust
from prequential target error, and suppresses source experts that are more than
1 ee point and more than 10% worse than target-only performance. The primary
transfer gate requires early-prefix AUC improvement of at least 10%, no
material negative transfer, matched-control superiority, and replication in
both directions.

## S10. Recommended figures and tables for the SI

The narrative should contain compact definitions and selected results. The
following items should be supplied as tables/figures or linked machine-readable
artifacts rather than expanded into the prose:

| Item | Recommended content | SI2 evidence |
| --- | --- | --- |
| Table S1 | Dataset counts, catalyst/condition IDs, endpoint availability, exclusions | `data/inputs/*curated-reaction-records.jsonl` |
| Table S2 | B0–B5 and P0–P4 definitions and feature counts | `METHODS.md`, Stage 2p/2pp manifests |
| Table S3 | Software versions, seeds, force fields, solvent, charge/multiplicity, constraints | `data/inputs/`, `data/xtb/`, source scripts |
| Table S4 | Stage 1 pose counts, validity, low/high strata, and retained counts by domain | `data/pose/*/stage1-reports/` |
| Table S5 | Held-out and family-held-out model comparisons | `data/pose/*/stage2/`, model-comparison outputs |
| Table S6 | CREST/xTB ablation metrics and paired bootstrap | `data/crest/benchmarks/p7-crest-xtb-model/` |
| Figure S1 | Independent progressive learning curves | existing supporting-information figures |
| Figure S2 | Estimator/representation comparisons | existing supporting-information figures |
| Figure S3 | Reciprocal transfer representation comparison | existing supporting-information figures |
| Figure S4 | Stage 2pp occupancy/pose overlays | existing supporting-information figures |

The full feature names, per-substrate values, prediction rows, and raw
coordinates should be supplied in the associated data archive. A reader can
then reproduce any table or figure without forcing the PDF SI to contain
thousands of columns or repeated coordinate blocks.

## S11. Data availability and reproducibility statement

The SI2 package contains the source snapshots, input records, generated
feature tables, retained pose coordinates, Stage 2p/2pp representations,
occupancy arrays, SVG diagnostics, CREST ensembles, xTB reference outputs,
BDE features, model predictions, reports, and file-level SHA-256 checksums.

The complete package is indexed in [`manifest.json`](manifest.json). The
record-level RDKit/Morgan table can be regenerated with:

```bash
.venv/bin/python SI2/source/rdkit/build_feature_table.py
```

Canonical repository-root feature commands and CREST/xTB commands are listed
in [`REPRODUCE.md`](REPRODUCE.md). The copied source snapshots in `source/`
are included for archival completeness; the original repository scripts remain
the operational entry points because they retain the repository-root default
paths.

Large XYZ/SDF coordinate collections and xTB/CREST raw logs should be released
through the repository release, Git LFS, or a permanent archive if ordinary
Git history is too large. The release must preserve the SI2 directory layout
and SHA-256 manifest. Replace the repository, release, DOI, code-license, and
data-license placeholders only when those public locations exist.

## S12. Limitations and claim boundary

The following statements should remain in the final SI:

1. The study is retrospective and does not establish prospective experimental
   improvement.
2. The canonical pose representation uses UFF-ranked geometric proxies and
   fixed catalyst cores; UFF values are not thermodynamic energies.
3. Stage 2p/2pp occupancy is geometric atom occupancy, not electron density.
4. Substrate-only CREST/GFN2-xTB generated one unique minimum for each of the
   56 completed records, so its probability features collapsed and the
   additive P7 ablation failed the locked promotion gate.
5. xTB BDE values remain uncalibrated to a higher-level reference and should
   not be interpreted as activation barriers.
6. The CMC-Por CREST run is incomplete; the four partial directories are not
   completed conformer results.
7. Candidate-site and reported-site fields must be distinguished. A reported-
   site diagnostic cannot be presented as a deployable new-substrate feature.
8. Product structures missing from the curated record are marked missing; they
   are not reconstructed for convenience.

This claim boundary is part of the reproducibility record, not merely a
presentation preference. It prevents the presence of extensive raw 3D or xTB
data from being mistaken for evidence that those data improved the predictive
model.
