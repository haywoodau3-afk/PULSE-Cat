# Methods

## Study design and reaction datasets

The computational workflow was developed for two independently curated
iron-porphyrin catalyst domains: Fe(P7)Cl (P7) and CMC-Por-FeCl (CMC-Por).
The frozen P7 dataset contained 41 reaction records; 39 were retained in the
progressive analysis and 38 had usable enantioselectivity (ee) labels after the
documented catalyst and outcome exclusions. The CMC-Por dataset contained 50
records, comprising 33 aryl substrates in the primary transfer domain and 17
sulfonyl substrates retained as a pathway control. Unsigned ee percentage was
the primary modeling endpoint, and isolated yield was analyzed independently
as a secondary endpoint. Each substrate, rather than each generated pose, was
treated as one experimental observation.

Reaction records were stored in JSONL format with substrate identity,
starting-material and free-nitrene SMILES, product SMILES when reported,
reaction-center metadata, catalyst and condition identifiers, experimental
outcomes, exclusions, and source provenance. Molecular identities were
canonicalized with RDKit. Thirteen canonical aryl substrates shared between
the two systems were reconciled in an explicit overlap ledger. These shared
identities were excluded from the source training set in cold-start transfer
experiments to prevent direct compound leakage. Missing product structures
were retained as null values and were not computationally reconstructed.

## Two-dimensional molecular representations

Eleven representation arms were defined. B0 was a training-fold-mean reference
with no molecular features. B1 contained six chemically interpretable RDKit
descriptors, and B2 contained 15 RDKit physicochemical descriptors. B3, B4,
and B5 combined the B2 descriptors with radius-2 Morgan fingerprints of 128,
256, and 1,024 bits, respectively. B5, containing 1,039 total features, was the
primary structure-only reference. Descriptor calculation and SMILES parsing
were performed with RDKit. Scaling, constant-feature filtering, and model
selection were fitted only on the training portion of each validation split.

## Pose generation and three-dimensional representations

Pose generation was label-blind: experimental ee and yield were not used to
generate, filter, rank, or retain conformers. For each substrate, the Stage 1
workflow attempted 5,000 deterministic RDKit ETKDGv3 embeddings. Substrate
geometries were cleaned with the Universal Force Field (UFF), virtually
assembled against the catalyst-specific frozen reference geometry, and checked
for connectivity preservation, reaction-site consistency, core-constraint
compliance, and severe nonbonded clashes. From the valid pose pool, 200 poses
were retained per substrate: the 100 lowest-UFF valid poses and the 100
highest-UFF chemically valid, clash-screened poses. UFF values were used only
to rank poses and were not interpreted as reaction energies, activation
barriers, free energies, or thermodynamic populations.

Stage 2p converted each retained ensemble into a 248-feature,
substrate-level representation anchored to the nitrene nitrogen, transferred
hydrogen, and product-forming carbon. Features summarized radial and angular
geometry, directed N-to-H and H-to-N relationships, elemental channels,
top-versus-bottom ensemble contrasts, and pose-distribution stability. The
Stage 2pp branch generated 655 persistent atomic-occupancy and
reaction-corridor flexibility features, numerical NPZ density arrays, and
derived SVG views. These fields represent geometric occupancy rather than
electron density. All poses belonging to one substrate remained together in
every model split.

Five pose-related model arms were evaluated. P0 contained the Stage 2p pose
block alone; P1 combined B1 with P0; and P2 combined B5 with the full Stage 2p
block. P3 appended a compact 44-feature C1 geometry block to B5. P4 appended
both C1 and a 16-feature C2 catalyst-interaction block to B5. Random,
dimension-matched, and substrate-permuted pose controls were retained where
specified by the individual experiment manifests.

## Rule-based substrate features

A separate label-independent feature branch encoded progressively richer
reaction-site rules. V0 contained the structure-only RDKit/Morgan reference;
V1 added coarse C–H bond-dissociation and electronegativity-shell priors; V2
added tether and global flexibility; V3 added steric, topological, polarity,
and site-ambiguity terms; V4 added neighbour-role and competing-site contrasts;
V5 added local reaction-path accessibility; and V6 combined the electronic,
contrast, accessibility, and local-regime blocks. The rule values were used as
fixed descriptors and acquisition features and were not fitted to ee labels.
An interim calibration compared the rule-based C–H ranking with existing
GFN2-xTB/ALPB(ether) calculations for 119 sites from 38 P7 substrates. Raw and
leave-one-substrate-out affine-corrected errors and within-substrate ranks were
recorded. A 12-site higher-level calculation panel was selected, but no
higher-level reference result was available.

