# Checkpoint 10 procedure: 0–100 substrate-development map

## Inputs

Checkpoint 10 reads, for P7 and CMC-Por independently:

- curated substrate records and SMILES;
- replicate-0 progressive selection events from sequential step 3 onward;
- frozen convergence manifests containing Ridge AUC-MAE and n90.

The source files are copied under `data/`. The implementation and regression
tests are under `checkpoint-10/`.

## Procedure

1. Parse and sanitize the proposed SMILES with RDKit.
2. Remove atom-map labels and generate a canonical SMILES plus a radius-2,
   1,024-bit Morgan fingerprint.
3. Select positive and negative route evidence from the minimum and maximum
   deterministic Ridge AUC-MAE, respectively, for the requested domain and
   target. Random routes are benchmarks and are not assigned polarity.
4. Compare the query with historical route-event substrates using Tanimoto
   similarity and proposed-versus-observed sequence-position fit.
5. Pair route placements for shared substrate IDs and calculate a similarity-
   weighted timing contrast.
6. Calibrate the contrast by the positive/negative AUC gap and clamp the final
   recommendation to 0–100.
7. Report score band, confidence, analogue evidence, contract warnings, and
   the explicit interpretation boundary.

## Interpretation

High scores mean that the proposed substrate/position resembles placements
associated with faster retrospective convergence. Low scores mean that it
resembles slower placements or fails the frozen substrate contract. The score
does not estimate yield, ee, reaction success, safety, availability, or
synthetic feasibility. Low analogue coverage should be treated as weak
evidence even if the numeric score is favourable.

For the whole-scope question, use `--recommend-route`. This ranks actionable
routes by equal-panel normalized AUC-MAE across P7/CMC-Por and ee/yield; n90
and random-route performance remain secondary diagnostics.
