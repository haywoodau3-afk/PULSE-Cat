# Candidate-generation and proposal records

The `pptl/` link exposes the complete frozen candidate-generation branch.

Important counts:

| Population | Raw | Unique canonical | Contract-valid | Contract-valid and in-domain |
| --- | ---: | ---: | ---: | ---: |
| SMILES-RNN/PromptSMILES generator | 50,560 | 9,184 | 563 | 483 |
| Deterministic enumeration comparator | 50,560 | 25,955 | 18,545 | 18,350 |

The applicability-domain threshold is `max_morgan_tanimoto <= 0.35` to the
91-reference set. The 500-candidate sample is a diagnostic screening pool per
provenance, not the 483-row final generated pool.

The current `funnel-enumeration-ee.csv` is truncated at `enum-049999`. The
exact 127 eligible omitted rows are materialized in
[`omitted-127-eligible-enumeration-candidates.csv`](omitted-127-eligible-enumeration-candidates.csv).
They are the rows satisfying:

```text
candidate_id in enum-050000 ... enum-050559
contract_valid == true
ad_status == in_domain
```

Their exact structures and AD values are also in `pptl/funnel-enumeration-ad.csv`.
They are unscored, not rejected. Rebuild the missing EE rows with the frozen
model before reporting a complete scored enumeration pool.

The sealed computational proposal set is `pptl/sealed-prospective-panel.csv`
and its lock is `pptl/sealed-prospective-panel-lock.json`. The separate
development set is `development-shortlist-16.csv`/`.jsonl`, with safety-screen
records retained as review evidence rather than experimental validation.
