# Atom-index error: plain-language explanation

## What the error was

The analysis used molecular atom number 0 as if it always meant “the nitrene nitrogen.” Atom numbers are positions in a particular SMILES or molecule object, not chemical identities. A valid SMILES can begin with a carbon and place the nitrene nitrogen later. The pose-assembly step also reorders atoms. In the affected path, the code could therefore read coordinates for the wrong atom as the nitrene position. Related geometry calculations could also choose the wrong hydrogen as the transferable hydrogen.

For substrate 1ah, recalculating the saved 200 pose coordinates with the chemically identified nitrene nitrogen changes the mean nitrene-N-to-reactive-C distance from 2.5386 Å in the archived feature output to 3.5815 Å. This is a concrete, measurable error, not just a possible coding concern.

## What did not change

The published reaction outcomes (ee and yield), molecular structures, and saved 3D pose coordinates were not changed. The error was in identifying atoms when converting those inputs into geometry descriptors. Predictions, model comparisons, acquisition scores, and other outputs that use the affected descriptors therefore had to be recalculated.

## Why it matters to the paper

The consequences are substantial for the numerical evidence, but they do not eliminate the underlying research question. The corrected Fe(P7)Cl structure-plus-pose model still has lower pooled MAE than structure-only in the two matched retrospective validations: 7.979 versus 12.612 ee points for target holdout, and 8.538 versus 10.406 for family holdout. Corrected acquisition analyses also favour uncertainty–diversity over source order in several tested comparisons. However, the size of reported effects changed; endpoint and substrate-class results remain conditional; the full-pose/acquisition combination does not beat the simpler structure/source cells; and the corrected Stage 1-v2/Stage 2-v2/Stage 3a seed pilot no longer supports its earlier slight shell-model advantage.

So the defensible central claim is narrower: catalyst-contextual features and information-guided ordering are promising, data-dependent retrospective tools in these small published datasets. The current evidence does not establish a generally superior or prospectively validated workflow.

## Why the correction must be disclosed

Keeping the original numbers while knowing that a feature-generation error changed their inputs would leave unsupported results in the paper and data package. It could materially undermine editorial confidence if discovered during review or after publication. The right response is to disclose the issue, report corrected results, withdraw any analysis that cannot be verified, and limit claims to what survives the correction.

See [ERROR_IMPACT_ANALYSIS.md](ERROR_IMPACT_ANALYSIS.md), [SOURCE_TREE_AUDIT.md](SOURCE_TREE_AUDIT.md), the feature and pose-level change summaries, and the corrected analysis files under `corrected_project/` for the detailed audit trail.
