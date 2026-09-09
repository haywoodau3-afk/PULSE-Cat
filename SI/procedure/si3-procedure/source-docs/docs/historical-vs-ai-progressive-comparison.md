# Historical order versus model-guided progressive learning

## Scope of this claim

This is a computational, retrospective benchmark. It uses the locked labelled
records for P7 and the CMC-Por aryl subset. `historical_order` reproduces the
order in which the source paper lists its substrates (`source_order`); it is a
non-optimised control and does not claim to reconstruct the authors' private
decision process. The AI comparison uses the deterministic model-guided
`uncertainty_diversity` policy selected from the pre-specified acquisition
routes. The primary model is Ridge on the locked `rdkit_morgan_stage2p`
representation and the target is unsigned enantiomeric excess (`ee_percent`).

The generated aryl-azide structures are proposals only. They have predicted ee
values and morphology labels, but no experimental outcome is assigned. They
must therefore be reported as a prospective design set, not as prospective
validation.

## Retrospective result

Mean prefix MAE is the mean absolute error averaged over every labelled prefix
in the progression. Lower is better. The route rank is within the five routes
evaluated by the existing workflow (three deterministic policies, historical
order, and the 500-replicate random control).

| Catalyst/domain | Historical mean prefix MAE | Historical rank | Best AI route | Best AI mean prefix MAE | AI rank | Reduction versus historical |
|---|---:|---:|---|---:|---:|---:|
| P7 | 21.672 ee points | 5/5 | uncertainty + diversity | 9.684 ee points | 1/5 | 55.3% |
| CMC-Por aryl | 13.155 ee points | 3/5 | uncertainty + diversity | 8.787 ee points | 1/5 | 33.2% |

The corresponding prefix-MAE sums (the workflow's `auc_mae` diagnostic) are
780.20 versus 348.62 for P7 and 315.72 versus 210.88 for CMC-Por aryl. The
historical route never met the workflow's 90%-error-reduction diagnostic for P7;
for CMC-Por aryl it first met that diagnostic at 16 labelled substrates,
whereas the best AI route met it at 8. This threshold is a predefined learning
diagnostic, not a claim of chemical success.

These numbers support the narrow statement that, in retrospective replay of
the observed ee labels, model-guided progressive ordering reduced prediction
error more quickly than the source-paper order. They do not show that the AI
will discover higher ee chemistry, because no generated candidate has a revealed
outcome.

## Where the generative copilot fits

The non-LLM SMILES-RNN + PromptSMILES branch generated a frozen, contract-valid
aryl-azide universe. Its progressive policy ranks candidates using the frozen
ee predictor plus uncertainty/diversity and morphology coverage. The sealed
8+8 panel records the resulting Round A/Round B proposals and the matched
deterministic-enumeration comparator. The `predicted_ee` field is explicitly a
model output; `outcome_ee` remains blank and `outcome_revealed=false`.

Accordingly, the manuscript should present two separate figures/tables:

1. **Retrospective learning curve:** historical order versus model-guided
   progressive routes on P7 and CMC-Por aryl, with prefix MAE and uncertainty
   bands where available.
2. **Design proposal panel:** generated starting-material SMILES, morphology
   family, predicted ee, applicability status, and round assignment. Caption
   the panel as computational proposals and do not call it prospective
   experimental validation.

The machine-readable source for the comparison is
`data/expansion/pptl/historical-vs-ai-progressive-comparison.json` (with the
route-level CSV beside it). The proposal lock is
`data/expansion/pptl/sealed-prospective-panel-lock.json`.

## Publication wording and limitation

Safe wording is: “A leakage-controlled retrospective replay found that
uncertainty–diversity progressive acquisition lowered prefix ee prediction MAE
relative to the historical substrate order in both catalyst domains. A frozen
non-LLM generator then proposed aryl-azide starting materials for a prospective
design panel.”

Do not write “the generator improved enantioselectivity,” “the AI discovered
better substrates,” or “the closed loop was validated.” Those statements require
revealed experimental ee labels. The computational paper can still be complete
as a methods/design study if this limitation is made explicit and the claims are
restricted to retrospective learning efficiency and prediction-only substrate
proposal.
