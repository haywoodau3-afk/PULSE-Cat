# Data-generation procedure

## 1. Curated reaction records

The P7 and CMC-Por records are copied into `data/jacs_2025/stage2/` and
`data/expansion/catalyst_rerun/cmcpor/`. Retain catalyst, condition, pathway,
record role, substrate identity, mapping/provenance, ee, yield, and missingness
on every row. Validate against the copied schemas and source ledgers. Use the
fixed reaction-centre and five-membered-ring connectivity rules; never infer a
missing outcome.

## 2. Structure features

Generate B1–B5 with the RDKit/Morgan builders in `scripts/pptl/` and the
feature scripts copied under `scripts/`. Generate Stage 2p pose features from
the fixed UFF/constraint workflow, then aggregate catalyst-aware interaction
records for C2. Feature selection, scaling, and projection are fold-local.
Feature manifests record dimensions, schema versions, source records, and
provenance.

## 3. Progressive routes

Use the frozen two-substrate seed and reveal one whole substrate per step.
Build historical, diversity-first, uncertainty-plus-diversity,
performance-first, and random routes. Persist every prefix, prediction,
selection event, seed, route score, and random-replicate summary. Keep ee and
yield as separate target streams.

## 4. Guarded transfer

Run both primary directions with canonical-overlap exclusion. Fit every expert
before revealing the target row; score the row; update only after scoring.
Persist expert predictions, guarded weights, cumulative losses, suppression
events, and shadow predictions. Produce the B1–B5/P0–P4 matrices and paired
scaffold/bootstrap diagnostics.

## 5. Candidate generation

The persisted generator data use five seeds and retain 10,112 rows per seed,
for 50,560 raw strings. Apply parsing, canonical deduplication, aryl-azide
identity, grammar, unique four-bond target, five-member closure,
functional-group/azide safety, novelty/applicability, and target-definition
gates in that order. Persist accepted rows and every rejection reason. Run the
deterministic enumeration comparator under the same budget. Seal the 8+8
panel before any prospective outcome is revealed.
