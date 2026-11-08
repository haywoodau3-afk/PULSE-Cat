# Reviewer 1 comment 6: proposed analysis plan

## Question to confirm

The reviewer challenges the inconsistent and sometimes worse yield performance under uncertainty–diversity. The response should determine how reproducible that observation is on common held-out substrates, investigate observable features of prediction and selection that might explain it, distinguish supported computational mechanisms from chemical hypotheses, and narrow claims where warranted. A retrospective dataset cannot establish a chemical mechanism of yield loss.

## Definitions

- Isolated yield is the measured yield endpoint, distinct from conversion and ee magnitude; an unreported yield is missing, not a zero.
- An acquisition effect is the difference between predictive errors under two selection policies with matched starts, test records, label budgets and estimator. It need not predict which policy maximizes isolated yield.
- An explanatory diagnostic is evidence about model and data behaviour. Association or selection frequency is not proof of a chemical causal mechanism.

## Before outcome analysis

1. Confirm the above interpretation with the user. Inspect the independent progression records, dataset and source provenance. Identify numeric ee-and-yield overlap per system; exclude missing outcomes, preserve the seven locked Fe(CMC-Por)Cl audit substrates, and avoid the known sulfonyl 6q censored-yield issue by restricting to the original aryl cohort. Record the exact populations and exclusions and verify features and target labels.
2. Document the originally reported yield results and clarify that reported-order and other remaining-pool trajectories use different evaluation sets, so their differences alone do not establish common-test effects. Do not equate yield with conversion or claim unavailable reaction failures.

## Prespecified computational analysis

3. If adequate paired records exist, use 20 deterministic overlapping common-test splits per system, holding out six P7 or five CMC aryl substrates, with three common initial pairs per split. Run each endpoint separately on the same paired substrate population, same splits, starting pairs and budgets 2, 6, 10, 15 and 20. Use the existing 1,287-field feature matrix, frozen uncertainty–diversity rule and Ridge model; compare source order, uncertainty–diversity and the mean of three random continuations. Each model only sees labels for its own endpoint; no acquisition decision sees held-out labels. The same split/seed design permits a descriptive endpoint comparison but does not match the original trajectory's estimators, pool or AUC metric. Record split-level, per-budget and route-specific predictions and sequences.
4. Diagnose yield, without tuning the method: compare yield target distribution and apparent ee–yield association; quantify between-route overlap and yield values of selected substrates only after selection; evaluate errors and route differences by held-out record and budget; examine whether observed yield uncertainty is associated with absolute prediction errors, if the existing uncertainty score can be reconstructed without leakage. Treat correlations and patterns as descriptive and post hoc, and do not infer reaction pathways, measurement error or causality. If one check is unidentifiable, report the limitation rather than manufacture an explanation.
5. Preserve source data and production code. Independently check split memberships, locked audits, endpoints, no leakage, route scores and prediction/MAE recalculation; save seeds, software versions, input hashes and scripts. Describe overlapping splits and small reported-scope datasets, not population-level significance.

## Writing and system adjustments

6. Record all findings and limitations in the comment folder and draft a point-by-point reply. Revise the cumulative comment 5 manuscript and SI to present the numerical common-test yield results, defensible data-level explanation, possible nonexclusive chemical contributors explicitly as hypotheses, and limitations; highlight new changes. Avoid unsupported claims that acquisition universally fails or is broadly effective for yield. Render and inspect the documents. No mechanistic experiment or prospective laboratory validation will be claimed.

## Status

Plan recorded before numerical outcome analysis or document editing; user confirmation of the interpretation is pending.

## Initial availability check

In the original active ee cohorts, all 38 Fe(P7)Cl and all 26 Fe(CMC-Por)Cl aryl records have numeric yield and ee fields. This is a field-availability check, not independent verification of reported yield values or a completed outcome analysis. The requested paired endpoint design is therefore feasible subject to provenance and censoring checks.

## Confirmed implementation details before computing yield outcomes

The user confirmed the interpretation. Both endpoint labels are present in every active record (38 P7 and 26 CMC aryl). To ensure exact endpoint pairing, reuse the already recorded comment 1 outer split IDs, initial pairs, ee predictions and selection paths rather than regenerate the same ee results; rerun yield using those same designs and original frozen scoring. The existing score defines uncertainty as half novelty and half min–max-normalised inter-model disagreement; consequently the nominal 0.40 diversity + 0.40 uncertainty + 0.20 coverage score also assigns weight to structural novelty through the uncertainty term. This is an algorithmic explanation, not evidence of a chemical mechanism. Separate held-out-set uncertainty calibration is not prespecified unless the score can be reconstructed on a meaningful candidate reference pool without leaking outcomes.

## Completion

The common-test yield replays and score diagnostics were completed and independently checked; findings, limitations and required writing/system adjustments are recorded in `results_and_adjustments.md`. No calibrated held-out uncertainty analysis was claimed because min–max candidate scoring is reference-pool dependent; no mechanism was experimentally established.
