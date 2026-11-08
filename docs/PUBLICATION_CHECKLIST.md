# Before public release

- Review and remove or appropriately replace local absolute paths where necessary. Preserve a private provenance copy, verify script dependencies, and regenerate affected inventories after any edits.
- Confirm rights for third-party source data and code. Assign licenses only where authorized; no blanket license has been selected.
- Perform a fresh-environment reproduction audit. The included version list is not a complete verified lockfile, and the complete analyses have not been rerun.
- Resolve or transparently retain the documented uncertainty concerning feature and hyperparameter selection.
- Review all files intended for publication, including historical and intermediate records. The archive includes source-corrected and historical datasets; historical zero-ee labels are not measured observations.
- Several files are larger than 50 MiB, although none exceeded 100 MiB when this copy was assembled. GitHub browser upload has a lower per-file limit; use a suitable Git client.
- After a public GitHub release is prepared, consider archiving a tagged release in Zenodo and check its contents, metadata and DOI. Update the manuscript's data availability statement with the actual verified DOI or link. No deposit has been made.
