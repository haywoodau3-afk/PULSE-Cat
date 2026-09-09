# Five-pose benchmark results

## Outcome

The computational budget is acceptable for direct GFN2-xTB single points, but
the current assemblies do **not** support defensible pose probabilities. The
100-pose/full-panel calculation is therefore not promoted yet, and no new
MAE/R2 claim is made.

Five diverse `1a` poses were selected at ranks 1, 12, 100, 102, and 170,
covering three low-UFF and two valid high-UFF representatives.

| Arm | Successful poses | Mean successful time/pose | Estimated 100-pose serial time | Estimated 38x100 serial time | Scientific result |
| --- | ---: | ---: | ---: | ---: | --- |
| Frozen-core GFN-FF cleanup + GFN2 SP | 3/5 | 11.13 s | 18.6 min | 11.75 h | Reject: 40% end-to-end failure; successful energy span 36,926 kcal/mol |
| Direct GFN2 SP, neutral closed shell | 5/5 | 2.18 s | 3.63 min | 2.30 h | Reject as population energy: 1,155.1 kcal/mol span; `N_eff=1.0` |
| Direct GFN2 SP, neutral doublet | 5/5 | 2.17 s | 3.62 min | 2.30 h | Same collapse; retain only as electronic-descriptor arm |
| Frozen-core GFN2 optimization, neutral doublet | 0 completed at stop | >5 min four-worker wall time | Not extrapolated | Not extrapolated | Reject current settings: 2 SCF failures and 3 unfinished when stopped |

The direct-doublet child-process high-water memory was approximately 160.5 MB.
An idealized four-worker direct-SP projection is about 0.57 h for the full
38-substrate panel and roughly 0.65 GB aggregate memory, but I/O and CPU
contention make that a lower-bound wall-time estimate.

## Representation demonstration

The direct-doublet run successfully generated a full label-blind feature row
for all 11 candidate C-H sites. The soft site-competition calculation assigned
the largest normalized reaction-ready mass to `1a-c11-benzylic` (0.615), but
this is a plumbing observation, not a validated site prediction. The maximum
pose weight was 1.0 and entropy-effective pose count was 1.0, so every weighted
standard deviation was effectively zero. This diagnostic correctly rejects
the proposed probability block rather than passing a numerically well-formed
but physically meaningless vector into the model.

## Baseline and gate

The unchanged publication baseline is ee MAE 9.627 and pooled R2 0.314 on 38
fixed-P7 modelable records. Promotion requires MAE <=7.627, increased R2, no
material RMSE degradation, and paired-bootstrap support under the same nested
family-held-out evaluation. Because the five-pose ensemble failed its physical
validity gate, model fitting would not answer whether probability weighting
improves those metrics; it would only measure an artifact of one collapsed
pose.

## Reproducible artifacts

- `results/five-pose-benchmark/benchmark.json`: GFN-FF cleanup arm.
- `results/five-pose-direct-gfn2-control/benchmark.json`: closed-shell direct
  single-point control.
- `results/five-pose-direct-gfn2-doublet/benchmark.json`: doublet direct
  single-point timing, energies, uncertainty weights, and resource estimates.
- `results/five-pose-direct-gfn2-doublet/representation-demo.json`: compact
  label-blind feature demonstration.
- `results/five-pose-gfn2-optimized-doublet/`: logs from the stopped
  optimization-control attempt.

## Conclusion

The novel representation remains promising as a compact combination of
reaction-frame sterics, xTB electronics, uncertainty, and site competition.
The new result is that raw full-assembly total energies are unsuitable for its
probability component on the currently retained poses. The next experiment
must repair conformer energetics and electronic-state convergence first; only
then is a 100-pose seed-set MAE/R2 benchmark scientifically justified.

# Substrate-only CREST/GFN2-xTB production and P7 ablation

## Processing outcome

The run stopped at the selected decision boundary after every job active at
that time completed. Complete results comprise 56 substrates: all 40 P7 and 16
CMC-Por. CREST generated and CREGEN retained exactly one unique minimum for
every completed substrate, for 56 retained conformers total. All 56 GFN2-xTB
reranks succeeded; there were no failed or timed-out completed records. Four
later CMC-Por directories (`2o`, `2p`, `2q`, `2r`) are partial and excluded.

Aggregate CREST worker time was 19,164.5 seconds (5.32 worker-hours). Per
substrate wall time had mean 342.2 seconds, median 334.8 seconds, minimum 122.8
seconds, and maximum 986.4 seconds. Each completed result has an XYZ hash, raw
stdout/stderr, rerank energy, command provenance, reaction temperature,
Boltzmann probabilities, and effective conformer count. Since every ensemble
contains one state, every Boltzmann probability and effective count equals 1.

## P7 nested family-held-out result

The direct comparison uses the same 38 modelable P7 records and nested
leave-one-family-out Elastic Net protocol for every arm.

| Feature arm | Features | MAE | R2 | RMSE | MAE change vs matched baseline |
| --- | ---: | ---: | ---: | ---: | ---: |
| Matched Stage-2p geometry baseline | 248 | 8.498 | 0.476 | 11.357 | 0.000 |
| Baseline + CREST geometry | 258 | 8.858 | 0.455 | 11.578 | +0.360 worse |
| Baseline + dense GFN2-xTB electronics | 261 | 8.610 | 0.440 | 11.745 | +0.112 worse |
| Baseline + CREST geometry + GFN2-xTB | 271 | 8.876 | 0.429 | 11.860 | +0.377 worse |

For the combined arm, a paired 20,000-draw substrate bootstrap estimates an
MAE improvement of -0.377 ee points (negative means worse), with 95% interval
[-1.000, 0.212] and probability 0.107 that the augmentation improves MAE. The
electronic-only interval is [-0.691, 0.423], also crossing zero while its point
estimate is worse. CREST geometry alone is directionally harmful with interval
[-0.733, -0.009].

## Decision

Substrate-only CREST/GFN2-xTB is **not an additive predictive feature block**
for P7 under the locked evaluation. It fails every promotion requirement: MAE
does not fall, R2 falls, RMSE rises, and the probability block is constant.
Computing the remaining 34 CMC-Por substrates is therefore not recommended for
this representation.

This does not reject pose-aware quantum features generally. It shows that a
free-substrate minimum cannot substitute for a probability distribution over
substrate compatibility with the catalyst pocket. A distinct next test would
keep P7 frozen, place a small diverse set of substrate poses in its reaction
frame, compute steric/electrostatic/dispersion and reaction-ready scores for
those assemblies, and normalize compatibility weights separately from the
free-substrate conformer prior.

## Reproducible artifacts

- `crest-10-conformers/`: completed conformers, metadata, and live logs.
- `p7_crest_xtb_benchmark.py`: feature extraction and locked model ablation.
- `p7-crest-xtb-model/features.json`: full auditable CREST/xTB feature values.
- `p7-crest-xtb-model/metrics.json`: metrics, folds, and paired bootstrap.
- `p7-crest-xtb-model/predictions.csv`: all held-out predictions.
