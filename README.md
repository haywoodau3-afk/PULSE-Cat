# PULSE-Cat

Computational records for the retrospective study of catalyst-contextual molecular representations and information-guided substrate ordering in two iron-porphyrin C(sp3)–H amination datasets.

## Navigate the repository

| Location | Contents |
| --- | --- |
| `curated-datasets/` | Source-corrected reaction ledgers, substrate structures, and cohort membership. Start with its README. |
| `scripts/` | Workspace analysis and feature-generation code retained in its original layout. |
| `revision/` | Scripts and selected inputs for the reviewer-response analyses. |
| `records/corrected_project/analysis_runs/` | Saved results, splits and predictions for the corrected revision. See [analysis map](docs/ANALYSIS_MAP.md). |
| `records/` | Corrected and historical intermediate records and code snapshots. |
| `data/` | Recorded inputs in workspace-relative locations required by some scripts. These include historical records; consult the warning below. |
| `environment/` | Recorded package versions and original environment notes. |

## Data and reproducibility

The authoritative source-corrected ee outcomes are in `curated-datasets/p7-records.jsonl` and `curated-datasets/cmcpor-records.jsonl`. Historical input files retain erroneous numerical zero ee entries for P7-study records 1z and 1ad. These are not measured zeros. See `HISTORICAL_INPUT_WARNING.txt` and `curated-datasets/dataset-id-lists.csv`.

Read [reproducibility status](REPRODUCIBILITY_STATUS.md) before running code. The archive contains scripts, inputs, and saved outputs, but complete regeneration in a clean environment has not been established; some scripts depend on original workspace paths and can overwrite outputs. The model-selection provenance limitation is also described there.

Run `python3 verify_saved_results.py` to check two reported common-test summaries from saved split results. This is an aggregation check, not a model rerun. `RELEASE_SHA256SUMS.txt` provides a checksum inventory of this structured copy; earlier inventories are retained as historical records.

## Before public release

See [publication checklist](docs/PUBLICATION_CHECKLIST.md). Local paths, third-party rights, licenses and clean-environment reproducibility remain to be reviewed. No DOI has been created.
