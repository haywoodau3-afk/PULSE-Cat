# Constrained generator execution runbook

Run this only after Gate 1 sign-off. Use a separate Python 3.10–3.12 environment; do not modify the validated analysis environment.

## Environment

```bash
python3.11 -m venv .venv-generator
.venv-generator/bin/pip install -r requirements-generator.txt
```

Clone the pinned SMILES-RNN and PromptSMILES commits from the URLs in `generator-freeze-config.json`. Record commit IDs and dependency lock output.

## Checkpoint

Acquire the official ChEMBL28 prior from the SMILES-RNN project. Compute its SHA-256, write the digest into `generator-freeze-config.json`, and retain the downloaded file in a checksum-addressed artifact store. A missing digest blocks generation.

## Fixed generation

For seeds `1101, 2202, 3303, 4404, 5505`, retain the complete persisted
production output of 10,112 strings per seed (50,560 total) using the scaffold
and attachment points in the freeze config. The original request was 10,000 per
seed; the 112-row batch overrun is recorded explicitly and is not silently
discarded. Record raw strings, seed, prompt, timestamp, runtime, memory, and
model version.

## Deterministic funnel

Apply, in order: RDKit parse/sanitize; canonical deduplication; aryl-azide identity; grammar fixture membership; unique four-bond target; five-member closure; functional-group and azide-safety rules; novelty/applicability features; route and availability review. Persist every rejection reason and never regenerate after prospective outcomes are revealed.

Run the deterministic-enumeration comparator under the same 50,560-candidate
budget. Report contract-valid yield, unique yield, diversity, novelty, route
acceptance, availability hit rate, experimental eligibility, and compute—not
raw validity alone.

## Freeze

Hash the raw and filtered candidate files, record all seeds and software versions, and seal the candidate universe before any Round A outcome is revealed. Only then may the progressive learner rank candidates for human chemistry and EHS review.
