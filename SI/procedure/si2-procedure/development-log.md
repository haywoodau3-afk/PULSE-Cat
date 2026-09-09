# Development log

## Confirmed decisions

- Primary target: ee magnitude; isolated yield is a secondary no-harm check.
- Evaluation: the same nested family-held-out cohort as the publication
  benchmark, with a required improvement of at least 2.0 ee points in MAE,
  increased pooled R2, no material RMSE degradation, and paired-bootstrap
  support.
- Candidate-site policy: enumerate every plausible C-H HAA site without using
  the reported product-forming site as model input.
- Intended scale: 100 poses per substrate, split 50/50 between diverse
  representatives of the retained low-UFF and valid high-UFF strata, but only
  after a five-pose resource and validity gate.
- Probability semantics: uncertainty-aware quasi-Boltzmann weights at the
  recorded 60 or 80 C reaction temperature, with energy-noise sensitivity,
  population entropy, effective pose count, and reaction-ready probability.

## Implementation

`pose_probability.py` now provides:

1. deterministic max-min pose selection in the fixed catalyst coordinate frame;
2. cluster-size sampling priors that prevent duplicate embeddings from
   automatically receiving excess probability mass;
3. GFN-FF cleanup, direct GFN2-xTB, and constrained GFN2-xTB optimization arms;
4. explicit charge and UHF settings (default neutral doublet, matching the
   defined selectivity intermediate); 
5. ALPB ether and per-process timing/resource provenance;
6. uncertainty-aware ensemble weighting with deterministic Monte Carlo draws;
7. label-blind per-site N-H distance, N-H-C angle, pocket clearance,
   xTB charges, C-H Wiberg bond order, and soft reaction-ready score;
8. compact population, steric, electronic, and site-competition aggregates.

Four tests cover population normalization, cluster degeneracy priors,
reproducible uncertainty propagation, and the reaction-ready kernel ordering.

## What changed after measurement

The initially recommended GFN-FF-cleanup route was demoted to an ablation. Its
full-complex topology/optimization was not robust, and its successful final
energies were not mutually plausible. Direct GFN2-xTB single points are fast
and robust as electronic descriptors, but raw total energies on the unrelaxed
assemblies are rejected as population energies because they collapse the
ensemble onto one pose. A constrained GFN2 optimization control was attempted
on the same five structures and stopped after more than five minutes: two
poses had already failed SCF convergence and three had not completed. This is
a scientific method failure, not merely a compute-budget issue.

## Required repair before the 100-pose run

1. Generate a genuine low-energy conformer ensemble (preferably CREST) rather
   than treating the deliberately retained high-UFF stress arm as equilibrium.
2. Calibrate charge/UHF and SCC stability for the Fe-aminyl assembly; include
   electronic-temperature and alternate-state sensitivity without mixing
   incomparable states in one partition function.
3. Separate conformer plausibility from catalyst-pocket accessibility:
   substrate/conformer free energies supply the former, while assembly steric,
   electrostatic, dispersion, and reaction-ready fields supply the latter.
4. Keep high-UFF poses as uniformly summarized counterfactual stress features,
   not thermodynamic microstates.
5. Require non-collapsed populations and pose-count convergence before fitting
   the locked ablation matrix.

## Substrate-only CREST production run

The requested scale was revised from 100 assembly poses to a maximum of 10
unique substrate conformers for every P7 and CMC-Por record. Inventory checks
found 40 P7 and 50 CMC-Por substrates. CREST is applied only to each neutral,
closed-shell aryl-azide precursor; no porphyrin atoms enter the metadynamics.
The later pose-feature stage will transform the substrate conformers into the
reaction frame while holding the corresponding porphyrin coordinates fixed.

Implementation details:

1. deterministic ETKDGv3 plus MMFF94/UFF seed generation;
2. CREST 3.0.2 legacy external-xTB quick GFN2 sampling with ALPB ether, a
   30 kcal/mol search window, and genetic crossing disabled because a
   one-member rigid ensemble makes that optional stage abort;
3. CREST/CREGEN uniqueness filtering followed by independent GFN2-xTB/ALPB
   ether single-point reranking;
4. retention of the lowest at most 10 unique conformers, with underfilled
   ensembles reported honestly rather than duplicated;
5. experimental-temperature Boltzmann weights, relative energies, and
   effective conformer count stored per substrate;
6. four one-core workers, 30-second heartbeats, append-only structured and
   human logs, per-substrate raw logs, hashes, and resumable completion checks.

The smoke substrate completed in 152.1 seconds and produced one genuinely
unique minimum. The production run was launched on 2026-09-07 and stopped at
the later agreed decision boundary after the four then-active jobs completed.
It produced complete artifacts for all 40 P7 and 16 CMC-Por substrates. Four
newly auto-started CMC-Por directories (`2o` through `2r`) contain partial raw
logs only and are not counted as results. No chemistry subprocess remained
after interruption.

## P7 predictive-value assessment

The P7 evaluation uses the repository's 38-record modelable cohort and exact
outer leave-one-family-out / inner leave-one-family-out Elastic Net procedure.
Substrates `1ad` and `1z` are non-modelable and `1an` has an achiral product for
which ee is explicitly not applicable. The matched Stage-2p geometry arm
reproduces MAE 8.498, R2 0.476, and RMSE 11.357.

The tested blocks were ten rotation-invariant heavy-atom size/shape descriptors
from the retained CREST minimum and thirteen dense molecule-level GFN2-xTB
descriptors: normalized total/electronic energies, HOMO, LUMO, gap, dipole,
global charge polarization, and atomic-dipole summaries. An initial exploratory
matrix with sparse element-specific charge indicators caused catastrophic
family extrapolation and was rejected as numerically unstable. Full raw values
remain in `features.json`; only the dense molecule-level block enters the
reported comparison. Tests verify rotational invariance and electronic feature
extraction.

The stable electronic augmentation worsened MAE by 0.112 ee points and lowered
R2 to 0.440. CREST geometry worsened MAE by 0.360 and lowered R2 to 0.455. The
combined arm worsened MAE by 0.377 and lowered R2 to 0.429. A deterministic
20,000-draw paired substrate bootstrap gives a combined-arm MAE-improvement
interval of [-1.000, 0.212] ee points and only 0.107 probability of a positive
MAE delta. This fails the locked improvement gate.

All 40 P7 searches returned one unique CREGEN minimum. Consequently retained
count, maximum probability, and effective conformer count are constant at one
and cannot contribute to prediction. This tests free-substrate plausibility
and electronics, not the still-uncomputed compatibility distribution against a
frozen porphyrin.
