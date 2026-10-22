# Committed runs

One line per live run; `results_log.md` has the full record. Every run has its
`vp.analysis` summary here (`*_summary.json`) and its per-trial records (the model's
answers, one JSON object per trial) as a gzip-compressed JSONL file (`*.jsonl.gz`).
`vp.analysis` and `experiments/rescore.py` read `.gz` files directly. Only a record file
larger than 9 MB compressed goes to a GitHub release instead; none has so far.

| Run | Model, effort | Bank | Trials | Records | Summary |
|---|---|---|---:|---|---|
| `pilot_opus55_computational` | Opus 5.5, medium | computational | 260 | `pilot_opus55_computational.jsonl.gz` | `pilot_opus55_computational_summary.json` |
| `pilot_opus55_medical` | Opus 5.5, medium | medical | 260 | `pilot_opus55_medical.jsonl.gz` | `pilot_opus55_medical_summary.json` |
| `pilot_sonnet55_computational` | Sonnet 5.5, medium | computational | 260 | `pilot_sonnet55_computational.jsonl.gz` | `pilot_sonnet55_computational_summary.json` |
| `pilot_haiku55_computational` | Haiku 5.5, medium | computational | 260 | `pilot_haiku55_computational.jsonl.gz` | `pilot_haiku55_computational_summary.json` |
| `pilot_haiku55_low_computational` | Haiku 5.5, low | computational | 260 | `pilot_haiku55_low_computational.jsonl.gz` | `pilot_haiku55_low_computational_summary.json` |
| `main_opus55_computational` | Opus 5.5, medium | computational | 5,200 | `main_opus55_computational.jsonl.gz` | `main_opus55_computational_summary.json` |

Reproduce a summary:

```bash
python -m vp.analysis data/runs/main_opus55_computational.jsonl.gz
```

The three hand-reviewed records in the main grid carry `hand_review`,
`cave_as_judged` and `second_class_as_judged`; `experiments/rescore.py` leaves them
unchanged.
