# Curated substrate datasets

The two JSONL files are the authoritative substrate/reaction records. The
tables in this directory are supporting inputs and validation artifacts.

| File | Contents |
| --- | --- |
| [`p7-records.jsonl`](p7-records.jsonl) | 41 P7 records with structures, outcomes, sites, conditions, and provenance |
| [`cmcpor-records.jsonl`](cmcpor-records.jsonl) | 50 CMC-Por records, including 33 aryl and 17 sulfonyl-control records |
| [`cmcpor-run-records.jsonl`](cmcpor-run-records.jsonl) | CMC-Por records with the fixed published condition set |
| [`dataset-id-lists.csv`](dataset-id-lists.csv) | Explicit membership for every population used in the analyses |
| [`substrate-smiles.csv`](substrate-smiles.csv) | Consolidated substrate/product SMILES, outcomes, sites, source locations, and overlap annotations |
| [`p7-source-ledger.csv`](p7-source-ledger.csv) | P7 paper/SI page and table provenance |
| [`p7-manual-substrates.csv`](p7-manual-substrates.csv) | P7 manually curated substrate/site table |
| [`cmcpor-manual-substrates.csv`](cmcpor-manual-substrates.csv) | CMC-Por manually curated substrate/site table |
| [`p7-optimization-conditions.csv`](p7-optimization-conditions.csv) | P7 condition-variation records; not substrate negatives |
| [`source-structures.jsonl`](source-structures.jsonl) | CMC-Por source structures and remapping provenance |
| [`derived-nitrene-sites.csv`](derived-nitrene-sites.csv) | Derived nitrene/reaction-centre site records |
| [`remap-validation.csv`](remap-validation.csv) | Structure and atom-map validation results |
| [`reaction-record.schema.json`](reaction-record.schema.json) | Machine-readable record schema |

Missing product mappings remain null. A missing ee is not zero, and an
unreported reaction is not a failure.
