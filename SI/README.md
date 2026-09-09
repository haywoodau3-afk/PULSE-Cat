# Supporting Information release map

**Study:** parallel progressive transfer learning for Fe(P7)Cl and CMC-Por-FeCl

**Inventory date:** 2026-09-09

This folder is the organized companion data/code package for the final
Supporting Information PDF, [`PULSE-Cat-Supporting-Information.pdf`](PULSE-Cat-Supporting-Information.pdf).
It does not invent missing experimental measurements. Large existing artifacts
are exposed through relative links to the repository's canonical data trees or
to the earlier SI2/SI3 packages while this working tree is used; the submission
archive must resolve those links into file contents. The `procedure/si2-manifest.json`,
`procedure/si3-manifest.json`, `procedure/si4-manifest.json`, and
`procedure/compact-si-data-manifest.json` files provide file-level provenance
for the existing packages.

## Quick start

| Need | Location in this SI folder |
| --- | --- |
| Curated records, SMILES, outcomes, conditions, and source provenance | [`curated-datasets/`](curated-datasets/) |
| Held-out predictions, splits, feature matrices, route and transfer metrics | [`prediction-validation/`](prediction-validation/) |
| Exact acquisition, transfer, metric, and candidate-screen definitions | [`algorithms/ALGORITHM_SPECIFICATIONS.md`](algorithms/ALGORITHM_SPECIFICATIONS.md) |
| Catalyst structures, poses, density fields, CREST, xTB, and logs | [`geometry-calculations/`](geometry-calculations/) |
| Generator streams, funnel records, applicability labels, and proposal panels | [`candidate-generation/`](candidate-generation/) |
| Analysis scripts, feature-generation source, dependencies, and replay notes | [`code/`](code/) and [`procedure/`](procedure/) |
| Figures and plot data | [`figures/`](figures/) and [`procedure/source-tables/`](procedure/source-tables/) |
| Current Data Availability Statement | [`DATA_AVAILABILITY_STATEMENT.md`](DATA_AVAILABILITY_STATEMENT.md) |

## Status legend

- **Available** — the requested evidence is present and linked below.
- **Available with limitation** — the artifact exists, but its scope or
  interpretation must be stated explicitly.
- **Pending release action** — the scientific record exists locally, but a
  repair, author decision, or persistent public location is still needed.
- **Not available by design** — no such measurement was made under the current
  retrospective/prediction-only study boundary.

## Requested SI contents and current status

### 1. Curated substrate datasets

**Status: Available, with documented curation limitations.**

- P7: 41 retained records in [`curated-datasets/p7-records.jsonl`](curated-datasets/p7-records.jsonl).
- CMC-Por: 50 retained records in [`curated-datasets/cmcpor-records.jsonl`](curated-datasets/cmcpor-records.jsonl), split into 33 aryl records and 17 sulfonyl control records.
- Starting-material tables, candidate sites, atom mappings, reaction-centre
  decisions, and validation records are in [`curated-datasets/`](curated-datasets/).
- P7 reaction conditions and the 16-condition optimization table are in
  [`p7-optimization-conditions.csv`](curated-datasets/p7-optimization-conditions.csv).
- Literature locations are carried in the source fields of the JSONL records
  and in the linked source-ledger/SMILES tables. The local Angewandte PDF is
  available at the repository root; the P7 source locations are recorded by
  document ID and page/table in the source ledger.
- `dataset-id-lists.csv` is the explicit count reconciliation for all analysis
  populations. `1z`, `1ad`, and `1an` are exclusions for different reasons;
  they must not be silently treated as zero outcomes.

**Limitation:** 29 P7 records have no curated product mapping. Their starting
structures and experimental labels are retained; product fields remain null
and are not reconstructed or imputed.

### 2. Prediction and validation records

**Status: Available.**

- Row-level structure-only predictions, observed values, residuals, split IDs,
  validation MAE, and selected estimator parameters are in
  [`prediction-validation/p7-model-reports/`](prediction-validation/p7-model-reports/).
