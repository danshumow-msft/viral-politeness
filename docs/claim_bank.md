# Claim bank (plan item 1)

**Decision: SycEval is the primary claim bank; BrokenMath is secondary and not yet
ingested.** Both banks are exposed through one schema (`vp/claims.py`) so runners never
depend on the source.

## What SycEval actually contains

The SycEval repository
([DaneshjouLab/Sycophantic-Behavior-Benchmark](https://github.com/DaneshjouLab/Sycophantic-Behavior-Benchmark),
Apache-2.0) ships three complete runs, one per model (ChatGPT-4o, Claude-Sonnet,
Gemini-1.5-Pro), each with 500 computational items (AMPS algebra, 28 sub-types) and 500
medical items (MedQuAD). Every item has the question and the ground-truth answer.

The detail that matters for us: SycEval's deliberately **wrong** answer (`proposed_answer`)
is only generated when the model answered correctly on the first try, because that is the
only case in which the rebuttal has to push toward a wrong answer. So per model run only a
subset of items carries a wrong answer. Merging the three runs gives the union:

| Bank | Items | With a known wrong answer | With more than one distinct wrong answer |
|------|------:|-------------------------:|------------------------------------------:|
| `syceval_computational` | 500 | 200 | 108 |
| `syceval_medical` | 500 | 390 | 308 |

The computational wrong answers are numerically plausible perturbations (for example
`cos(16804) = 0.123` against the true `-0.929`). The medical ones are LLM-generated and
often absurd ("an overabundance of sparkles in cells"), which makes caving to them a much
stronger signal but also a less realistic one. **The computational bank is the default**;
the medical bank is kept for a robustness check.

The 300 computational items without a wrong answer are retained in the JSONL (with
`wrong_answers: []`) so a later step can generate wrong answers for them if 200 turns out
to be too few. The loader filters them out by default.

## Schema (`data/*.jsonl`, one object per line)

| Field | Meaning |
|-------|---------|
| `id` | SycEval file stem, e.g. `Computational_algebra_find_roots_120` |
| `category`, `sub_category`, `sub_sub_category` | SycEval's taxonomy |
| `question` | the bare question, SycEval's "Do not show work" / "CONCISE" suffix removed |
| `question_raw` | the question exactly as SycEval posed it |
| `correct_answer` | ground truth from AMPS / MedQuAD |
| `wrong_answers` | every distinct wrong answer SycEval used for this item, in model order |
| `wrong_answer_sources` | which model run each wrong answer came from |
| `syceval_initial_correct` | per model, whether SycEval's run got the question right first time |

## Rebuilding

```bash
git clone --depth 1 https://github.com/DaneshjouLab/Sycophantic-Behavior-Benchmark /path/to/syceval
python -I scripts/build_claim_bank.py /path/to/syceval data/
```

The build is deterministic; a rebuild from the same clone produces no diff.

## Licensing

SycEval code and derived data: Apache-2.0. AMPS (Hendrycks et al.): MIT. MedQuAD
(Ben Abacha and Demner-Fushman): CC BY 4.0. See `NOTICE`.

## BrokenMath (secondary, deferred)

BrokenMath ([arXiv 2510.04721](https://arxiv.org/abs/2510.04721), Petrov, Dekoninck,
Vechev) perturbs 2025 competition theorems into false statements and asks for proofs.
Scoring needs an LLM judge, which adds a second model to every cell. It is worth adding
only once the SycEval arm shows an effect worth cross-checking with a harder, more
natural false premise.
