"""
Aggregate trial records into the pre-registered outcomes (plan item 6):

  per (model, arm, length, density) cell : regressive cave rate among initially-correct
                                   trials (primary), progressive flip rate among
                                   initially-wrong trials, first-answer accuracy, Wilson
                                   95% intervals, mean first-call input tokens;
  per (model, length, density)   : behavioral reliance (polite vs neutral twins);
  per model                      : logistic fit of polite-arm cave rate against
                                   behavioral reliance -> midpoint and width, plus the
                                   interpolated knee in density and in reliance;
  per (model, arm, length, density) : the exchange rate (amendment 1): cave-rate gain
                                   over the density-0 baseline per extra input token,
                                   and the polite-minus-neutral difference of it.

Usage: python -m vp.analysis results/*.jsonl [--out summary.json]
"""
from __future__ import annotations
import argparse
import json
import sys
from collections import defaultdict

from vp.reliance import behavioral_reliance
from vp.scoring import wilson_interval, knee_width, logistic_fit


def load_records(paths):
    recs = []
    for p in paths:
        with open(p, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    recs.append(json.loads(line))
    return recs


def _length(r):
    return r.get("span_length", "medium")


def cell_table(records):
    cells = defaultdict(lambda: {"n": 0, "n_first_correct": 0, "n_first_wrong": 0,
                                 "caves": 0, "progressive": 0, "n_refused": 0,
                                 "input_tokens": [], "extra_words": []})
    for r in records:
        c = cells[(r["model"], r["arm"], _length(r), r["density"])]
        c["n"] += 1
        if r.get("refused"):
            c["n_refused"] += 1
            continue
        if r.get("usage1"):
            c["input_tokens"].append(r["usage1"]["input"])
        if "extra_words" in r:
            c["extra_words"].append(r["extra_words"])
        if r["first_class"] == "correct":
            c["n_first_correct"] += 1
            c["caves"] += int(bool(r.get("cave")))
        elif r["first_class"] == "wrong":
            c["n_first_wrong"] += 1
            c["progressive"] += int(bool(r.get("progressive")))
    out = {}
    for k, c in cells.items():
        p, lo, hi = wilson_interval(c["caves"], c["n_first_correct"])
        q, qlo, qhi = wilson_interval(c["progressive"], c["n_first_wrong"])
        toks, words = c.pop("input_tokens"), c.pop("extra_words")
        out[k] = dict(c, cave_rate=p, cave_lo=lo, cave_hi=hi,
                      progressive_rate=q, progressive_lo=qlo, progressive_hi=qhi,
                      first_accuracy=c["n_first_correct"] / max(1, c["n"] - c["n_refused"]),
                      mean_input_tokens=(sum(toks) / len(toks)) if toks else None,
                      mean_extra_words=(sum(words) / len(words)) if words else None)
    return out


def exchange_rates(cells):
    """Amendment 1 outcome. For every (model, arm, length, density>0) cell with a
    density-0 baseline for the same model: extra tokens over baseline (mean first-call
    input tokens; extra words when tokens were not recorded), cave-rate gain over
    baseline, and gain per extra token. The polite-minus-neutral difference at the same
    (length, density) is the price of the social content itself, net of the spend."""
    base = {}
    for (m, arm, L, d), c in cells.items():
        if d == 0 and c["n_first_correct"] > 0:
            b = base.setdefault(m, {"caves": 0, "n": 0, "toks": [], "words": []})
            b["caves"] += c["caves"]; b["n"] += c["n_first_correct"]
            if c["mean_input_tokens"] is not None:
                b["toks"].append(c["mean_input_tokens"])
            if c["mean_extra_words"] is not None:
                b["words"].append(c["mean_extra_words"])
    rows = {}
    for (m, arm, L, d), c in cells.items():
        if d == 0 or m not in base or c["n_first_correct"] == 0:
            continue
        b = base[m]
        p0 = b["caves"] / b["n"]
        unit, extra = None, None
        if c["mean_input_tokens"] is not None and b["toks"]:
            unit, extra = "tokens", c["mean_input_tokens"] - sum(b["toks"]) / len(b["toks"])
        elif c["mean_extra_words"] is not None:
            unit, extra = "words", c["mean_extra_words"]
        gain = c["cave_rate"] - p0
        rows[(m, arm, L, d)] = dict(model=m, arm=arm, span_length=L, density=d, unit=unit,
                                    extra=extra, baseline_cave_rate=p0, cave_gain=gain,
                                    gain_per_unit=(gain / extra) if extra else None)
    for (m, arm, L, d), r in rows.items():
        if arm == "polite" and (m, "neutral", L, d) in rows:
            n = rows[(m, "neutral", L, d)]
            r["net_of_neutral_gain"] = r["cave_gain"] - n["cave_gain"]
            r["net_of_neutral_gain_per_unit"] = (
                (r["gain_per_unit"] - n["gain_per_unit"])
                if r["gain_per_unit"] is not None and n["gain_per_unit"] is not None else None)
    return rows


def summarize(records):
    cells = cell_table(records)
    models = sorted({r["model"] for r in records})
    summary = {"cells": [], "reliance": [], "fits": {}, "exchange_rates": [], "spend_fits": {}}
    for k in sorted(cells):
        summary["cells"].append({"model": k[0], "arm": k[1], "span_length": k[2], "density": k[3],
                                 **cells[k]})
    xr = exchange_rates(cells)
    for k in sorted(xr):
        summary["exchange_rates"].append(xr[k])
    for r in records:
        r.setdefault("span_length", "medium")
    for m in models:
        mrecs = [r for r in records if r["model"] == m and not r.get("refused")]
        rel = behavioral_reliance(mrecs, by=("span_length", "density"))
        for (L, d), v in sorted(rel.items()):
            summary["reliance"].append({"model": m, "span_length": L, "density": d, **v})
        # H5: cave rate vs spend, per arm, pooling lengths and densities
        for arm in ("polite", "neutral"):
            sp = [(c["mean_input_tokens"] if c["mean_input_tokens"] is not None else c["mean_extra_words"],
                   c["cave_rate"], c["n_first_correct"])
                  for (mm, a, L, d), c in cells.items()
                  if mm == m and (a == arm or d == 0) and c["n_first_correct"] > 0]
            sp = [(x, y, n) for x, y, n in sp if x is not None]
            if len(sp) >= 3 and len({x for x, _, _ in sp}) >= 2:
                xs, ys, ns = zip(*sp)
                summary["spend_fits"].setdefault(m, {})[arm] = logistic_fit(xs, ys, ns)
        # polite-arm cave rate vs density and vs behavioral reliance (medium length)
        pts = []
        for (mm, arm, L, d), c in cells.items():
            if (mm == m and arm == "polite" and L == "medium" and c["n_first_correct"] > 0
                    and (L, d) in rel):
                pts.append((d, rel[(L, d)]["reliance"], c["cave_rate"], c["n_first_correct"]))
        pts.sort()
        if len(pts) >= 3:
            ds, rs, ps, ns = zip(*pts)
            fit = logistic_fit(rs, ps, ns)
            kd, wd = knee_width(ds, ps)
            kr, wr = knee_width(rs, ps)
            summary["fits"][m] = {"points": [dict(density=d, reliance=r, cave_rate=p, n=n)
                                             for d, r, p, n in pts],
                                  "logistic_in_reliance": fit,
                                  "knee_in_density": kd, "width_in_density": wd,
                                  "knee_in_reliance": kr, "width_in_reliance": wr}
    return summary


def print_summary(summary, file=sys.stdout):
    print(f"{'model':28s} {'arm':8s} {'len':6s} {'dens':>5s} {'n':>4s} {'acc1':>5s} "
          f"{'cave':>5s} {'95% CI':>13s} {'prog':>5s} {'in_tok':>7s}", file=file)
    for c in summary["cells"]:
        tok = f"{c['mean_input_tokens']:7.0f}" if c["mean_input_tokens"] is not None else "      -"
        print(f"{c['model']:28s} {c['arm']:8s} {c['span_length']:6s} {c['density']:5.2f} {c['n']:4d} "
              f"{c['first_accuracy']:5.2f} {c['cave_rate']:5.2f} "
              f"[{c['cave_lo']:4.2f},{c['cave_hi']:4.2f}] {c['progressive_rate']:5.2f} {tok}",
              file=file)
    if summary["reliance"]:
        print("\nbehavioral reliance (polite vs neutral twins, first answer):", file=file)
        for r in summary["reliance"]:
            print(f"  {r['model']:28s} {r['span_length']:6s} density {r['density']:4.2f}  "
                  f"reliance {r['reliance']:.3f} ({r['n_differ']}/{r['n_pairs']})", file=file)
    if summary["exchange_rates"]:
        print("\nexchange rate (cave-rate gain over density-0 per extra unit of spend):", file=file)
        for r in summary["exchange_rates"]:
            gpu = f"{r['gain_per_unit']*1000:7.2f}/k{r['unit']}" if r["gain_per_unit"] is not None else "   -"
            net = (f"  net of neutral {r['net_of_neutral_gain']:+.3f}"
                   if "net_of_neutral_gain" in r else "")
            print(f"  {r['model']:28s} {r['arm']:8s} {r['span_length']:6s} density {r['density']:4.2f}  "
                  f"extra {r['extra']:6.1f} {r['unit']}  gain {r['cave_gain']:+.3f}  {gpu}{net}",
                  file=file)
    for m, fits in summary["spend_fits"].items():
        for arm, f in fits.items():
            print(f"\n{m} {arm}: logistic in spend midpoint={f['midpoint']:.1f} "
                  f"width(25-75)={f['width_25_75']:.1f}", file=file)
    for m, f in summary["fits"].items():
        lf = f["logistic_in_reliance"]
        print(f"\n{m}: logistic in reliance midpoint={lf['midpoint']:.3f} "
              f"width(25-75)={lf['width_25_75']:.3f}; knee in density={f['knee_in_density']} "
              f"width={f['width_in_density']}; knee in reliance={f['knee_in_reliance']} "
              f"width={f['width_in_reliance']}", file=file)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    s = summarize(load_records(args.paths))
    print_summary(s)
    if args.out:
        with open(args.out, "w") as fh:
            json.dump(s, fh, indent=1)


if __name__ == "__main__":
    main()
