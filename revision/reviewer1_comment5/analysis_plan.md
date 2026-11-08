# Reviewer 1 comment 5: aryl and sulfonyl scope plan

## Agreed question

Explain why the original Fe(CMC-Por)Cl acquisition analysis was restricted to aryl azides, test the practical effect of including available sulfonyl records where the source supports it, and limit conclusions to the populations actually evaluated. A retrospective simulation cannot identify the true bias relative to unreported experiments or validate a future laboratory workflow.

## Source and feature reconciliation, before outcome analysis

1. Reconcile the curated 33 aryl and 17 sulfonyl records with the source paper and its Supporting Information. Verify catalyst identity, ee labels, structures and recorded reaction conditions; separate known values from assumptions in the curated ledger. The source paper is Wang et al., Angew. Chem. Int. Ed. 2023, 62, e202218577 (https://doi.org/10.1002/anie.202218577). The source SI is `expand/10.1002:anie.202218577/anie202218577-sup-0001-misc_information.pdf`. Preserve the previously locked seven aryl audit records; do not use them for fitting, acquisition or test. Check unique identity, nonmissing outcome and Stage 2p feature coverage, reactive-site assignments, and class labels. Describe the original aryl restriction as the documented analysis scope, not as a post hoc explanation of the authors' motives.
2. Record any label/catalyst or condition ambiguities rather than assuming the curated metadata is per-substrate verified. If mismatches are material, stop or restrict analysis to verifiable records, and distinguish simulations conditional on curated inputs from validated literature data.

## Prespecified retrospective comparison if the records support it

Use the existing PULSE-Acquire feature set and Ridge scoring with default frozen weights and the prior common-test approach. Compare the original aryl-only candidate pool with an expanded mixed aryl/sulfonyl pool; both use the same held-out sets and same two aryl initial substrates, so the mixed pool has access to extra sulfonyl labels while both begin from the same start. Use 26 active aryl and 17 sulfonyl records, with 20 deterministic stratified splits (3 aryl + 2 sulfonyl held out), three shared aryl starting pairs per split, and label budgets 2, 6, 10, 15 and 20. Preserve the locked seven aryl records outside all sets. For source-order continuation, uncertainty–diversity, and three seeded random continuations per starting pair, compute MAE on the same aryl and sulfonyl held-out records separately and pooled. Average over five budgets and initial pairs within each split, and random replicates before comparing policies. Record per-class acquisition counts, per-budget predictions and sequences. The aryl-only model's sulfonyl predictions are cross-class extrapolations; mixed-pool predictions can use sulfonyl labels. Candidate pools differ deliberately, so comparisons estimate a combined effect of available pool, training composition and selection rule, not the isolated effect of adding a sulfonyl substrate. The two-class split is tiny, overlapping, and stratification fixes test-class proportions; it is not an independent prospective test.

Run a separate sulfonyl-only replay if source checks and chemistry-aware feature coverage are adequate: 20 deterministic splits with three sulfonyl held out, three shared initial pairs per split, budgets 2, 6, 10 and 13, and the same three routes with three random continuations. This complements the mixed-pool comparison but has a small test set and is not matched to the mixed evaluation population. No weight tuning or significance claim.

## Verification and outputs

Save split IDs, class memberships, starting pairs, seeds, prediction rows, selected IDs, aggregate metrics, input hashes, software versions, and script. Independently recompute all MAEs and class membership; verify audit exclusion, no training/test leakage, valid features, same starts and random seeds, and default acquisition score against original function. Report all findings, including adverse results, and qualify differences in candidate pools and class test sizes. Record code/analysis changes and reviewer response; update cumulative R1.4 manuscript and SI DOCX with highlighted scope restriction and accurate findings, then render and visually inspect. Do not change production code, archive, or original percentages.

## Status

Interpretation confirmed by the user; plan recorded before running the proposed outcome comparisons. Basic ledger and source availability were inspected to design the test.

## Source-condition finding before outcome comparisons

The original paper, Tables 1 and 4, reports aryl scope at −10 °C with Boc2O and sulfonyl scope at 40 °C, with a 25 °C exception noted in Table 4. The current curated ledger assigns the same −10 °C condition to all 50 records. Therefore the ledger condition field is inaccurate for the sulfonyl scope and cannot be used to claim a single reaction protocol. The predictive matrix and acquisition code do not encode reaction conditions: mixed-pool results are conditional on pooled class/protocol differences, and cannot disentangle temperature, additive, structural class or other source differences. Correct this explicitly in manuscript and SI, preserve the ledger unchanged, and identify record-level exception status from the original figure before making per-substrate claims.

## Completion record

The source audit, planned 20-split mixed and sulfonyl-only analyses and independent checks were completed. See `results_and_adjustments.md`, the response draft and `validation_report.txt`. The source-order mixed baseline is class-imbalanced because it selects no sulfonyl record at the assessed budgets. The original release ledger remains unchanged and needs correction before submission.
