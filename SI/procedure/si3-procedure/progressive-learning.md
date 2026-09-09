# Progressive-learning procedure

1. Select the two-substrate central-plus-diverse seed from the locked domain.
2. Mask all future target labels.
3. Fit the declared estimator at the current prefix using only revealed labels.
4. Predict every unrevealed substrate and record uncertainty, novelty,
   family coverage, and expected information value.
5. Reveal one complete substrate according to the fixed route.
6. Append the observed ee and yield to their separate histories.
7. Repeat until the domain is exhausted.
8. Repeat the random policy for 500 independent routes and report mean and
   interquartile curves rather than a best seed.

The primary acquisition score is the frozen uncertainty-plus-diversity policy:

```text
0.4 * uncertainty + 0.4 * diversity + 0.2 * family coverage
```

Historical order and performance-first routes are controls. All fixed-prefix
arms share the same route and split definitions so their curves are paired.
