# Working on viral-politeness

These instructions apply throughout this repository. This is a research harness for
testing whether politeness in conversation history changes a model's response to a
wrong-answer rebuttal. Preserve the distinction between a hypothesis, a measurement,
and an established result.

## Read first

- [README](README.md): setup, entry points, and the original reported result.
- [Original plan](PLAN.md) and [pre-registration](docs/preregistration.md): historical
  design, hypotheses, exclusions, stopping rules, and amendments.
- [Results log](results_log.md) and [committed runs](data/runs/README.md): what actually
  ran, scoring changes, and retained evidence.
- [Outcome contract](docs/outcomes.md): primary endpoint, scorable denominators,
  independent secondary annotations, coverage, and analysis-version compatibility.
- [Protocol checks](docs/protocols.md): trial identity, pooling/resume compatibility,
  missing-twin coverage, and unverified legacy metadata.
- [Assessment](docs/assessment-2026-10-24.md): independently checked limitations at
  revision `1b7f773`.
- [Follow-up plan](docs/follow-up-plan.md): planned measurement repairs and decision
  gates. It is not an implemented change or a pre-registration amendment.

For new work, use the follow-up plan without rewriting the historical protocol to
match later decisions. Append dated amendments before collecting data under a changed
design; identify retrospective reanalysis explicitly.

## Code map

- [Claims](vp/claims.py) loads the vendored SycEval banks; the
  [builder](scripts/build_claim_bank.py) records upstream provenance.
- [Contexts](vp/contexts.py) builds all four arms with shared layouts and word-matched
  phrase sets. Density controls spans in prior user turns, not the final question.
- [Scoring](vp/scoring.py), [reliance](vp/reliance.py), and
  [analysis](vp/analysis.py) are shared measurement code. Reuse them across runners
  rather than introducing divergent outcome definitions.
- The [API runner](experiments/run_api.py) uses a heuristic plus an optional judge.
  The [open-weights runner](experiments/run_openweights.py) uses heuristic scoring and
  adds attention measurements; it is not exercised in CI.
- [Rescoring](experiments/rescore.py) reads existing outputs without rerunning the
  tested model; it can still make paid judge calls unless the judge is disabled.
- [Tests](tests) are offline; [CI](.github/workflows/tests.yml) runs pytest.

## Research constraints

- The recorded main run has zero final target-adoption flags, not proof of zero
  correct-to-incorrect regressions or of no politeness effect in general.
- Historical prose reports 5,110 scorable trials and stored version-1 summaries use
  5,112. Analysis versions 2 and 3 reproduce 5,085 after the documented second-answer
  exclusions, while preserving first-answer accuracy counts. See the correction in
  the results log; do not mix historical and corrected summary versions.
- Separate adopting the supplied wrong answer, inventing another incorrect answer,
  and uncertainty. An unclassified answer is not evidence of a successful hold.
  Quoting or refuting an answer is not committing to it.
- Legacy behavioral reliance measures first-answer **class disagreement** between
  polite and neutral twins. It can miss changes in later susceptibility. Do not
  equate it with causal reliance or attention mass, or transfer a 0.9 threshold
  merely because measures share a zero-to-one range.
- A floor effect can make a threshold untestable; it does not establish the mechanism.
  Attention correlations and base-versus-instruct differences alone are not causal
  evidence for induction heads or trained social compliance.
- Phrase sets are currently word-matched, not guaranteed token-matched. Do not claim
  fixed token cost without checking the actual tokenizer or billed usage.
- Treat findings from the
  [companion project](https://github.com/shumow/transformer-context-contagion) as
  motivation, not a proven transfer to ordinary polite language.

## Evidence and experiment hygiene

- Preserve committed trial records, original judgments, and hand-review annotations.
  Produce versioned derived outputs for reanalysis; do not silently overwrite history
  or remove an override because a new judge disagrees.
- Secondary annotations require provenance, independent judgments, and a matching
  source fingerprint. Legacy `other` is not a broader-regression label. No committed
  run currently has secondary annotations, so its secondary rates are unavailable.
- Do not bypass duplicate/protocol errors by dropping records, inventing metadata,
  or renaming models. Analyze incompatible configurations separately. Missing/refused
  twins must remain visible in pair coverage.
- Keep refused, truncated, unparseable, and otherwise unscorable responses visible in
  counts. Report exclusions and per-outcome denominators explicitly.
- Record the protocol/scorer version, model actually served, judge settings, sampling
  and effort, claim IDs, layout seeds, and token usage for new runs. Do not silently
  substitute a different model or merge incompatible protocols.
- Do not launch paid calls, judge rescoring, or model-weight downloads without an
  approved run specification and budget. A documentation or code task is not approval
  to collect data. Use benign known-answer tasks, not third-party production targets.
- Preserve [claim-bank provenance](docs/claim_bank.md) and [attribution](NOTICE).
  Medical wrong answers can be implausible; they are not interchangeable with the
  computational bank as a robustness test.

## Development and validation

Use the existing dependencies and simple shared functions. Add focused offline
regressions for measurement changes, especially exclusions, paired records, quoted
answers, equivalent mathematical forms, and degenerate fits. Validate the smallest
affected test set before expanding to the suite.

Offline entry points, run from the repository root:

```text
python -m pytest -q
python -m experiments.run_api --dry-run --n-claims 1 --densities 0.5 --arms polite
```

Follow the [setup instructions](README.md#setup) when dependencies are needed.
Documentation-only changes do not require model calls or a test run. Update the
directly affected research notes when behavior changes, and state what was actually
validated rather than treating a successful unit test as validation of the theory.
