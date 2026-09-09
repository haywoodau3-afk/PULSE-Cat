# Probabilistic steric-electronic pose representation

This dated folder is an isolated development area for testing whether the
stored catalyst-substrate XYZ poses can contribute more predictive information
without changing the established Stage 2 or Stage 3 artifacts.

The agreed first gate is a five-pose timing benchmark on substrate `1a`.
`pose_probability.py` selects diverse representatives from both retained UFF
strata and can test direct GFN2-xTB single points, frozen-core GFN-FF cleanup,
or frozen-core GFN2-xTB optimization with ALPB ether. It also implements the
proposed uncertainty-aware weighting and label-blind candidate-site feature
scaffold. The five-pose result tests plumbing and resource cost only; it cannot
test model accuracy or conformer convergence.

The production-scale repair sampled the substrate independently of the
porphyrin: CREST explores the neutral closed-shell aryl-azide precursor, while
the P7 or CMC-Por geometry is excluded from conformer sampling and will remain
fixed during the subsequent pose-compatibility calculation. This avoids paying
for porphyrin motion and prevents catalyst flexibility from contaminating the
substrate conformer probabilities. The requested inventory covered all 40 P7
and 50 CMC-Por substrates. At the agreed decision boundary, processing stopped
after all 40 P7 and 16 completed CMC-Por substrates; remaining CMC-Por work is
deferred. The workflow retains up to 10 genuinely unique minima per substrate
and never pads a rigid molecule with duplicate conformers.

Each retained conformer is independently reranked with GFN2-xTB/ALPB ether and
assigned a Boltzmann probability at its reaction's recorded temperature. The
next stage will anchor those conformers to the corresponding frozen porphyrin
and combine free-substrate plausibility with pocket compatibility. Production
features will combine:

- steric reaction-frame fields and catalyst-pocket occupancy;
- xTB charges, bond orders, frontier-orbital gap, and interaction proxies;
- label-blind geometry scores for every plausible C-H HAA site;
- uncertainty-aware Boltzmann means, variances, quantiles, population entropy,
  effective pose count, and productive-geometry probability;
- probability mass and free-energy gaps for the leading candidate site versus
  its competitors.

The locked model gate is at least a 2.0 ee-point reduction from the current
publication benchmark MAE of 9.627, increased pooled R2 from 0.314, no material
RMSE degradation, and paired substrate-bootstrap support under the same nested
family-held-out evaluation. Yield is a secondary no-harm endpoint.

## Commands

```bash
.venv/bin/python docs/research/2026-09-07/test_pose_probability.py
.venv/bin/python docs/research/2026-09-07/pose_probability.py --skip-cleanup \
  --uhf 1 --output docs/research/2026-09-07/results/five-pose-direct-gfn2-doublet

.venv/bin/python docs/research/2026-09-07/generate_crest_ensembles.py \
  --domain all --workers 4 --threads 1 --retain-count 10 \
  --output docs/research/2026-09-07/crest-10-conformers
```

The CREST command emits JSON events to the terminal and appends the same events
to `crest-10-conformers/progress.jsonl`; a concise human-readable mirror is in
`crest-10-conformers/run.log`. Each substrate directory retains CREST stdout,
stderr, final XYZ structures, GFN2 reranking/population data, and provenance
metadata. Re-running the command skips completed and scientifically underfilled
substrates, so interrupted runs resume safely.

`p7_crest_xtb_benchmark.py` performs the decision-stage P7 ablation. It
extracts rotation-invariant CREST geometry descriptors and a compact dense
GFN2-xTB electronic block, then compares them with the exact matched Stage-2p
baseline under nested leave-one-family-out validation. The result is negative:
neither feature block improves MAE or R2. See `results.md` and
`p7-crest-xtb-model/metrics.json` for the numerical comparison.

See `results.md` for measured timings and scientific conclusions after the
benchmark completes, `development-log.md` for decisions and implementation
history, and `pose-ensemble-steric-electronic-representations.md` for the
primary-source literature basis.
