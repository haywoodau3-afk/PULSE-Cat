# Draft response to Reviewer 1, comment 2

## Reviewer comment

The uncertainty-diversity acquisition weights (0.40/0.40/0.20) are presented as a fixed rule without justification for the specific values. No sensitivity analysis is performed to show how the results change when these weights are varied, nor is there evidence that this particular combination is optimal or even reasonable for the studied systems.

## Draft response

We thank the reviewer for noting that the original manuscript did not justify the acquisition coefficients or examine their sensitivity. We have revised the Methods and Supporting Information to describe the weights as a fixed heuristic rather than an optimized or chemically derived rule. We also clarify an implementation detail that affects their interpretation: the operational uncertainty component is `U = 0.5D + 0.5Q`, where `D` is normalized structural novelty and `Q` is normalized disagreement among Ridge, Elastic Net, and Tanimoto-kNN predictions. Thus, the nominal score `0.40U + 0.40D + 0.20C` is implemented as `0.60D + 0.20Q + 0.20C`; the named top-level terms do not represent independent contributions.

We evaluated all 21 non-negative `(D,U,C)` weight combinations on a 0.20 simplex grid, including the original `(0.40,0.40,0.20)` setting. Each combination used the same common held-out splits, initial pairs, model settings, and label budgets in the two catalyst datasets. The default ranked 11th of 21 for Fe(P7)Cl and tied 10th–11th for Fe(CMC-Por)Cl. The lowest observed grid means were 0.53 and 0.66 ee points below the default, respectively, but these grid minima are descriptive and were not used to choose new weights. Results and all combinations are provided in Supporting Information Table S19 and Figure S11.

We have therefore retained the original weights only as the fixed rule used in this retrospective study. We now state that they are not established as optimal or universally preferred, and that prospective calibration would be needed for another reaction context. The revisions appear in the acquisition-score definition and results discussion of the manuscript and in Supporting Information Section S9.

Using the same held-out splits, starting pairs and label budgets, we also compared each weight setting with source-order and random continuations. The mean difference favoured 21/21 Fe(P7)Cl settings and 20/21 Fe(CMC-Por)Cl settings versus source order, with one tie; versus random, it favoured 18/21 and 20/21 settings, respectively. Results varied across individual splits, and these descriptive averages do not establish significance or general superiority. The original mean-prefix metric was not reconstructed for the grid because remaining-pool predictions at every prefix were not saved; the held-out analysis should not be interpreted as sensitivity of the original 55.3% and 33.2% reductions.

## Author-side caveat

The grid is coarse and is evaluated on overlapping splits of the same small datasets; its ranks do not constitute independent validation. Preserve this limitation in the submitted response and manuscript. Do not describe the default as statistically equivalent to alternatives or claim that the grid identified a superior policy.
