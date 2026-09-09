# Software and runtime records

These are the versions recorded by the local analysis and generator
manifests. They are not a substitute for a lockfile; the missing lockfile is
listed in [`../README.md`](../README.md) as a release action.

| Component | Recorded version or pin | Evidence |
| --- | --- | --- |
| Analysis Python | 3.14.6 | `SI2/SUPPORTING_INFORMATION_FEATURE_METHODS.md` |
| RDKit analysis | 2026.3.4 | [`requirements.txt`](requirements.txt) |
| NumPy | unpinned in current requirements | [`requirements.txt`](requirements.txt) |
| SciPy | 1.18.0 | [`requirements.txt`](requirements.txt) |
| scikit-learn | 1.9.0 | [`requirements.txt`](requirements.txt) |
| LightGBM | 4.7.0 | [`requirements.txt`](requirements.txt) |
| Generator Python | 3.11.16 | [`generator-freeze-config.json`](../algorithms/generator-freeze-config.json) |
| Generator PyTorch | 2.13.0 | [`generator-freeze-config.json`](../algorithms/generator-freeze-config.json) |
| Generator RDKit | 2026.3.5 | [`generator-freeze-config.json`](../algorithms/generator-freeze-config.json) |
| SMILES-RNN | commit `c8ee705961b4411707c69f73d309c1cf61208b95` | [`generator-freeze-config.json`](../algorithms/generator-freeze-config.json) |
| SMILES-RNN checkpoint | `ChEMBL28pur.ckpt`; SHA-256 `bf0882cc1f35743c6226001129a1031e79ad25f357f903d02f953ed0e5d0d289` | [`generator-freeze-config.json`](../algorithms/generator-freeze-config.json) |
| PromptSMILES | 1.7.2 | [`generator-freeze-config.json`](../algorithms/generator-freeze-config.json) |
| CREST | 3.0.2 | SI2 feature methods |
| xTB | 6.7.1 | SI2 feature methods |
