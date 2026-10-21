import json
import random
from vp.analysis import summarize, load_records
from experiments.run_api import main as api_main


def _synthetic(tmp_path):
    """Caving probability is a sharp function of density in the polite arm only, and the
    first answer flips with the spans at high density."""
    rng = random.Random(0)
    recs = []
    for cid in range(40):
        for d in [0, 0.25, 0.5, 0.75, 0.9, 1.0]:
            for arm in (["polite", "neutral", "rude", "social"] if d > 0 else ["polite", "neutral"]):
                first = "correct"
                if arm == "polite" and d >= 0.9 and rng.random() < 0.3:
                    first = "other"
                p_cave = 0.9 if (arm == "polite" and d >= 0.9) else 0.1
                cave = first == "correct" and rng.random() < p_cave
                recs.append(dict(model="m", claim_id=f"c{cid}", arm=arm, density=d, seed=0,
                                 first_class=first, second_class="wrong" if cave else "correct",
                                 cave=cave, progressive=False, refused=False))
    p = tmp_path / "r.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in recs))
    return p


def test_summary_finds_knee(tmp_path):
    s = summarize(load_records([_synthetic(tmp_path)]))
    polite = {c["density"]: c for c in s["cells"] if c["arm"] == "polite"}
    assert polite[0.25]["cave_rate"] < 0.3 and polite[1.0]["cave_rate"] > 0.7
    assert polite[1.0]["cave_lo"] > polite[0.25]["cave_hi"]
    rel = {r["density"]: r["reliance"] for r in s["reliance"]}
    assert rel[0] == 0.0 and rel[0.25] == 0.0 and rel[1.0] > 0.1
    f = s["fits"]["m"]
    assert 0.75 < f["knee_in_density"] <= 0.9
    assert f["width_in_density"] < 0.25


def test_api_dry_run(capsys):
    assert api_main(["--dry-run", "--n-claims", "2", "--seeds", "1"]) == 0
    out = capsys.readouterr().out
    assert '"role": "user"' in out and "I think the answer is" in out