## Predictive modeling and validation

Five supervised estimator families were examined across the study: Ridge
regression, Elastic Net, Tanimoto-k-nearest neighbours, LightGBM, and
Gaussian-process regression. The primary progressive and transfer estimator
was standardized Ridge regression with alpha = 10 and predictions bounded to
the physically meaningful interval of 0–100%. Progressive Elastic Net used
alpha = 0.1, an L1 ratio of 0.15, a maximum of 10,000 iterations, and random
state 0. Tanimoto-k-nearest-neighbour predictions were based on Morgan
fingerprint similarity. The independent P7 held-out benchmark additionally
used nested selection over prespecified Ridge, Elastic Net, LightGBM, and
Gaussian-process grids.

Target-held-out validation withheld each target substrate in turn. In the
39-record P7 benchmark, 30 structurally diverse molecules were selected from
the remaining records for training by MaxMin Morgan/Tanimoto distance, with
the remaining eight used for validation and hyperparameter selection.
Family-held-out analyses withheld complete curated substrate families and
performed feature processing and model selection without access to the held-out
family. Model performance was summarized by MAE, root-mean-square error,
coefficient of determination, rank correlation where applicable, and the
fractions of predictions falling within specified ee-error thresholds.
Bayesian-bootstrap intervals for the independent held-out benchmark used
20,000 draws with frozen seed 20260731.

## Progressive substrate-scope learning

Progressive learning began from a two-substrate central-plus-diverse seed and
revealed one complete substrate at each subsequent step. Five acquisition
logics were compared: historical order, diversity-first, performance-first,
uncertainty–diversity, and random selection. The uncertainty–diversity score
combined uncertainty (weight 0.4), molecular diversity (0.4), and family
coverage (0.2). The performance-first score combined predicted performance
(0.5), uncertainty (0.3), and diversity (0.2). Random controls used 500
independent two-substrate seeds sampled without replacement and were evaluated
at every labelled prefix. Ridge and Tanimoto-k-nearest-neighbour models were
included in the 500-route random stress test; Elastic Net was retained for the
deterministic-route comparisons.

At each prefix, predictions were made for the unrevealed substrate set before
the next label was exposed. Full learning trajectories, selection events, and
per-prefix errors were persisted. Learning efficiency was assessed using mean
prefix MAE, area under the progressive MAE curve (AUC-MAE), final-prefix MAE,
and `n90`, defined in the frozen manifests as the number of labelled substrates
required for the median learning-curve MAE to achieve 90% of the error reduction
between the training-fold-mean baseline and the full-data reference model.

## Guarded bidirectional transfer learning

Transfer was evaluated in both directions: P7 as the frozen source for
CMC-Por, and CMC-Por as the frozen source for P7. At every target prefix,
target-only, source-only, pooled/domain-aware, and guarded predictions remained
separately identifiable. Before a target label was revealed, each eligible
expert predicted that record. After label revelation, expert trust was updated
from cumulative prequential target error. The guard began with a target weight
of 0.5, allocated no more than 0.5 total weight to source experts during the
first five scored post-seed reveals, and suppressed an active source expert
when its cumulative MAE was both more than 1 ee point and more than 10% worse
than the target-only expert. Suppressed experts continued to generate shadow
predictions for auditing.

The B1–B5 and P0–P4 representations were compared under the same target orders.
Paired route and scaffold bootstrap analyses were used to quantify differences
between target-only and guarded predictions. The prespecified primary transfer
gate required at least a 10% reduction in early-prefix AUC-MAE, preservation or
improvement of the full learning curve, no material family/scaffold negative
transfer, superiority to matched controls, and replication in both transfer
directions. This gate was evaluated as specified and was not relaxed after
observing the results.

## Generative substrate search

