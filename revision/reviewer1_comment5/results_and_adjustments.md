# Reviewer 1, comment 5: findings and adjustments

## Source audit

Wang et al., Angew. Chem. Int. Ed. 2023, 62, e202218577, Tables 1 and 4, report two distinct substrate scopes. The aryl protocol uses −10 °C and Boc2O; the sulfonyl scope uses 40 °C and its table does not list Boc2O. An additional 25 °C result is reported for 6a; its 81% ee used here is the 40 °C result. The 26 active aryl and 17 sulfonyl ee values were checked against the source tables. The 50-record ledger has 33 aryl and 17 sulfonyl records (34% sulfonyl); seven aryl records remain locked outside all analyses. The original aryl-only acquisition analysis therefore supports an aryl-specific conclusion; we cannot infer a documented historical reason beyond its defined analysis scope.

The original curated ledger incorrectly gives −10 °C for the sulfonyl records. The source reports the yield of 6q as <5%, while the original ledger records 5 as an exact value. A revision-local corrected copy, `results/cmcpor_source_corrected_copy.jsonl`, preserves the source's upper-bound qualifier and records 40 °C for this scope. **The original release ledger remains uncorrected and should be updated before submission or public release.** No yield analysis is performed here; the ee feature matrix does not encode temperature or Boc2O, so correcting those metadata does not change these ee calculations. Class and conditions are confounded. Reactive-site geometry includes repaired assignments; see `source_audit_report.txt` for coverage and provenance. The source comparison verifies outcomes and reported conditions, not independent experimental measurements or every geometry.

## Prespecified comparisons

Twenty deterministic, overlapping stratified splits each hold out 3 aryl and 2 sulfonyl substrates. Three shared aryl starting pairs per split and budgets 2, 6, 10, 15 and 20 were used. Random is averaged over three continuations per start. The Ridge feature set and frozen acquisition weights follow the existing protocol. Split averages weight budgets and starts equally. MAEs below are ee percentage points. The mixed candidate pool comprises the remaining aryl and sulfonyl records; the aryl-only pool excludes all sulfonyl records, while both are evaluated against the same held-out substrates.

| Held-out group | Mixed source order | Mixed uncertainty–diversity | Mixed random | Aryl-only uncertainty–diversity |
|---|---:|---:|---:|---:|
| All five | 17.14 | 15.41 | 16.71 | 16.15 |
| Aryl (3) | 14.80 | 14.36 | 16.19 | 14.22 |
| Sulfonyl (2) | 20.64 | 16.97 | 17.49 | 19.03 |

Mixed versus aryl-only uncertainty–diversity favoured the mixed pool on sulfonyl error in 12/20 splits and aryl error in 8/20. The mixed source route selects no sulfonyl labels up to budget 20 because all aryl records precede sulfonyl in the ledger; uncertainty–diversity selects on average 6.95 sulfonyl labels at budget 20. Thus the source route does not represent a balanced mixed-class baseline. Pool, training composition and acquisition path change together; these are not isolated causal effects of substrate class.

A separate sulfonyl-only replay (20 overlapping splits, three sulfonyl test records, three starts, budgets 2/6/10/13) gives source-order, uncertainty–diversity and random MAEs of 17.51, 18.61 and 18.71, respectively. Uncertainty–diversity beats source order in 6/20 splits and random in 10/20. This is a different evaluation population and budget schedule from the mixed analysis and does not establish a universal ordering. No statistical significance is claimed.

`pool_comparison.py` and `results/{mixed,sulfonyl}/` preserve inputs, seeds, selection paths, predictions, split summaries and software metadata; `validate_pools.py` and `validation_report.txt` document independent recomputation and checks. These retrospective outcomes are limited to reported scope records and do not address unpublished failures or prospectively chosen substrates.

## Writing and system adjustments

- Identify the original Fe(CMC-Por)Cl acquisition cohort as aryl-only, correct the description of sulfonyl records as a substrate scope, and state the two reported protocols.
- Add the common-test expanded-pool results and sulfonyl-only counterexample, including the source-order class imbalance and class–condition confounding.
- Add full methods, numerical summaries and metadata caveats in the SI; highlight newly revised material in both documents.
- Retain the original analysis, production code, original 33.2% result and archived ledger unchanged; the separate corrected metadata copy and reproducible analysis are revision artifacts. Before submission the author must reconcile and update the actual distributed dataset and deposit the new analysis outputs, then check the manuscript's data availability statement against that release.
