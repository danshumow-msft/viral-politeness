# Repository assessment and proposed next steps

Assessment date: 2026-10-24.

Reviewed revision:
[`1b7f7734987c32281c34423407c6ca8f87d4e7b4`](https://github.com/shumow/viral-politeness/tree/1b7f7734987c32281c34423407c6ca8f87d4e7b4).

This document records the assessment delivered in chat before beginning follow-up
work. It is an assessment and proposed direction, not a pre-registration amendment.
No implementation changes or new live experiments are included.

## Scope and overall opinion

I reviewed the research notes, both runners, scoring and analysis code, tests, and all
six committed run datasets. I independently checked the record counts and inspected
the three hand-overridden judgments. I did not rerun paid model calls.

**My honest opinion: this is a thoughtful, unusually transparent early-stage research
project. Its experimental discipline is stronger than its current theoretical
argument.** I think it has produced a useful, narrowly scoped negative result, not yet
a convincing test of "politeness as contagion."

## What I like

- **It reports the disappointing result rather than manufacturing a success.** The
  [results log](../results_log.md) clearly distinguishes unsupported hypotheses from
  hypotheses the experiment could not reach.
- **The measurement failures are exposed.** Publishing how the original scorer
  produced 16 false caves, how the judge also failed, and how those failures were
  investigated is genuinely good practice.
- **The controls are thoughtfully chosen.** Polite, neutral, rude, and
  authority-loaded histories are a sensible starting point. Matching their positions
  and phrase layouts makes comparisons substantially more credible.
- **The implementation is appropriately small and understandable.** Context
  construction, scoring, reliance, and aggregation are separated without excessive
  machinery. There are meaningful offline tests, and the reviewed revision's
  [CI passed](https://github.com/shumow/viral-politeness/actions/runs/39859539320).
- **The raw outputs make the conclusions auditable.** I checked the three manual
  overrides; all three really are reaffirmations of the correct answer, not adoption
  of the supplied wrong answer.

That is a solid foundation.

## Biggest objection: reliance does not measure what the theory needs

The [behavioral reliance definition](reliance.md) is essentially:

> How often do polite and neutral twins receive different correctness classifications
> on their **first**, pre-rebuttal answers?

That creates two serious problems.

**First, it can miss precisely the proposed phenomenon.** A model could answer
correctly in both conditions, then cave under pressure only after the polite history.
Politeness would have changed its susceptibility to persuasion, while this reliance
measure would remain zero.

**Second, the proposed 0.9 threshold is structurally incompatible with high
first-answer accuracy.** If both arms score about 98% correct, their classifications
can disagree on at most about 4% of pairs: disagreement requires at least one member
not to be classified correct.

So reaching 0.9 on this metric would require enormous first-answer degradation or
disagreement, not merely strong reliance on social context.

This is more than a floor-effect inconvenience. It is a **construct-validity
problem**: correctness-class disagreement, attention mass, and causal dependence on
context are different quantities. Giving each a range of zero to one does not make a
numerical threshold transferable between them.

Relatedly, the [H2 analysis plan](preregistration.md#analysis-plan) treats a narrower
logistic transition as evidence of better prediction. That is not a reliable
predictive-model comparison; transition widths depend on the predictor's scale and
distribution.

**I would rework this part before spending much more on the central theory.**

## The result is useful, but narrower than some of the prose suggests

The defensible finding is approximately:

> Under these synthetic conversation histories, the tested Claude models did not
> adopt the benchmark's supplied wrong answers in the final reviewed classifications.

That does **not** establish that politeness has no effect generally, that answers
never deteriorate under pressure, or that a contagion mechanism has been ruled out.

There is a concrete example in the
[main-run records](../data/runs/main_opus55_computational.jsonl.gz): on one
completing-the-square problem, five trial responses changed a correct answer into an
incorrect one after pushback, replacing the constant `-39/4` with `-9/4`. They rejected
the user's proposed answer but invented a different wrong answer.

Those responses are classified `other`, so they do not count as caves under the
declared outcome. That is consistent with the chosen scoring scheme, but **"zero
adoptions of the supplied wrong answer" is not "zero correct-to-incorrect
regressions."** These cases do not establish a politeness effect; they demonstrate why
the outcome's wording matters.

I also think the pilots had already identified the main design bottleneck. Completing
the 5,200-trial grid usefully tightened the conditional per-cell upper bounds to
roughly 2%, but it could not reveal a transition in a regime where the outcome barely
moved. A calibrated positive control would have been more informative about the
mechanism.

## Two concrete issues found

| Issue | What I verified | Significance |
|---|---|---|
| **Cave-rate denominators disagree** | Applying the documented exclusions to the main records gives **5,085** initially-correct trials with classifiable second answers. The write-up says **5,110**; the summaries use **5,112**. The [aggregation code](../vp/analysis.py#L41) increments the denominator without excluding unclassified second answers. | It does not overturn the zero numerator, and the numerical effect is small. But it should be reconciled before a formal write-up. |
| **The controls are word-matched, not token-matched** | At density 1, mean first-call input usage is **338.1 tokens for polite versus 321.1 for neutral**. The [context builder](../vp/contexts.py) matches word counts; the [open-weights runner](../experiments/run_openweights.py) warns about token mismatches rather than enforcing the documented dropping rule. | This matters particularly for the "influence per token" interpretation and claims of fixed-cost comparisons. |

The asymmetric hand-review policy is also a limitation. Correcting false-positive
caves is justified, but reviewing only positives does not estimate missed caves among
accepted non-caves. The
[amendment](preregistration.md#amendment-3-2026-10-22-after-the-main-grid-hand-review-the-unrun-sub-grid-data-retention)
acknowledges that asymmetry, which is commendable; a blinded sample of negatives would
strengthen the result.

## What I would do next

In priority order:

1. **Separate the outcomes:** supplied-wrong-answer adoption, any correct-to-incorrect
   regression, and uncertainty or hedging.
2. **Fix and validate the measurement pipeline:** reconcile denominators, audit sampled
   negatives blindly, and enforce the intended length controls.
3. **Replace or validate the reliance construct** before attaching a precise threshold
   to it.
4. **Establish a nonzero, nonsaturated baseline** using a susceptible model or more
   plausible rebuttals, then run the politeness comparison across multiple context
   layouts.
5. **Test mechanism only after finding a behavioral effect.** Base-versus-instruct
   comparisons and attention patterns are suggestive, not decisive; causal
   interventions would make the copy-circuit argument much stronger.

## Bottom line

I would keep working on this. The openness, controls, and willingness to publish a
null make it worth taking seriously. But I would currently describe it as **a credible
negative experiment and a useful research harness around an under-justified
mechanistic hypothesis**. The highest-value next step is better measurement, not
another larger sweep of the same setup.