Candidate generation used SMILES-RNN with a ChEMBL28 prior and PromptSMILES
1.7.2 conditioning on the aryl-azide substrate scaffold. Five fixed random
seeds (1101, 2202, 3303, 4404, and 5505) generated 10,112 strings each,
yielding 50,560 persisted raw candidates. The complete deterministic batch was
retained without post hoc removal of the 112-per-seed excess over the original
10,000-per-seed request. A deterministic enumeration comparator was generated
at the same 50,560-candidate budget.

Candidates passed through frozen RDKit parsing and sanitization, aryl-azide
identity, topology, reaction-site, ring-closure, functional-group, duplicate,
and applicability-domain checks. Rejection reasons and canonical identities
were retained for every processed candidate. Candidate prioritization used the
frozen ee predictor together with uncertainty or expected information gain,
applicability distance, and structural-morphology diversity. Generator
likelihood was not used as the decisive ranking variable. Generated candidates
and the sealed proposal panel were treated as prediction-only records; no
experimental outcome, availability, route feasibility, or safety claim was
assigned to them.

## Reproducibility and artifact integrity

All analysis outputs were stored as versioned CSV, JSON, JSONL, NPZ, SVG, or
Markdown artifacts. Feature definitions, split assignments, random seeds,
selection events, predictions, exclusions, model metrics, and source paths were
persisted. Publication-level and raw-data manifests record byte sizes and
SHA-256 digests. The supporting-information deposit contains 30,118 non-XYZ
scientific files totaling 567,855,166 bytes. Large XYZ coordinate caches were
excluded from the local manuscript package but are enumerated in the exclusion
manifest and can be distributed as a separate coordinate archive.

# Data availability

The curated reaction records, starting-material and available product SMILES,
descriptor and fingerprint matrices, pose-derived feature matrices, numerical
density arrays, model splits, predictions, progressive-learning trajectories,
transfer replicates, generator outputs, proposal panels, and file-level
checksums will be made publicly available upon publication at:

**GitHub repository:** `[GITHUB_REPOSITORY_URL]`  
**Frozen release/tag:** `[GITHUB_RELEASE_OR_TAG]`  
**Permanent archive DOI:** `[ZENODO_OR_OTHER_ARCHIVE_DOI]`

Because of repository size limits, large coordinate collections, model
checkpoints, and other binary artifacts will be distributed through GitHub
Releases, Git Large File Storage, or the linked permanent archive rather than
the ordinary Git history. The release will preserve the directory structure
used by the analysis and will include a manifest mapping every deposited file
to its SHA-256 digest. The manuscript tables and compact machine-readable data
are also provided in the accompanying Supporting Information. Until the public
release is created, the placeholders above do not constitute an active data
repository.

No data are currently available for checkpoint 10, which concerns transfer to
an unseen third iron-porphyrin system. The corresponding catalyst records,
reference geometry, pose features, and experimental outcomes will be deposited
under a new versioned release if and when that study is completed.

# Code and library availability

The scripts used for curation, feature generation, modeling, progressive
learning, guarded transfer, visualization, candidate filtering, and SI assembly
will be released with the data at `[GITHUB_REPOSITORY_URL]`. Reproduction
commands and environment files will be provided at the repository root.

The frozen primary analysis environment used Python 3.14.6, RDKit 2026.3.4,
SciPy 1.18.0, scikit-learn 1.9.0, and LightGBM 4.7.0. The separate generator
environment used Python 3.11.16, PyTorch 2.13.0, and RDKit 2026.3.5. Candidate
generation used SMILES-RNN commit
`c8ee705961b4411707c69f73d309c1cf61208b95` with the ChEMBL28 prior checkpoint
and PromptSMILES version 1.7.2. The checkpoint identity and SHA-256 digest are
recorded in the generator freeze configuration.

RDKit, SciPy, scikit-learn, LightGBM, NumPy, PyTorch, SMILES-RNN, and
PromptSMILES are third-party libraries and remain subject to their respective
licenses. SMILES-RNN is recorded as MIT licensed and PromptSMILES as
Apache-2.0 licensed in the frozen configuration. Project-specific code and
data will be released under `[CODE_LICENSE]` and `[DATA_LICENSE]`, respectively.
