# Reproduction entry points

Run from the repository root. The commands below operate on the frozen
records and do not reveal or fabricate prospective outcomes.

```bash
.venv/bin/python scripts/environment_contract.py
.venv/bin/python scripts/pptl/validate_contract.py \
  --contract scripts/pptl/pptl-contract.json \
  --output scripts/pptl/contract-validation.json
.venv/bin/python scripts/pptl/build_overlap_ledger.py \
  --p7-records data/jacs_2025/stage2/curated-reaction-records.jsonl \
  --cmcpor-records data/expansion/catalyst_rerun/cmcpor/stage2-records.jsonl \
  --output data/expansion/pptl/canonical-overlap-rebuilt.json
.venv/bin/python scripts/pptl/build_model_progression_tables.py
.venv/bin/python scripts/pptl/build_supporting_information.py
```

For the complete structure-only P7 rerun, use the stage-2 scripts and the
released split/prediction artifacts under `SI/prediction-validation/` as the
audit target. For pose, CREST, and xTB regeneration, use the scripts under
`SI/code/feature-source/` and the environment declaration under
`SI/geometry-calculations/xtb/stage3-features/stage3-environment.json`.

Candidate generation is frozen rather than regenerated during ordinary SI
replay. Its checkpoint, commit, seeds, filters, and hashes are in
`SI/candidate-generation/pptl/generator-freeze-config.json`.

