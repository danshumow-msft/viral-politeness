# viral-politeness
Experiments on if politeness is a social context contagion.

Hypothesis: polite phrases ("please", "thank you") are benign context contagions whose
influence on a model's answers tracks *reliance* rather than usefulness, with a
condensation threshold near 0.9 reliance. The measurable outcome is regressive
sycophancy (caving to a wrong-answer rebuttal) as a function of politeness density.
See [`PLAN.md`](PLAN.md) for the plan of record and status.

## Layout

| Path | What |
|---|---|
| `PLAN.md` | plan of record, item status |
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
| `results_log.md` | every live run, what it found, what changed because of it |
| `data/runs/` | committed per-trial records and summaries |
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

Status: the pilot has run (`results_log.md`). On `claude-opus-5-5` and the computational
bank the model held its first answer in 260 of 260 trials across all arms and densities;
the pilot fixed the scorer and the judge (`docs/preregistration.md`, amendment 2). The
main run's model and bank are being chosen on further pilot-scale runs.

Companion repo: [`transformer-context-contagion`](https://github.com/shumow/transformer-context-contagion)
(the conservation-law / condensation-knee results this project builds on).
