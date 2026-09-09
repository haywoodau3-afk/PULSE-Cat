# Supporting-information output package

This folder is the SI-ready package for manuscript checkpoints 1–9. It contains the assembled Markdown draft, publication figures, substrate/pose tables, the provenance manifest, and the reproducibility builder script.

## Contents

- `supporting-information.md` — assembled supporting-information text.
- `manuscript-introduction.md` — manuscript-ready introduction summarizing checkpoints 1–9, with a clearly marked checkpoint 10 placeholder.
- `manuscript-methods-and-data-availability.md` — concise methods, reproducibility, data-availability, and software/library-availability text with repository placeholders.
- `manuscript-results.md` — factual, numerical Results section covering the frozen checkpoint 1–9 analyses without figures or literature comparison.
- `figures/` — independent, model-variant, representation-version, progressive-transfer, and pose-overlay graphics (SVG).
- `tables/si_substrate_smiles.csv` — starting/product SMILES and associated record metadata.
- `tables/si_pose_overlay_index.csv` — canonical pose-pair index with source SVG paths and hashes.
- `si_data_manifest.json` — provenance, sizes, and SHA-256 hashes for the source artifacts.
- `raw-data/` — self-contained, file-level raw-data deposit organized by scientific stage, with CSV/JSON checksums.
- `si_completeness_audit.md` — checkpoint-to-claim-to-raw-data completeness matrix and manuscript limitations.
- `si_model_progression_tables.xlsx` — workbook with separate experiment-inventory, feature-arm, representation-progression, independent-progression, holdout-comparison, and notes sheets.
- `build_model_progression_tables.py` — reproducible extractor for the progression tables.
- `checkpoint-1-9-manuscript-freeze.md` — frozen checkpoint scope, exclusions, and claim boundary.
- `pptl-final-report.md` — detailed PPTL analysis report retained for manuscript drafting.
- `build_supporting_information.py` — the generator used for the canonical SI source package.

XYZ coordinate files are intentionally not included because they were deferred for this manuscript package. All other supporting source records, non-XYZ conformers, full learning-curve rows, feature matrices, predictions, numerical density arrays, transfer replicates, and generator outputs are copied into `raw-data/`.

To regenerate the canonical package from the repository root, run:

```bash
.venv/bin/python scripts/pptl/build_supporting_information.py
```

The canonical generated files are written under `docs/supporting-information*`; this folder is the frozen delivery copy.