- Family-held-out and target-held-out split membership is in the same report
  tree (`full-scope-structure-splits.json` and
  `family-heldout-ee-splits.json`, plus the yield equivalents).
- Structure, pose, and yield matrices are in
  [`prediction-validation/p7-stage2/features/`](prediction-validation/p7-stage2/features/).
- Reciprocal B5/P3/P4 transfer matrices, 500-route records, scaffold
  replays, and bootstrap summaries are in
  [`prediction-validation/transfer-and-route-artifacts/`](prediction-validation/transfer-and-route-artifacts/).
- The bootstrap inputs are the released row-level prediction/route records;
  the corresponding scripts, replicate counts, and random seeds are in
  [`code/scripts/pptl/`](code/scripts/pptl/) and the algorithm specification.

### 3. Complete algorithm specifications

**Status: Available.**

[`algorithms/ALGORITHM_SPECIFICATIONS.md`](algorithms/ALGORITHM_SPECIFICATIONS.md)
consolidates the implementation-level definitions for uncertainty, novelty,
family coverage, performance score, normalization, nearest-neighbor use,
initial substrate selection, tie-breaking, transfer weights and safeguards,
MAE/RMSE/R², bootstrap intervals, learning-curve AUC, and `n90`. The frozen
machine-readable transfer contract is linked as
[`algorithms/pptl-contract.json`](algorithms/pptl-contract.json).

### 4. Geometry and calculation files

**Status: Available, with conditional interpretation for exploratory branches.**

- Fixed P7 and CMC-Por catalyst references, constraints, Stage 1 retained
  poses, acceptance reports, and assemblies are under
  [`geometry-calculations/pose/`](geometry-calculations/pose/).
- Stage 2/2p/2pp feature JSONL files and manifests are included with the pose
  trees. The 91 per-substrate occupancy representations are under
  [`p7-density/`](geometry-calculations/p7-density/) and
  [`cmcpor-density/`](geometry-calculations/cmcpor-density/); the matching SVG
  views are retained beside them.
- The 13 canonical shared-substrate overlays are indexed in
  [`procedure/source-tables/si_pose_overlay_index.csv`](procedure/source-tables/si_pose_overlay_index.csv)
  and represented by the paired-pose/overlay artifacts.
- CREST/xTB structures, output files, and logs are under
  [`geometry-calculations/crest/`](geometry-calculations/crest/) and
  [`geometry-calculations/xtb/`](geometry-calculations/xtb/).
- Exact feature-column definitions are in the Stage 2p/Stage 2pp manifests,
  [`procedure/si2-data-dictionary.md`](procedure/si2-data-dictionary.md),
  and the feature-source code.

**Limitation:** the substrate-only CREST branch is exploratory. It has one
completed conformer per completed substrate and incomplete CMC-Por coverage;
it must not be described as a complete 50-substrate ensemble study or as
electron-density data. Pose-derived occupancy is geometric occupancy, not
quantum electron density.

### 5. Candidate-generation and proposal records

**Status: Available for the frozen comparison, with an explicit documented exclusion.**

- Generator configuration, SMILES-RNN checkpoint provenance, five seeds,
  raw streams, enumeration vocabulary, funnel rejection reasons, and hashes
  are under [`candidate-generation/pptl/`](candidate-generation/pptl/).
- The generator has 50,560 persisted raw rows, 9,184 unique canonical
  structures, 563 contract-valid structures, and 483 contract-valid
  structures inside the applicability domain (`max Morgan Tanimoto <= 0.35`).
- The equal-budget enumeration comparator has 50,560 raw rows, 25,955 unique
  structures, 18,545 contract-valid structures, and 18,350 in-domain
  structures.
- The 500-candidate diversity sample is a diagnostic stratified screening
  sample (`stratified_screening_pool_per_provenance=500` in the freeze config).
  It is not the final generated pool. The final generated pool is the 483-row
  contract-valid/in-domain set after the frozen filters.
- The 16-substrate development shortlist and the sealed 8+8 prediction-only
  panel, including round assignments and lock hashes, are linked in the
  candidate-generation tree.
