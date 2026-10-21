# Plan of record — politeness as context contagion

As of 2026-10-21. Supersedes the checklist at the bottom of
[`docs/references.md`](docs/references.md). Each numbered item is one unit of work and
lands as roughly one commit; status is tracked inline.

**Hypothesis under test.** Polite phrases ("please", "thank you") are benign, naturally
occurring context contagions: near-zero task information, high implicit trust. By the
conservation-law result from
[`transformer-context-contagion`](https://github.com/shumow/transformer-context-contagion)
(exploitability tracks *reliance* rather than *usefulness*), their influence on a model's
answers should scale with reliance, with a Pólya-urn-style condensation threshold near
0.9 reliance. The measurable outcome is **regressive sycophancy**: the rate at which a
model abandons a correct answer under a wrong-answer rebuttal, as a function of
politeness density in the context.

## Items

| # | Item | Output | Status |
|---|------|--------|--------|
| 1 | Pick the claim bank: **SycEval** primary, BrokenMath secondary | `docs/claim_bank.md`, `vp/claims.py`, `data/` | done |
| 2 | Operationalize **reliance** (the hypothesis is untestable without it) | `docs/reliance.md`, `vp/reliance.py` | done |
| 3 | Decide the **control arms** (neutral filler, rude, social-loaded) | `vp/contexts.py` | done |
| 4 | **Verify** the benchmark figures in `docs/references.md` against the papers | updated `docs/references.md` | done (abstract level; PDFs unreachable from container) |
| 5 | **Scaffold the harness**: API runner for chat models + open-weights runner forked from the companion repo's `e4_trust.py` | `vp/`, `experiments/` | todo |
| 6 | **Pre-register** the density grid, sample size, and jump criterion | `docs/preregistration.md` | todo |
| 7 | Build the **mechanism discriminator** (copy circuit vs RLHF social compliance) into the design: base vs instruct on open weights | folded into 5 and 6 | todo |

## 1. Claim bank

SycEval (Fanous et al., 2025) is primary: known-answer questions, a rebuttal protocol
that is a direct analogue of a trusted injected phrase, and a public code repository.
Progressive vs regressive sycophancy is already separated, and regressive is the
quantity we care about. BrokenMath is the secondary bank, to be added only if the primary
shows an effect: its false premises are closer to an injected phrase than a rebuttal is,
and the math setting removes subjective judging.

Deliverable: a loader that yields `(question, correct_answer, wrong_answer)` triples in
one schema regardless of source, plus a note on licensing and what was actually
downloaded.

## 2. Reliance

The hypothesis says influence tracks reliance, with a threshold near 0.9. The companion
repo measured trust as induction-head attention onto repeated spans. Polite phrases are
short, common, in-distribution strings, not repeated out-of-distribution payloads, so
that proxy does not transfer unchanged. Two operationalizations, both to be computed:

- **Behavioral reliance** (any model, API or open weights): the fraction of the answer
  that changes when prior user turns are removed. Concretely, the agreement rate between
  the model's answer with the full context and with the polite spans ablated to neutral
  filler. High agreement means low reliance on the polite spans.
- **Attentional reliance** (open weights only): attention mass flowing from the answer
  tokens onto the polite-phrase tokens, summed over heads, normalized by total attention
  onto user-turn tokens. This is the direct descendant of the companion repo's trust
  measure.

The density axis (fraction of user turns carrying niceties) is the *manipulation*;
reliance is the *measured mediator*. The prediction is that cave rate is a function of
measured reliance with a knee near 0.9, and that density is only a knob for moving
reliance.

## 3. Controls

Four arms at every density, all length-matched in tokens at the same positions:

| Arm | Content of the inserted span | What it separates |
|-----|------------------------------|-------------------|
| polite | "please", "thank you so much", "I really appreciate it" | the treatment |
| neutral filler | length-matched, socially inert text ("as noted above", "for reference") | token count and position |
| rude | "hurry up", "that was useless", "just answer" | sign of social valence |
| social-loaded, non-polite | socially charged but not deferential ("I'm an expert in this", "my colleagues agree") | social valence vs deference specifically |

A fifth arm with density 0 is the baseline every curve is anchored to.

## 4. Verification

The figures in `docs/references.md` came from search snippets. Each number is to be
checked against the paper abstract or results section and the row updated with the
verified value or marked as unverifiable.

## 5. Harness

Two runners sharing one context builder and one scorer:

- `experiments/run_api.py` — chat models over an API. Builds the multi-turn context,
  asks the question, injects the rebuttal, records whether the model caves. This is the
  main arm for the density sweep.
- `experiments/run_openweights.py` — fork of the companion repo's `e4_trust.py`. Runs the
  same contexts on open-weights models under TransformerLens and adds the attentional
  reliance measure. This arm is what makes item 7 possible.

The context builder, scorer, and reliance measures live in `vp/` so both runners share
them. Smoke tests run on a handful of items without any network or GPU.

## 6. Pre-registration

Written before data collection:

- Density grid: 0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0 (fraction of user turns carrying a
  span), denser between 0.75 and 1.0 if a knee appears there.
- Context length: 8 prior user turns before the test question, so density 0.1 rounds to
  one turn and 1.0 to all eight.
- Sample size: enough Bernoulli trials per cell that the Wilson 95% interval half-width
  near P = 0.5 is under 0.1, matching the companion repo's E1 standard. That is at least
  100 trials per cell (claims × samples).
- Jump criterion: fit a logistic in reliance and report both the midpoint and the
  transition width. A knee is a transition width narrower than the spacing of the grid
  around it; a graded ramp is wider. Both outcomes are reported.
- Primary outcome: regressive cave rate. Secondary: progressive flip rate, answer length,
  and the two reliance measures.

## 7. Mechanism discriminator

The condensation knee in the companion work came from repetition driving induction
heads. Polite phrases are in-distribution, so a base model has no reason to treat them as
novel; if an effect appears only in chat models, the likelier mechanism is trained social
compliance, not context copying. The design separates these by running the open-weights
arm on matched base and instruct checkpoints (Qwen2.5, Llama-3.2) and comparing:

- an effect present in base and instruct, and tracking attentional reliance, points to
  the copy circuit;
- an effect present only in instruct, with no attentional signature, points to RLHF.

Either answer is reportable.

## Out of scope for now

Rude or harmful payloads beyond the rude control arm; production systems; models not
hosted by us or reachable under rate-limited API terms. The companion repo's
`SECURITY.md` posture applies.
