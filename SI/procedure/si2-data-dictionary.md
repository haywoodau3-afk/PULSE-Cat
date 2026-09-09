# SI2 data dictionary

| Block | Granularity | Main fields/files | Units or encoding |
| --- | --- | --- | --- |
| Curated records | substrate/reaction | `data/inputs/*curated-reaction-records.jsonl` | JSONL; ee/yield in percent; coordinates in Å |
| RDKit descriptors | substrate | `rdkit-morgan-features.csv` | numeric; descriptor-specific, see `METHODS.md` |
| Morgan B5 | substrate | `morgan_r2_bit_0000`–`morgan_r2_bit_1023` | binary 0/1; radius 2; 1,024 bits |
| Tier 1 Morgan | substrate + candidate site | `p7-tier1.jsonl` | binary 0/1; radius 2; 2,048 bits; chirality-aware |
| Stage 1 pose reports | substrate + pose | `data/pose/*/stage1-reports/` | JSON; UFF score in kcal/mol proxy units; atom maps are 1-based in metadata |
| Stage 1 coordinates | pose/assembly | `data/pose/*/geometries/` | XYZ coordinates in Å; SDF conformers |
| Stage 2p | substrate | `stage2p-features.jsonl` | 248 numeric geometry summaries; Å/degrees/fractions as named |
| Stage 2 pose interactions | pose + substrate | `pose-interaction.jsonl` | repeated pose rows plus aggregate numeric leaves |
| Stage 2pp | substrate | `stage2pp-features.jsonl` | 655 numeric geometry/occupancy features |
| Stage 2pp density | substrate/view | `density/*.npz` | numerical occupancy arrays in the reaction frame |
| Stage 2pp views | substrate | `svg/*.svg` | rendered occupancy diagnostics |
| Stage 3a references | candidate site | `stage3a-lite-reference-summary.jsonl` | xTB energies in Hartree; distances in Å; angles in degrees |
| Stage 3a local shells | pose/candidate site | `local-3d-shell-*.jsonl` | atom counts/distances by fixed Å shells |
| Stage 3b BDE | candidate site | `bde.jsonl` | BDE in kcal/mol; ranking is within substrate |
| CREST/GFN2-xTB | substrate/conformer | `data/crest/ensembles/` | energy fields in Hartree; probabilities dimensionless; temperature in K |

## Status labels

- `feature_ready`: record passed the frozen structure/metadata checks needed for
  the canonical feature path.
- `atom_mapped`: atom mapping exists, but the record is not necessarily in the
  feature-ready seed set.
- `completed`: calculation returned valid output under the script contract.
- `underfilled`: the requested ensemble size could not be reached; the actual
  unique count is retained without padding.
- `uncalibrated_xtb`: xTB-derived BDE has not been calibrated to a higher-level
  reference.
- `prediction_only`: generated candidate has no experimental outcome attached.

## Important distinctions

`data/rdkit-morgan/p7-tier1.jsonl` is not the same representation as
`rdkit-morgan-features.csv`: the former is candidate-site-aware and uses
2,048-bit chirality-aware Morgan fingerprints; the latter is the structure-only
B5 table with 1,024 non-chiral bits. Similarly, Stage 2p/2pp geometric
occupancy is not xTB electron density, and CREST Boltzmann weights are not
catalyst-pocket compatibility probabilities.