- The 127 eligible omitted enumeration candidates are not chemically absent:
  they are the rows in `funnel-enumeration-ad.csv` with IDs in
  `enum-050000`–`enum-050559`, `contract_valid=true`, and
  `ad_status=in_domain`. The exact extracted rows are listed in
  [`candidate-generation/omitted-127-eligible-enumeration-candidates.csv`](candidate-generation/omitted-127-eligible-enumeration-candidates.csv).
  The current EE scoring table stops at row 49,999, so these candidates remain
  unscored. The final PDF explicitly excludes them from the frozen scored
  population; no prediction is imputed. A future rerun would be a new
  versioned comparison, not a silent repair to the reported statistics.

### 6. Reproducible code and data release

**Status: Local replay package available; public release metadata pending.**

- Analysis and validation scripts are linked under [`code/scripts/`](code/scripts/).
- Feature-generation source is linked under [`code/feature-source/`](code/feature-source/).
- Analysis and generator dependency declarations are linked under
  [`code/requirements.txt`](code/requirements.txt) and
  [`code/requirements-generator.txt`](code/requirements-generator.txt).
- The recorded software versions and external commit/checkpoint pins are
  summarized in [`code/SOFTWARE_VERSIONS.md`](code/SOFTWARE_VERSIONS.md).
- The local package manifests and compact SI manifest are linked under
  [`procedure/`](procedure/).
- Replay commands and claim boundaries are documented in
  [`code/REPRODUCE.md`](code/REPRODUCE.md)
  and the linked procedure documents.

## Submission checks and remaining limitations

| Gap | Current evidence | Closure action | Release output |
| --- | --- | --- | --- |
| 127 eligible enumeration candidates have no EE prediction rows | The final PDF and `omitted-127-eligible-enumeration-candidates.csv` explicitly document their exclusion from the frozen 18,223-row scored population | No action is needed for the reported comparison; rerun only as a separately versioned analysis | Explicit exclusion record and unchanged frozen statistics |
| Public archive URL/DOI is not claimed | Final PDF S9.8 specifies delivery as the companion `SI.zip` file | Provide the materialized companion archive with the manuscript; add a DOI only if the journal requires one | `SI.zip` plus the final PDF |
| Exact environment reconstruction is not guaranteed | Runtime versions, requirements, and external commit/checkpoint pins are recorded; no complete lockfile/container digest is claimed | Retain the limitation in the submission; add a lockfile only if required by the journal | `code/SOFTWARE_VERSIONS.md` and requirements files |
| Transfer contract and implementation contain distinct safeguards | Final PDF S7/S9.3 discloses the absolute-error implementation rule and the unestablished relative-family contract threshold | Preserve the disclosure and do not claim that the complete acceptance criterion was met | Contract, implementation, and methods text |
| Public SI archive must not depend on relative links | This working SI map reuses existing large artifacts through symlinks | Materialize with links resolved and validate the archive before submission | Self-contained `SI.zip` |
| Additional internal diagnostics are not part of the final narrative | The final PDF defines the reported populations and claim boundary; generated outcomes, supplier evidence, route acceptance, and safety review are prediction-only or outside scope | Do not add invented values; retain the stated study boundary | Final PDF S9.8 and this package |

## Release boundary

The current study supports retrospective prediction, directional transfer
diagnostics, geometry/feature provenance, and prediction-only candidate
generation. It does not contain experimental outcomes for the generated panel,
the five P7 prediction-only substrates, supplier evidence, route acceptance,
safety review, or a closed-loop laboratory result. Those are not missing
records to be filled with estimates; they require new experimental or
procurement work and are outside the present computational claim.

## Submission procedure

For the journal upload, provide the final PDF together with a materialized
archive of this directory. The working tree contains symlinks so that the
repository does not duplicate approximately 1 GB of existing artifacts. From
the repository root, resolve them before creating the companion archive:

```text
rsync -aL SI/ /path/to/materialized/SI/
cd /path/to/materialized
zip -r SI.zip SI
```

The archive must contain file contents rather than symlinks. The final PDF's
S9 section is the authoritative map for what is included and how the reported
exclusions and study boundaries should be interpreted.
