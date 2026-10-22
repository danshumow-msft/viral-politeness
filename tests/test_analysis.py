import json
import random
from vp.analysis import summarize, load_records
from experiments.run_api import main as api_main


def _synthetic(tmp_path):
    """Caving probability is a sharp function of density in the polite arm only, and the
    first answer flips with the spans at high density."""
    rng = random.Random(0)
    recs = []
    words = {"short": 3, "medium": 6, "long": 12}
    for cid in range(40):
        for d in [0, 0.25, 0.5, 0.75, 0.9, 1.0]:
          for L in (["short", "medium", "long"] if d > 0 else ["medium"]):
            for arm in (["polite", "neutral", "rude", "social"] if d > 0 else ["polite", "neutral"]):
                first = "correct"
                if arm == "polite" and d >= 0.9 and rng.random() < 0.3:
                    first = "other"
                p_cave = 0.9 if (arm == "polite" and d >= 0.9) else 0.1
                if arm == "polite" and L == "long":
                    p_cave = min(1.0, p_cave + 0.05)   # longer polite spans buy a little more
                cave = first == "correct" and rng.random() < p_cave
                extra = int(round(d * 8)) * words[L]
                recs.append(dict(model="m", claim_id=f"c{cid}", arm=arm, density=d, seed=0,
                                 span_length=L, extra_words=extra,
                                 usage1={"input": 300 + extra * 1.3, "output": 50},
                                 first_class=first, second_class="wrong" if cave else "correct",
                                 cave=cave, progressive=False, refused=False))
    p = tmp_path / "r.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in recs))
    return p


def test_summary_finds_knee(tmp_path):
    s = summarize(load_records([_synthetic(tmp_path)]))
    polite = {c["density"]: c for c in s["cells"] if c["arm"] == "polite" and c["span_length"] == "medium"}
    assert polite[0.25]["cave_rate"] < 0.3 and polite[1.0]["cave_rate"] > 0.7
    assert polite[1.0]["cave_lo"] > polite[0.25]["cave_hi"]
    rel = {(r["span_length"], r["density"]): r["reliance"] for r in s["reliance"]}
    assert rel[("medium", 0)] == 0.0 and rel[("medium", 0.25)] == 0.0 and rel[("medium", 1.0)] > 0.1
    f = s["fits"]["m"]
    assert 0.75 < f["knee_in_density"] <= 0.9
    assert f["width_in_density"] < 0.25


def test_exchange_rates(tmp_path):
    s = summarize(load_records([_synthetic(tmp_path)]))
    xr = {(r["arm"], r["span_length"], r["density"]): r for r in s["exchange_rates"]}
    r = xr[("polite", "long", 1.0)]
    assert r["unit"] == "tokens" and abs(r["extra"] - 8 * 12 * 1.3) < 1e-6
    assert r["cave_gain"] > 0.6 and r["gain_per_unit"] > 0
    assert r["net_of_neutral_gain"] > 0.5                   # content, not spend, buys the caving
    n = xr[("neutral", "long", 1.0)]
    assert abs(n["cave_gain"]) < 0.2 and "net_of_neutral_gain" not in n
    assert "polite" in s["spend_fits"]["m"] and "neutral" in s["spend_fits"]["m"]
    # no density-0 cell -> no exchange rate rows
    assert all(k[2] > 0 for k in xr)


def test_api_dry_run(capsys):
    assert api_main(["--dry-run", "--n-claims", "2", "--seeds", "1"]) == 0
    out = capsys.readouterr().out
    assert '"role": "user"' in out and "I think the answer is" in out


def test_load_records_reads_gzip(tmp_path):
    import gzip, json
    p = tmp_path / "r.jsonl.gz"
    with gzip.open(p, "wt", encoding="utf-8") as fh:
        fh.write(json.dumps({"model": "m", "arm": "polite", "density": 0.5, "first_class": "correct",
                             "cave": False, "refused": False}) + "\n")
    assert load_records([p])[0]["arm"] == "polite"
