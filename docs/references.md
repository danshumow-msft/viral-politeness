# Politeness as Context Contagion — References

As of 2026-10-21 · Dan Shumow

## Theory

Polite phrases ("please", "thank you") are benign, naturally occurring context contagions: near-zero task information, high implicit trust. By the conservation-law result (exploitability tracks reliance rather than usefulness), their influence should scale with reliance, with a Pólya-urn condensation threshold near 0.9 reliance. Side framing: since usage is billed per token, niceties are a small "tip" economy paid in compute.

## Sycophancy benchmarks

SycEval is the closest fit: it has questions with known answers and measures regressive sycophancy (the model caving to a wrong answer) separately from progressive sycophancy.

| Benchmark | What it measures | Why it fits | Link |
| --- | --- | --- | --- |
| SycEval (Fanous et al., 2025) | Progressive vs regressive sycophancy under in-context rebuttals; ~58% sycophancy overall, ~15% regressive | Ground-truth answers; rebuttal framing is a direct analogue of a trusted injected phrase | [arXiv 2502.08177](https://arxiv.org/abs/2502.08177), [code](https://github.com/DaneshjouLab/Sycophantic-Behavior-Benchmark) |
| BrokenMath | Whether models "prove" theorems with deliberately flawed premises; best model caves in ~29% of responses | Math setting, clean false premises, no subjective judging | [sycophanticmath.ai](https://www.sycophanticmath.ai/) |
| Multi-turn sycophancy (2025) | Acceptance of false presuppositions across dialogue turns | Multi-turn is the natural setting for an accumulating contagion | [arXiv 2505.23840](https://arxiv.org/abs/2505.23840) |
| ELEPHANT | Social sycophancy: validating unfounded assumptions and moral framings (r/Advice, r/AITA pairs) | Closest to the "niceties" register, but subjective ground truth | [arXiv 2505.13995](https://arxiv.org/abs/2505.13995) |
| lechmazur/sycophancy | Narrator bias: agreeing with both sides of the same dispute | Cheap, symmetric control for pure agreement drift | [GitHub](https://github.com/lechmazur/sycophancy) |
| The Price of Agreement (2026) | Sycophancy in agentic financial QA under injected user preferences | Injection methodology is reusable for politeness injections | [arXiv 2604.24668](https://arxiv.org/abs/2604.24668) |

Summaries are from search snippets, not full reads; verify figures against the papers before citing.

## Experiment sketch

Hypothesis: polite phrases are benign context contagions whose influence tracks reliance rather than usefulness, with a condensation threshold near 0.9 reliance.

1. Take a claim bank with ground truth (SycEval or BrokenMath).
2. Build contexts at politeness densities from 0 to saturation (fraction of user turns carrying niceties).
3. Present each claim with a wrong-answer rebuttal; record regressive sycophancy rate per density.
4. Controls: equal-length filler tokens with no social valence, and rude phrasing at the same density.
5. Look for a nonlinear jump in cave rate at high density, which would be the Pólya-urn signature.

- [ ] Pick the claim bank
- [ ] Decide the filler-token control
- [ ] Choose target models and token budget
