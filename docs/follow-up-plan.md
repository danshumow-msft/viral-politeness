# Measurement-first follow-up plan

Date: 2026-10-24.

Status: planned; no work package below is implemented by adding this document.

This plan turns the [assessment](assessment-2026-10-24.md) of revision
[`1b7f773`](https://github.com/shumow/viral-politeness/tree/1b7f7734987c32281c34423407c6ca8f87d4e7b4)
into actionable work. It guides follow-up development without replacing the
[original plan](../PLAN.md) or amending the [pre-registration](preregistration.md).
New hypotheses, outcomes, sampling rules, and live runs require a dated protocol
decision before data collection. Reanalysis of existing records must be labeled
retrospective.

## Objective and non-goals

First make the measurement trustworthy. Then establish whether a controlled
politeness manipulation changes behavior in a regime with measurable susceptibility.
Only after that should the project test a reliance threshold or a copy-circuit
mechanism.

This is not a plan to find a positive result at any cost. A well-powered, scoped null,
an unreachable mediator, and an inconclusive mechanism are all reportable outcomes.
Do not enlarge the same floor-effect grid, assume the short/long-span result from
medium spans, or reinterpret a new measure until it crosses 0.9.

## Baseline to preserve

The [main-run records](../data/runs/main_opus55_computational.jsonl.gz), their
[summary](../data/runs/main_opus55_computational_summary.json), and the
[results log](../results_log.md) describe 200 computational claims, one layout seed,
medium spans, and eight prior user turns:

| Quantity | Baseline finding from the assessment |
|---|---|
| Recorded trials | 5,200 |
| Refused trials | 2 |
| Non-refused trials labeled initially correct | 5,112 |
| Initially-correct trials with a classifiable second answer | 5,085 |
| Initially-correct trials with second answer labeled `other` | 27 |
| Final recorded target-adoption flags | 0 |
| Judge-positive caves manually overridden | 3, all verified reaffirmations |

The historical prose reports 5,110 scorable trials, while the summaries use 5,112.
The 5,085 count applies the documented exclusions to the current annotations; it is
not a new, independently adjudicated correctness result. Five completing-the-square
responses illustrate real correct-to-new-incorrect regressions hidden inside `other`.
At density 1, polite and neutral prompts also differ in mean billed input tokens:
338.1 versus 321.1. These are starting facts to reconcile, not completed repairs.

## Work packages and dependencies

All packages start as **planned**. Dependencies are explicit; independent offline
packages may proceed in parallel after their common prerequisite.

| ID | Work package | Depends on | Completion gate |
|---|---|---|---|
| M1 | Outcome contract and provenance | None | Endpoint definitions and versioning agreed |
| M2 | Correct aggregation and baseline reconciliation | M1 | Counts and exclusions reproduce exactly |
| M3 | Scorer validation and balanced audit | M1 | Error rates and unresolved cases reported |
| M4 | Matched prompts and auditable run configuration | M1 | Matching policy enforced and tested |
| M5 | Reliance and statistical redesign | M1; M2-M4 for final validation | Valid mediator, or explicit behavioral-only scope |
| M6 | Calibration pilot | M2, M3, M4, M5; approved protocol and budget | Nonzero, nonsaturated regime or a documented stop |
| M7 | Confirmatory behavioral study | M6; frozen analysis and approved budget | Paired effect estimates with uncertainty |
| M8 | Causal mechanism study | Reproducible positive behavior from M7 | Intervention evidence or an explicit inconclusive result |

### M1. Define outcomes before changing the scorer

**Work**

- Define correctness independently from commitment to the supplied rebuttal target.
  Keep at least three distinct readouts: supplied-wrong-answer adoption, any
  correct-to-incorrect regression, and uncertainty or hedging.
- Specify whether and how those readouts overlap. A tentative mention, a quoted
  answer, a rejected answer, an equivalent expression, and an asserted new wrong
  answer must not collapse into the same category.
- Distinguish genuinely unscorable output from a scored but unfamiliar answer.
  Refusals, empty/truncated answers, judge failures, and invalid references need
  explicit statuses, not implicit non-events.
- Define eligibility and denominators separately for each endpoint. Preserve
  first-answer accuracy independently from second-answer scorable status. Keep
  correct-answer rebuttals and progressive flips separate from wrong-answer adoption.
- Choose a versioned record/annotation contract that preserves existing classes,
  flags, judge verdicts, and hand reviews. New annotations must identify their
  scorer/protocol version and provenance; legacy records must remain readable.

**Surfaces:** [scoring](../vp/scoring.py), [API runner](../experiments/run_api.py),
[open-weights runner](../experiments/run_openweights.py),
[rescoring](../experiments/rescore.py), and [analysis](../vp/analysis.py).

**Acceptance:** a compact decision table covers each case above, including the three
verified overrides and the five completing-the-square regressions. Historical target
adoption and the broader new endpoint are reported under different names, not silently
substituted for one another.

### M2. Repair aggregation and reconcile the historical record

**Work**

- Add explicit per-outcome scorable denominators rather than changing the meaning of
  the initially-correct count used for first-answer accuracy.
- Count every refusal and missing/unclassified second answer; exclude them from the
  relevant scorable rate, not from the accounting. Report coverage beside rates.
  Show sensitivity bounds where unknown outcomes could materially change a conclusion.
- Check pairing keys, duplicate trials, missing twins, and incompatible protocol
  versions before pooling. Do not silently discard ambiguous pairings.
- Independently reconcile all six [committed runs](../data/runs/README.md), then
  regenerate versioned summaries. Preserve source records and identify any replaced
  derived summary with a dated explanation.
- Add a correction entry to the results log and update current result statements
  only after the counts are reproducible. Do not rewrite the original protocol.

**Acceptance**

- With the existing main-run annotations, aggregation reports 5,200 total trials,
  2 refusals, 5,112 initially correct, 27 initially-correct/unclassified-second cases,
  and 5,085 scorable initially-correct cases, with zero final target-adoption flags.
- Offline regressions cover mixed second-answer classes, both-call refusals,
  empty cells, progressive trials, missing twins, and plain/gzip inputs. Rates and
  Wilson intervals use their declared denominator; no eligible trials is displayed
  as unavailable, not evidence of a zero event probability.
- Generated tables, summaries, and narrative figures agree. Subsequent adjudication
  changes produce a new annotation version rather than invalidating the audit trail.

### M3. Validate scoring in both directions

**Work**

- Build a small labeled fixture set from existing responses plus benign synthetic
  cases: genuine adoptions, holds quoting the target, new incorrect answers,
  equivalent algebra, negations, hedges, and ambiguous conventions.
- Separate development fixtures from an audit set before tuning the scorer or judge.
  Validate commitment as well as mathematical correctness; overlapping reference
  numbers alone do not establish either.
- Design an audit of accepted non-caves as well as positives and `other` responses.
  Predeclare sample sizes, selection seeds, strata, and acceptable error/uncertainty
  bounds. Blind reviewers to arm, density, model identity, and existing verdict
  where feasible; retain disagreements and their adjudication.
- Report false positives, false negatives, coverage, and uncertainty, not only
  agreement on an all-hold pilot. Keep judged and reviewed results distinguishable.
- Preserve the three existing overrides. Reassessing them under a broader outcome
  needs an explicit new annotation, not removal of the historical review.

**Acceptance:** [scoring tests](../tests/test_scoring.py),
[rescoring tests](../tests/test_rescore.py), and offline mocked-runner tests verify
the outcome contract. Audit results and unresolved reference issues are recorded;
the measurement gate is not declared passed merely because the judge emits valid
JSON. Paid rejudging or external review services require separate approval.

### M4. Make the intervention and its cost measurable

**Work**

- Retain polite, neutral, rude, and authority-loaded arms with matched claim,
  positions, phrase indices, and declared layout schedules.
- Choose a token-matching policy per tokenizer before running: adjust or filter
  aligned phrase indices, declare a tolerance, and fail preflight if it cannot be
  met. A warning followed by an unmatched run is not enforcement.
- When an API tokenizer is unavailable, use a declared token-counting facility if
  available or label the design word-matched. Report actual billed usage and limit
  fixed-cost claims accordingly; do not treat word counts as exact token costs.
- Record realized span counts as well as nominal densities. Eight prior turns permit
  only nine span counts; nearby density labels can produce identical interventions.
  Any change in turn count or density resolution needs a protocol amendment.
- Record a run manifest: claim IDs, seeds, phrase set, rendered contexts or a
  reproducible equivalent, requested/served model, judge, decoding and effort,
  token limits, matching policy, and protocol/scorer versions. Resume and pooling
  must reject incompatible configurations.

**Acceptance:** [context tests](../tests/test_contexts.py) cover all lengths and
arms, deterministic layouts, token-mismatch enforcement, and realized density.
Offline mocked runners verify manifests and shared outcome semantics. Validate an
open-weights smoke separately before claiming runtime support; CI does not exercise
the current open-weights runner. No weight download is implied by this package.

### M5. Replace unsupported reliance and prediction claims

**Work**

- Retain the legacy first-answer disagreement statistic as a descriptive sensitivity
  measure, not a validated causal mediator. On a common paired sample its maximum is
  bounded by the sum of the two arms' non-correct rates: about 0.04 when each is 98%
  correct. Document that attainable range before interpreting a threshold.
- Test candidate measures on controlled examples where first answers stay correct
  but susceptibility after rebuttal changes. A measure that misses this case cannot
  by itself test the proposed social mechanism.
- Keep outcome sensitivity, attention, and causal reliance separate. In particular,
  do not rename the adoption treatment effect "reliance" and then use it to predict
  the same adoption outcome.
- Require an independent justification and attainable range for a new mediator.
  Do not carry over the numerical 0.9 prediction by rescaling. If no defensible
  mediator is available, register a behavioral-effect study and defer H2/H3.
- Compare predictors with a declared predictive criterion, such as held-out log
  loss or binomial deviance, on the same held-out observations. Split by claim so
  related arms/layouts cannot leak across training and evaluation. Logistic width
  alone is not a predictive comparison.
- Use paired treatment contrasts and account for repeated claims/layouts in
  uncertainty estimates. Predeclare a primary comparison and multiplicity policy;
  do not infer a difference solely from overlap of marginal Wilson intervals.
- For all-zero/all-one outcomes or inadequate predictor variation, report the fit
  or threshold as not estimable with a reason. Numerical convergence is not evidence
  that an extrapolated midpoint is meaningful.

**Acceptance:** the revised [reliance note](reliance.md) and statistical specification
state exactly which claims can be tested. Synthetic tests distinguish a detectable
behavioral effect from unchanged first-answer classes, and reject degenerate knee
claims. Final validation uses the measurement and matching contracts from M2-M4.

### M6. Find a testable regime with a bounded calibration pilot

**Work**

- Before any new calls, approve and record a calibration protocol: candidate models,
  rebuttal strengths, claim split, layout replication, classification coverage,
  acceptable baseline-susceptibility range, maximum attempts, and a total budget cap.
  Set numerical go/no-go thresholds before observing pilot outcomes.
- Start with a small, justified candidate set, such as a smaller open-weights
  instruct model or more plausible rebuttals. Do not search models and prompts
  indefinitely until a desired politeness effect appears.
- Verify positive controls can elicit genuine wrong-target adoption and negative
  controls preserve correct answers, without using those controls as the treatment
  effect estimate. Check first-answer accuracy and scorable coverage as well.
- Keep calibration separate from confirmatory claims. Reserve claims before tuning
  where feasible; if the bank cannot support a holdout, explicitly classify the
  subsequent reuse as exploratory rather than calling it independent confirmation.

**Acceptance:** a documented regime has nonzero, nonsaturated susceptibility with
measurement uncertainty acceptable under the preregistered rule, or the pilot stops
with a report that no candidate met the gate. Stronger pressure may change the
phenomenon; record that change rather than treating it as the original experiment.

### M7. Run the confirmatory behavioral study

**Work**

- Freeze the protocol and analysis after calibration: models, claim set, arms,
  realized density grid, multiple layout seeds, primary endpoint, effect size of
  interest, exclusions, paired inference, power/sample-size rationale, and budget.
- Run the approved design to its declared stopping rule. Record failures and
  refusals; never silently substitute a model or repeat selected cells until they
  become significant.
- Report adoption, broader regressions, uncertainty, first-answer accuracy, and
  classification coverage separately. Report effect estimates and intervals even
  when every arm is zero.
- Add the short/long-span or exchange-rate study only under its own approved
  design. Include measured token costs and uncertainty; medium-span results do not
  establish the unrun span-length result.

**Acceptance:** an auditable record, balanced scoring audit, and reproducible
summaries support a clearly scoped positive, null, or inconclusive behavioral result.
If the floor persists, stop mechanistic escalation and report the bound.

### M8. Test mechanism with interventions, not just correlations

**Work**

- Select matched base/instruct checkpoints only after the behavioral effect
  replicates. Account for differences in task competence, prompts, coverage, and
  rebuttal handling before interpreting checkpoint differences.
- Measure all-head and induction-head attention, but treat those as descriptive
  until interventions test necessity. Compare targeted ablations with matched
  random-head controls and monitor general answer quality.
- Where feasible, use restoration or another specificity check to distinguish loss
  of the proposed mechanism from generic model damage.

**Acceptance:** support for copying requires a specific causal intervention result,
not just increased attention. An instruct-only effect does not by itself prove
preference-training causation. If evidence does not discriminate mechanisms, report
it as inconclusive and update the [mechanism note](mechanism.md) accordingly.

## First implementation slice and decision gates

The recommended first code change is **M1 plus a narrow M2 regression**: agree on
endpoint/eligibility definitions, add a fixture where a correct first answer has an
unclassified second answer, and separate the scorable denominator from first-answer
accuracy. Then reconcile the existing summaries without making new model calls.

Before advancing to live work, the owner must approve:

- the primary endpoint and treatment of scored-new-wrong versus unscorable answers;
- scorer-audit sample sizes and acceptable error bounds;
- token-matching policy and any unavailable-tokenizer limitation;
- a validated reliance measure or explicit deferral of the threshold hypothesis;
- numerical calibration gates, claim splits, model choices, and budget/stopping caps.

Each implementation package should include focused offline tests and a dated account
of its validation. Use existing [tests](../tests) and entry points rather than adding
new tooling by default. Update this plan's status only when its completion evidence
exists; a planning document or passing unit test alone does not validate the research
claim.
