# viral-politeness
Experiments on if politeness is a social context contagion.

Hypothesis: polite phrases ("please", "thank you") are benign context contagions whose
influence on a model's answers tracks *reliance* rather than usefulness, with a
condensation threshold near 0.9 reliance. The measurable outcome is regressive
sycophancy (caving to a wrong-answer rebuttal) as a function of politeness density.
See [`PLAN.md`](PLAN.md) for the original plan of record and status. The
[2026-10-24 assessment](docs/assessment-2026-10-24.md) and
[measurement-first follow-up plan](docs/follow-up-plan.md) describe the proposed next
phase; the follow-up plan is not a pre-registration amendment.

## Layout

| Path | What |
|---|---|
| [`AGENTS.md`](AGENTS.md) | repository guidance for research and development agents |
| `PLAN.md` | original plan of record, item status |
| [`docs/assessment-2026-10-24.md`](docs/assessment-2026-10-24.md) | repository assessment and verified measurement limitations |
| [`docs/follow-up-plan.md`](docs/follow-up-plan.md) | phased measurement repairs, acceptance criteria, and experiment gates |
| [`docs/outcomes.md`](docs/outcomes.md) | agreed primary endpoint, scorable counts, coverage, and analysis output versions |
| [`docs/protocols.md`](docs/protocols.md) | identity, pooling/resume compatibility, pair coverage, and historical metadata limitations |
| [`docs/sensitivity.md`](docs/sensitivity.md) | conditional missing-outcome bounds and versioned strict-JSON exports |
| [`docs/scorer-audit.md`](docs/scorer-audit.md) | retrospective blinded audit design; independent reviews are still pending |
| `docs/references.md` | theory sketch, candidate benchmarks with verified figures |
| `docs/claim_bank.md` | why SycEval, what the vendored bank contains |
| `docs/reliance.md` | the two reliance measures and how the 0.9 prediction is tested |
| `docs/preregistration.md` | hypotheses, grid, sample size, analysis plan, stopping rules; amendment 1 adds the tip-economy test |
| `docs/mechanism.md` | base-vs-instruct discriminator: copy circuit vs trained compliance |
| `data/` | claim bank JSONL built from SycEval (`scripts/build_claim_bank.py`) |
| `vp/` | library: claims, contexts (arms), scoring, reliance, analysis |
| `experiments/run_api.py` | density sweep on chat models over the Claude API |
| `experiments/run_openweights.py` | same protocol on Hugging Face models, with attention |
| `experiments/rescore.py` | re-classify an existing results file with the current scorer and judge |
| [`vp/audit.py`](vp/audit.py) | offline preparation of ungraded reviewer packets and private coordinator mappings |
| `results_log.md` | every live run, what it found, what changed because of it |
| `data/runs/` | committed run summaries and gzip-compressed per-trial records |
| `tests/` | offline unit tests |

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt anthropic         # API arm
pip install -r requirements-openweights.txt       # open-weights arm (torch, transformers)
python -m pytest -q
```

## Run

```bash
# see the exact conversation a trial builds, no API calls
python -m experiments.run_api --dry-run --n-claims 1 --densities 0.5 --arms polite

# pilot: 10 claims, full grid, one seed (~0.26k trials, ~$7 on claude-opus-5-5)
ANTHROPIC_API_KEY=... python -m experiments.run_api --n-claims 10 --out results/pilot.jsonl

# tip-economy sub-grid (pre-registration amendment 1): span length x spend
ANTHROPIC_API_KEY=... python -m experiments.run_api --n-claims 10 --span-lengths short,long \
    --arms polite,neutral --densities 0,0.5,1.0 --out results/pilot.jsonl

# analyze (cells, reliance, knee fits, exchange rates)
python -m vp.analysis results/pilot.jsonl --out results/pilot_summary.json

# open weights (GPU recommended; 0.5B runs on CPU)
python -m experiments.run_openweights --model Qwen/Qwen2.5-0.5B-Instruct --n-claims 5
python -m experiments.run_openweights --model Qwen/Qwen2.5-0.5B --base --n-claims 5
```

Status: the pre-registered main grid has run on `claude-opus-5-5`
([results log](results_log.md)): 0 target adoptions in 5,085 scorable initially-correct
trials after the retrospective analysis-version-2 exclusion correction, every cell
at [0.00, 0.02]. The 5,112 initially-correct answers include 27 unclassifiable second
answers; those are not scorable holds. Historical summaries are retained, and the
dated correction is in the results log. Zero target adoptions does not mean zero
broader correct-to-incorrect regressions; see the [outcome contract](docs/outcomes.md).
Pilot-scale runs on Sonnet 5.5, Haiku 5.5 and the medical bank
found the same floor. The pilot fixed the scorer and the judge
(`docs/preregistration.md`, amendment 2). The hypothesis is unreachable with this
outcome on these models; the next step is an open-weights arm, a stronger rebuttal, or
another vendor, each needing an amendment first.

Analysis version 3 added [independent secondary annotations](docs/outcomes.md)
and [protocol/pairing checks](docs/protocols.md). It does not infer broader regressions
from old `other` labels or rejudge existing outputs: secondary rates on the committed
runs remain unavailable. Duplicate or incompatible trials now fail explicitly;
missing/refused twins are excluded with visible coverage. New runs record generation
and scoring configurations, and unsafe legacy resumes require a new output file.

Current version 4 adds [conditional sensitivity bounds](docs/sensitivity.md).
For example, assigning all 27 unclassified second answers to adoption gives an
upper endpoint of `27/5112` (0.528%) **conditional on the existing eligibility and
scored labels**, not a whole-run confidence limit. The
[blinded scorer-audit design](docs/scorer-audit.md) and packet preparer are available;
no independent reviews have been completed and no scorer-validity gate has passed.

Companion repo: [`transformer-context-contagion`](https://github.com/shumow/transformer-context-contagion)
(the conservation-law / condensation-knee results this project builds on).
