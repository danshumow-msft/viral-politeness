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

Analyze the records with the current implementation:

```bash
python -m vp.analysis data/runs/main_opus55_computational.jsonl.gz
```

## Analysis versions

The committed `*_summary.json` files are historical version-1 outputs. Current
analysis emits `analysis_version: 2` and `outcome_contract_version: 1`, with separate
scorable denominators and exclusion/coverage counts. Rates with no scorable trials
are JSON null, printed as `-`; derived exchange rates and fit weights use scorable
adoption counts. See the [outcome contract](../../docs/outcomes.md).

For the main run, current aggregation preserves 5,112 initially-correct labels but
excludes 27 unclassifiable second answers from the adoption denominator, giving
0 adoptions in 5,085 scorable trials. The [results log](../../results_log.md) records
the retrospective correction across all six runs. No model was rerun or rejudged.
Write any new derived output to a versioned name such as `*_summary_v2.json`, not
over the historical summaries. Pairing/protocol validation and fit-identifiability
improvements remain follow-up work.

The three hand-reviewed records in the main grid carry `hand_review`,
`cave_as_judged` and `second_class_as_judged`; `experiments/rescore.py` leaves them
unchanged.
