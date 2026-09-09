# Data Availability Statement

All data needed to inspect the retrospective computational analyses are
provided in the companion `SI.zip` archive submitted with the manuscript.
The organized entry point inside that archive is [`README.md`](README.md).
The working repository's `SI/` directory is the source tree used to build the
archive; its large artifacts are linked during development and are resolved to
file contents in `SI.zip`.

Curated P7 and CMC-Por reaction records, structures, experimental ee/yield
values, conditions, source locations, family assignments, exclusions, model
predictions, split membership, feature matrices, transfer/route results,
geometry files, CREST/xTB outputs, generator streams, funnel records, and
proposal-panel locks are listed in the README and linked subdirectories.
Analysis scripts, feature-generation source, replay commands, dependency
declarations, and file manifests are included under `SI/code/` and
`SI/procedure/`.

The generated candidate panel is prediction-only. No experimental outcome,
supplier availability, route-feasibility, safety, or laboratory-success value
is included for generated candidates or the five P7 prediction-only
substrates. The 127 eligible enumeration candidates whose EE rows were not
written are explicitly documented in `SI/candidate-generation/` and the
README; they are not treated as chemical failures.

The distribution route for this study is the accompanying `SI.zip` archive;
no separate public repository DOI is claimed. The archive contains resolved
file contents rather than symlinks and preserves the directory map described
in the final Supporting Information Section S9. The package records runtime
versions and dependency declarations, but does not claim a complete lockfile
or bitwise-identical environment reconstruction.
