# Reproducibility status

This release gathers the existing records and workspace code; a complete clean-environment rerun has not been established. The original work used Python 3.14.6, NumPy 2.5.1, SciPy 1.18.0, scikit-learn 1.9.0, RDKit 2026.03.4 and LightGBM 4.7.0. The requirements files and environment notes are recorded under `environment/`; they are historical specifications, not a complete tested lockfile.

The former archive omitted `scripts/scope_progression.py` and `data/jacs_2025/stage2/features/pose-summary.jsonl`; both are now included together with revision scripts and recorded inputs. Original workspace paths and historical inputs have been retained for provenance. In particular the historical P7 input snapshot and original workspace ledger contain invalid zero-ee entries for 1z and 1ad; do not treat these as measured outcomes. The source-corrected authoritative ledger is `curated-datasets/p7-records.jsonl`; the 38-substrate ee cohort excludes those records and 1an.

Many scripts assume the original project root, make fixed relative-path references, or write output into the workspace. Do not run them over the archive without first reviewing the paths and output destinations. The `records/corrected_project/analysis_runs/` directories provide saved split-level data and outputs for the corrected revision. `python3 verify_saved_results.py` checks selected published summaries using saved records; it does not re-run the models or establish independent reproducibility.

The original screening check did not independently verify every feature and hyperparameter selection decision against held-out outcomes. No prospective validation or bitwise reproduction of all historical runs has been established. Inspect rights to redistribute third-party data and code and review local absolute paths before publication.

## Checks performed during assembly

Using the original local Python environment, the common-test loader imported the included progression module and loaded 38 Fe(P7)Cl and 26 Fe(CMC-Por)Cl active records using the corrected Stage 2p feature files. This establishes that these inputs can be loaded in that environment; no clean-environment end-to-end replay was performed. The recorded-version list includes a NumPy version captured from that local environment, but is not a fully resolved or independently installed lockfile.
