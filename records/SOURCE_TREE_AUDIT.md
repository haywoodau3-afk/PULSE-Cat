# Source-tree audit for the atom-index correction

## Corrected source of record

The corrected revision uses the atom-mapping-aware scripts under the workspace
`scripts/` tree. Their source snapshots, plus the corrected exploratory pose
descriptor script, are included in
`corrected_project/source_scripts/` and hashed in the package manifest. The
nitrene is identified from the molecular graph, then mapped into the assembled
coordinate ordering. The corrected pose-coordinate inputs and their SHA-256
manifest are included under
`corrected_project/input_snapshots/pose_coordinates/`.

The exploratory `docs/research/2026-09-07/pose_probability.py` source also had
the positional assumption and has now been corrected. Its pre-correction
exploratory outputs have not been regenerated and are not used as evidence in
the revised manuscript or supporting information.

## Historical source snapshots

An audit for direct uses of `stage1_to_assembly[0]` and `index_map[0]` found
pre-correction source copies in the frozen package trees `SI/`, `SI2/`, `SI3/`,
and `SI4/`. These include pose-interaction, Stage 2p representation, and
Stage 3a reference-feature scripts. The older copies are retained as historical
package snapshots with their associated outputs and manifests; they are not
the code of record for the corrected manuscript. Their atom-zero references
must not be used to regenerate or validate the corrected claims.

The historical snapshots were not silently rewritten because that would make
their archived output and hash manifests appear to describe the corrected
pipeline when they do not. The corrected, hashed source snapshots in
`corrected_project/source_scripts/` and the revised manuscript/SI in this
folder are the authoritative correction release. Any later journal deposit
should package that corrected release and identify or omit superseded source
snapshots.

## Scope and limitations of the audit

This audit is scoped to source files retained in the workspace and the direct
positional expressions above. It establishes which code snapshot is the basis
of the corrected revision; it does not reconstruct every historical software
environment or every pre-correction intermediate file bit for bit. The
corrected pose-feature regeneration has the original coordinate inputs
available in the archive, but model-selection and analysis results remain
retrospective and do not constitute prospective experimental validation.
