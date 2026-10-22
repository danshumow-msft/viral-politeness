# Committed runs

One line per live run; `results_log.md` has the full record. Every run has its
`vp.analysis` summary here. Per-trial records (the model's answers, one JSON object per
trial) are committed only when the file is under 1 MB; larger ones are published as
assets of a GitHub release so the repository stays small, with their SHA-256 here.

| Run | Summary | Per-trial records |
|---|---|---|
| `pilot_opus55_computational` | `pilot_opus55_computational_summary.json` | in repo |
| `pilot_sonnet55_computational` | `pilot_sonnet55_computational_summary.json` | in repo |
| `pilot_haiku55_computational` | `pilot_haiku55_computational_summary.json` | in repo |
| `pilot_haiku55_low_computational` | `pilot_haiku55_low_computational_summary.json` | in repo |
| `pilot_opus55_medical` | `pilot_opus55_medical_summary.json` | release [`runs-2026-10-21`](https://github.com/shumow/viral-politeness/releases/tag/runs-2026-10-21), `pilot_opus55_medical.jsonl.gz` (1.2 MB uncompressed) |
| `main_opus55_computational` | `main_opus55_computational_summary.json` | release [`runs-2026-10-21`](https://github.com/shumow/viral-politeness/releases/tag/runs-2026-10-21), `main_opus55_computational.jsonl.gz` (5.5 MB uncompressed) |

SHA-256 of the uncompressed release files:

    94f5b1a6e701880d0c756676068b4276fd6b506d06a4b21a53fd49f511c5ffee  main_opus55_computational.jsonl
    5facd17caf936bb3763249435011eb2dc272ccc4942a10fd5ec909818927aa58  pilot_opus55_medical.jsonl

To reproduce a summary from a release file:

```bash
curl -sSL -o data/runs/main_opus55_computational.jsonl.gz \
  https://github.com/shumow/viral-politeness/releases/download/runs-2026-10-21/main_opus55_computational.jsonl.gz
gunzip data/runs/main_opus55_computational.jsonl.gz
sha256sum -c <(echo "94f5b1a6e701880d0c756676068b4276fd6b506d06a4b21a53fd49f511c5ffee  data/runs/main_opus55_computational.jsonl")
python -m vp.analysis data/runs/main_opus55_computational.jsonl
```

The three hand-reviewed records in the main grid carry `hand_review`,
`cave_as_judged` and `second_class_as_judged`; `experiments/rescore.py` leaves them
unchanged.
