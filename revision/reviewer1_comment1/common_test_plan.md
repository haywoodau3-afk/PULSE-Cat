# Reviewer 1 comment 1: repeated common-test-set plan

## Purpose

Evaluate whether the observed remaining-pool advantage also appears when the compared acquisition routes predict the same held-out substrates. The existing seven-record Fe(CMC-Por)Cl audit is retained as a separate historical check; it is not used to choose this experiment's design.

## Design, recorded before execution

1. Use the same 38 Fe(P7)Cl and 26 Fe(CMC-Por)Cl active ee-labelled records as the shared-start analysis. The seven previously locked Fe(CMC-Por)Cl audit records remain excluded.
2. For each domain, generate 20 distinct outer held-out subsets uniformly without replacement using the reproducible domain-specific seeds 20261108 and 20261109. Hold out six Fe(P7)Cl records and five Fe(CMC-Por)Cl records; keep each complete substrate out of training and acquisition for its split. The remaining active records form the candidate pool.
3. Within each split, draw three distinct unordered two-substrate initial pairs uniformly without replacement from that split's candidate pool. Each pair is shared by uncertainty–diversity, source-order continuation, and random continuation. After the initial pair, source-order continuation selects the earliest remaining record by source order; it is a controlled continuation rather than the original historical trajectory. Average three independently seeded random continuations within each starting pair.
4. Retain the existing representation, acquisition scoring components, Ridge evaluation, prediction bounds and fold-local standardisation. Refit after every acquired label. Score each route on the same outer held-out substrates at 2, 6, 10, 15 and 20 active labels, then average these five MAEs for the route and starting pair. All budgets are feasible in both candidate pools.
5. Compute paired comparator-minus-uncertainty–diversity differences, first average within each outer split over the three starting pairs and, for the random comparator, over the three random continuations, and then summarise the 20 split-level differences. Record means, medians, interquartile ranges, ranges, and the proportion of splits favouring each route. Save split IDs, pair IDs, seeds, budget-level predictions and scores, and provenance.
6. The outer splits overlap and all derive from the same small datasets. A descriptive 95% percentile interval over the 20 split-level effects describes their observed spread; it is not a confidence interval or independent-dataset significance test. An optional split-resampling interval for the mean would measure Monte Carlo variability conditional on these fixed data and the split-generation procedure, not uncertainty for a substrate population. No p-value or broad statistical significance claim will be inferred from overlapping splits.
7. Independently check the reported aggregate scores from saved individual predictions, prevent all held-out and previously locked CMC audit records from entering acquisition or fitting, and report negative or inconsistent results without selecting favourable splits. Record convergence-warning limitations and any deviation before interpretation.

## Intended outputs

- Reproducible scripts, split and seed records, per-substrate predictions, aggregate results, and a brief findings note in the reviewer-comment folder.
- Update the existing draft response and the separate revised manuscript and supporting-information copies, with changes highlighted and limitations made explicit. Keep the original headline trajectory percentages separate from the new common-test results.

## Status

Design was recorded before implementation. Both 20-split analyses have been completed; outputs, verification and limitations are documented in `common_test_results.md`. The revised documents and reviewer response incorporate the results. The intervals remain conditional on the observed datasets and do not establish population-level significance.
