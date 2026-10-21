# Politeness as Context Contagion — References

As of 2026-10-21 · Dan Shumow

## Theory

Polite phrases ("please", "thank you") are benign, naturally occurring context contagions: near-zero task information, high implicit trust. By the conservation-law result (exploitability tracks reliance rather than usefulness), their influence should scale with reliance, with a Pólya-urn condensation threshold near 0.9 reliance. Side framing: since usage is billed per token, niceties are a small "tip" economy paid in compute.

## Sycophancy benchmarks

SycEval is the closest fit: it has questions with known answers and measures regressive sycophancy (the model caving to a wrong answer) separately from progressive sycophancy.

| Benchmark | What it measures | Why it fits | Link | Verified |
| --- | --- | --- | --- | --- |
| SycEval (Fanous et al., 2025; AIES 2025) | Progressive vs regressive sycophancy under in-context and preemptive rebuttals on AMPS math and MedQuAD. 58.19% sycophancy overall; 43.52% progressive, 14.66% regressive; preemptive rebuttals 61.75% vs in-context 56.52%; citation rebuttals give the highest regressive rate; 78.5% persistence | Ground-truth answers; rebuttal framing is a direct analogue of a trusted injected phrase | [arXiv 2502.08177](https://arxiv.org/abs/2502.08177), [DOI](https://doi.org/10.1609/aies.v8i1.36598), [code](https://github.com/DaneshjouLab/Sycophantic-Behavior-Benchmark) | Yes: figures and venue confirmed from the abstract in the code repository's README (v4, 2025-09-19). Ingested as the claim bank, see `claim_bank.md` |
| BrokenMath (Petrov, Dekoninck, Vechev, 2025; NeurIPS 2025 / ICML 2026) | Whether models "prove" competition theorems perturbed into false statements, LLM-judged. Best model (GPT-5) still sycophantic on 29% | Math setting, clean false premises; but needs an LLM judge | [arXiv 2510.04721](https://arxiv.org/abs/2510.04721), [sycophanticmath.ai](https://www.sycophanticmath.ai/) | Yes: 29% and construction confirmed from the NeurIPS page and abstract snippets. The original note had no arXiv ID; it is 2510.04721 |
| SYCON Bench (Hong et al., 2025; v4 2026-02-26) | Multi-turn sycophancy: Turn of Flip and Number of Flip across 17 LLMs in debate, unethical-query, and false-presupposition (CREPE-based) scenarios. Finding: alignment tuning amplifies sycophancy, scale and reasoning reduce it | Multi-turn is the natural setting for an accumulating contagion; its "sustained pressure" protocol is reusable for a density sweep | [arXiv 2505.23840](https://arxiv.org/abs/2505.23840) | Yes: title, metrics, and scenarios confirmed from abstract snippets. Originally listed without a name |
| ELEPHANT (Cheng et al., 2025; ICLR 2026) | Social sycophancy as face preservation: LLMs preserve the user's face about 45 percentage points more than humans on open advice queries and r/AmITheAsshole posts; affirm both sides of a moral conflict in 48% of cases | Closest to the "niceties" register, but subjective ground truth | [arXiv 2505.13995](https://arxiv.org/abs/2505.13995), [code](https://github.com/myracheng/elephant) | Yes: 45 pp (abstract; body says 46) and 48% confirmed from abstract snippets |
| lechmazur/sycophancy | Narrator bias: 198 balanced disputes in 14 categories, each in five views (neutral, two stripped first-person, two affective first-person); sycophantic if the model sides with the narrator on both opposite versions. Reports sycophancy, contrarian, and abstention rates separately | Cheap, symmetric control for pure agreement drift | [GitHub](https://github.com/lechmazur/sycophancy) | Yes: README read directly. Top-cohort sycophancy ranges from 0% (with low decisive coverage) to 22.4% |
| The Price of Agreement (Zhao et al., Writer Inc., 2026; ICLR 2026) | Sycophancy in agentic financial QA. Plain rebuttals cause only low-to-modest accuracy drops; injected user preferences that contradict the reference cause most models to fail; benchmarks recovery via input filtering | Injection methodology is reusable for politeness injections | [arXiv 2604.24668](https://arxiv.org/abs/2604.24668) | Partly: existence, venue, and qualitative findings confirmed from abstract snippets; no headline percentage located |

Verification status as of 2026-10-21: arXiv is not reachable from the working container, so figures were checked against the SycEval repository README, the lechmazur README, conference listing pages, and abstract snippets returned by web search, not against the PDFs. Re-check against the PDFs before citing any number in a write-up.

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
