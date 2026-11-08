# Corrected pose-coordinate inputs

This archive contains the saved Stage 1 reports and assembly XYZ files used to
regenerate the corrected nitrene-anchored pose descriptors. It includes 140
Stage 1 reports and 28,000 assembly coordinate files: 40 Fe(P7)Cl substrates
with 200 poses each, plus 50 Fe(CMC-Por)Cl substrates with two recorded report
variants and 200 poses per variant.

`pose_coordinate_inputs_manifest.csv` lists each original repository-relative
path, size, and SHA-256 digest. The archive contains the same paths. It has
28,140 file entries, and each entry was verified against the manifest.

To restore the inputs, extract `pose_coordinate_inputs.tar.gz` at the root of a
copy of the project so that the archived `data/...` paths are recreated. Do
not extract over a working data tree without first making a backup.

The coordinates are unchanged source inputs. The correction changes how the
nitrene atom is found in those inputs; it does not regenerate the poses.
