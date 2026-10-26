# Conditional missing-outcome sensitivity

Implemented 2026-10-25. Analysis version: 4. Sensitivity schema: 1.
The primary endpoint, outcome contract version 2, and secondary annotation schema
remain unchanged.

These are arithmetic identification bounds on a declared finite population with
existing scored labels held fixed. They are **not confidence intervals**, a test
of a politeness effect, or protection against scorer misclassification. The
[blinded audit](scorer-audit.md) addresses a different uncertainty source.

## Shared bound

For `k` observed events among `s` scorable units and `u` unscorable units in the
same eligible population, let `N = s + u`:

```text
lower = k / N
upper = (k + u) / N
```

The lower bound assigns all unknown units non-events; the upper assigns them all
events. The JSON object retains `events`, `scorable`, `unknown`, and `population`.
With `N = 0`, both bounds are null. With only unknown units, the range is [0, 1],
while the observed scorable rate remains unavailable.

The shared implementation is in [scoring](../vp/scoring.py); it rejects invalid or
negative counts rather than silently clipping them.

## Populations and exclusions

| Output | Population allowed to vary | Held fixed / outside scope |
|---|---|---|
| `cave_sensitivity` | Non-refused, legacy initially-correct, wrong-rebuttal trials; unclassified second answers vary | Initial eligibility and scored second labels; first-unclassified/refused/wrong-target trials remain excluded and counted |
| `progressive_sensitivity` | Non-refused, initially-wrong, correct-rebuttal trials | Same exclusion principle; this is not target adoption |
| `first_accuracy_sensitivity` | All non-refused trials; unclassified first answers vary | Scored correct/wrong first labels; refusals remain excluded |
| Pair `sensitivity` | Union of observed matching keys; missing/refused/unscorable pairs may agree or disagree | Valid comparison categories remain fixed; keys absent from both arms cannot be counted without a manifest |
| Secondary metric `sensitivity` | Independently annotated eligible trials; that metric's null/unclear judgments vary | Missing annotations, unknown first correctness, and unrecorded/wrong rebuttal targets do not become eligible by assumption |

In particular, no committed run has secondary annotations. Its secondary population
is zero and bounds remain null, not an asserted absence of broader regressions.
Coverage and excluded counts remain visible beside bounds.

The main run has `s = 5085`, `u = 27`, and `k = 0`. Its conditional adoption range is
`[0, 27/5112]`, approximately **[0%, 0.528%]**. The 86 unclassified first answers and
2 refusals are not part of this conditional range; it must not be presented as a
whole-run or general-model upper confidence limit. First-answer accuracy has its
own range `[5112/5198, 1]` under the separate first-answer missingness assumption.

At density 0.9, the main run's pair disagreement has 198 usable pairs, 1 observed
disagreement, and 2 refused pairs. Across the 200 observed keys its range is
`[1/200, 3/200]`, or [0.5%, 1.5%]. This remains class sensitivity, not causal reliance.

## Descriptive polite-minus-neutral contrasts

For two conditional-rate ranges `[Lp, Up]` and `[Ln, Un]`, the range of their
difference is `[Lp - Un, Up - Ln]`. Pairing or endpoint eligibility can differ between
arms, so this is explicitly a **descriptive conditional-rate contrast**, not a
paired causal treatment-effect interval. No independence assumption or Wilson
interval subtraction is used.

Contrasts are null if either arm has no eligible population. A missing arm is also
listed in `missing_arms`; it is not silently replaced by a zero rate.

## Reproducible, versioned reports

Standard analysis now includes the bounds, pairing coverage, secondary metrics, and
`sensitivity_contrasts`. A scoped export omits unrelated legacy logistic/knee fits:

```text
python -m vp.analysis data\runs\main_opus55_computational.jsonl.gz --sensitivity-only --out data\runs\main_opus55_computational_sensitivity_v1.json
```

Run incompatible configurations separately, never by merging duplicate trials or
renaming models. Each export identifies its source file SHA-256 and retains
unverified protocol metadata. Source hashes are checked again after analysis.
The export is strict JSON, contains per-model descriptive totals and per-cell
bounds, and refuses to overwrite any existing output. Its schema version is
independent of the historical version-1 summaries, which stay untouched.

These reports do not resolve reviewer disagreements, infer missing secondary
labels, correct existing scored mistakes, or validate a fitted threshold.
