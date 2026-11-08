# Reviewer 1 comment 1: revision and computational experiment plan

## Objective

Assess how sensitive the reported acquisition comparison is to the initial measured substrates, and report the limits of the evidence. Retain the original reported-order and uncertainty–diversity trajectories as descriptive results. Do not present a new replay as an exact reconstruction without verification.

The author confirmed this interpretation: the reviewer asks for uncertainty around the headline comparisons and evidence about sensitivity to the initial substrate pair. Report weaker or inconsistent findings if observed and adjust the claims accordingly. A starting-pair analysis is conditional on the two observed datasets; it does not by itself quantify uncertainty over a wider substrate population.

Terminology: an **initial substrate pair** is the two observed substrates at the start of one replay. It is different from the project's 12-substrate **Seed Set** in the root context and from a pseudorandom seed used to reproduce a computation. A **shared-pair comparison** starts each compared route with the same initial pair, while subsequent remaining evaluation pools may diverge.

## 1. Check reproducibility and inputs

- Confirm the 38 Fe(P7)Cl and 26 Fe(CMC-Por)Cl ee populations, exclusions, feature matrices, source ordering, and model settings against the archived records and manifests.
- Recalculate the reported mean-prefix MAEs from the existing learning curves and compare a current-code replay with the archived trajectories. Record any differences and their likely causes; the original run-specific random seeds and complete prediction-level archives are not established for every run.
- Retain all models used in the acquisition uncertainty calculation, even if Ridge is the reported prediction model. Record versions, random seeds, and input hashes for new runs.

## 2. Main experiment: vary the initial substrate pair

- Before inspecting the outcomes, select 50 distinct initial pairs per catalyst using a recorded pseudorandom seed. Record the pair IDs and any eligibility rules.
- Use a dedicated wrapper or scoped copy inside this folder: the existing program assigns deterministic routes a fixed pair and changing its pseudorandom seed does not vary that pair. Keep original project code and archived outputs intact.
- For each pair, start uncertainty–diversity and a reported-order continuation from the same two substrates. The latter follows source order for the remaining eligible candidates. Retain the current representation, pool, Ridge evaluation, label budgets, and mean-prefix MAE; confirm that both routes use identical budgets.
- For context, include random continuation from the same initial pair. If feasible, repeat its random continuation several times per pair and describe the aggregation.
- Prespecify three random continuations per pair where computationally practical; otherwise record the actual number and why it changed. Average those continuations within the pair before comparing with the uncertainty–diversity result.
- For each catalyst, report the paired difference in mean-prefix MAE across initial pairs, its median and spread, and the fraction of pairs favouring uncertainty–diversity. Present both absolute ee-point differences and, where the denominator is well defined, relative differences.
- Report a 95% interval for the average paired difference by resampling whole initial-pair results, if appropriate; distinguish this interval from the spread of individual outcomes. Both describe the selected initial-pair distribution conditional on the fixed datasets, not uncertainty across new catalyst systems. Do not treat learning-curve prefixes as independent replicates.

## 3. Small complementary checks

- Plot the two original trajectories alongside the across-pair distribution, clearly distinguishing the historical route-specific starting pairs from the new shared-pair replays.
- Evaluate a common held-out prediction set as a secondary sensitivity analysis only if a scientifically defensible split leaves enough data. Prespecify the split and avoid tuning on locked audit records. If it is infeasible, explicitly state that the original remaining-pool evaluation differs by route.
- The Fe(P7)Cl late-stage records have no measured outcomes and cannot be used as a labelled holdout. The Fe(CMC-Por)Cl archive identifies seven locked labelled audit records; preserve their locked status and do not choose the main analysis using their results.
- Prespecified secondary check: the seven locked Fe(CMC-Por)Cl audit records all have ee labels. If the primary replay runs successfully, evaluate the two deterministic routes from the same 50 initial pairs on this fixed set at 6, 13 and 20 labelled active substrates. Summarise the mean MAE across these three budgets and paired differences across pairs; do not use the audit results for choosing weights, pairs, or policies. The seven-record test set and its selection limit generalisation. Do not treat the unlabelled Fe(P7)Cl late-stage set as a test set.
- The original fitting code suppresses Elastic Net convergence warnings. Preserve the original algorithm for comparability, and explicitly report that absence of warnings is not proof of convergence.
- If the full replay cannot be reproduced, document the discrepancy, retain the original results as archived descriptive values, and report any new replay as a separately defined analysis. The 500 existing random-route trajectories provide context but do not establish uncertainty–diversity stability across starting pairs.

## 4. Changes to manuscript and supporting information after results are available

- **Methods:** identify the original route-specific starting pairs; describe the shared-pair selection, comparator, metric, and uncertainty summary for the new analysis.
- **Results:** keep the 55.3% and 33.2% figures explicitly tied to the original trajectories. Add a concise summary of the new results, including negative or inconsistent outcomes.
- **SI:** provide pair IDs, seeds, configurations, a compact results table, learning-curve summaries, and reproducibility limitations.
- **Abstract and conclusions:** state only what the repeated analysis supports and retain the retrospective, dataset-specific limitation.
- **Response to reviewer:** explain what was tested, what the intervals mean, and where the changes appear. Do not assert statistical significance without a prespecified, defensible analysis.

## Status

Plan recorded before implementation. Reviewer concern and evidence-independent reporting principle confirmed with the author. Reproduction checks, both 50-pair experiments, and the prespecified CMC fixed-audit check have been completed. The subsequent `common_test_plan.md` was recorded before carrying out the repeated common-test-set analysis; its results are in `common_test_results.md` and the latest highlighted Word copies. No formal hypothesis test is claimed. Confirm submission location for the supplementary data and code before sending the revision.
