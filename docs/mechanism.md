# Mechanism discriminator (plan item 7)

The companion repo's condensation knee is caused by repetition driving induction heads:
a repeated out-of-distribution string crosses a threshold and the in-context copy circuit
reproduces it. Polite phrases are short, common, in-distribution strings. A base model has
no reason to treat them as novel, so a priori the copy-circuit story is weak here. If
politeness does move cave rate in chat models, the likelier mechanism is trained social
compliance from preference optimization, which has nothing to do with context copying.
The design has to be able to tell these apart, or a positive result on H1 says little
about the context-contagion theory.

## The comparison

Run `experiments/run_openweights.py` on matched base and instruct checkpoints of the
same family at the same densities, and read two things per cell:

| | Copy-circuit mechanism | Trained-compliance mechanism |
|---|---|---|
| Base checkpoint cave rate | rises with density | flat |
| Instruct checkpoint cave rate | rises with density | rises with density |
| Attentional lift, all heads | rises with density at the knee | flat or unrelated to cave rate |
| Attentional lift, induction heads | rises more than all-heads lift | no difference from all-heads |
| Behavioral reliance | tracks attentional lift | moves without attentional change |

A base model has no rebuttal-handling behavior to speak of, so for the base arm the
first-answer sensitivity (behavioral reliance) is the main readout and the cave rate is
secondary. For instruct models both are read.

## Checkpoint pairs

- Qwen2.5-7B / Qwen2.5-7B-Instruct
- Llama-3.2-3B / Llama-3.2-3B-Instruct
- Qwen2.5-0.5B / Qwen2.5-0.5B-Instruct for CPU smoke tests only

These are the same families as the companion repo's size sweep, so the induction-head
detection (repeated-random-sequence score, top 8 heads) is directly comparable to its
E2 results.

## What each outcome means for the theory

- **Copy-circuit signature present.** Politeness is a context contagion in the companion
  repo's sense, and the conservation law (influence tracks reliance, not usefulness)
  extends to in-distribution benign spans. This would be the strong result.
- **Compliance signature only.** Politeness changes answers, but through training, not
  through the context mechanism. The "tip economy" framing survives (the phrases still
  cost tokens and still buy influence), the Pólya-urn framing does not.
- **Neither.** Politeness at these densities does not move answers. Report the null with
  the intervals; the reliance measure then bounds how much the model attends to the
  spans at all.

Tokenizer caveat: the arms are word-count matched; the runner checks token-count
alignment under each tokenizer and warns if any phrase index differs by more than one
token across arms. Any such index is dropped from the span pool before the run and the
drop is recorded in the amendments of `docs/preregistration.md`.
