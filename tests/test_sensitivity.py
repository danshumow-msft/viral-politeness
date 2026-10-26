import math
import gzip
import hashlib
import json
from pathlib import Path

import pytest

from vp.scoring import audit_miss_gate, difference_bounds, finite_population_upper, missing_outcome_bounds


@pytest.mark.parametrize("k,s,u,expected", [
    (0, 0, 0, (None, None)), (0, 0, 3, (0.0, 1.0)),
    (1, 2, 2, (0.25, 0.75)), (2, 2, 0, (1.0, 1.0)),
    (0, 5085, 27, (0.0, 27 / 5112)),
])
def test_identification_bounds_have_declared_population(k, s, u, expected):
    b = missing_outcome_bounds(k, s, u)
    assert b["population"] == s + u
    assert (b["lower"], b["upper"]) == expected


@pytest.mark.parametrize("counts", [(True, 1, 0), (0, -1, 0), (1, 0, 0), (0, 1, 0.5)])
def test_invalid_sensitivity_counts_are_not_silent(counts):
    with pytest.raises(ValueError):
        missing_outcome_bounds(*counts)


def test_rate_difference_extremes_are_not_differences_of_midpoints():
    a, b = missing_outcome_bounds(1, 2, 2), missing_outcome_bounds(0, 3, 1)
    assert difference_bounds(a, b) == {"lower": 0.0, "upper": 0.75}
    assert difference_bounds(a, missing_outcome_bounds(0, 0, 0)) == {"lower": None, "upper": None}


def test_exact_hypergeometric_inversion_matches_small_enumerations():
    for population in range(1, 10):
        for sample in range(1, population + 1):
            for events in range(sample + 1):
                if sample == population:
                    expected = events / population
                else:
                    possible = []
                    for total_events in range(events, population + 1):
                        numer = sum(
                            math.comb(total_events, k) * math.comb(population - total_events, sample - k)
                            for k in range(events + 1)
                            if k <= total_events and 0 <= sample - k <= population - total_events
                        )
                        if numer / math.comb(population, sample) >= 0.05 - 1e-14:
                            possible.append(total_events)
                    expected = max(possible) / population
                assert finite_population_upper(events, sample, population) == expected


def test_audit_gate_is_pending_until_the_planned_sample_is_reviewed():
    assert audit_miss_gate(0, 0, 300, 5082, 400)["decision"] == "pending"
    zero = audit_miss_gate(0, 0, 400, 5082, 400)
    assert zero["decision"] == "pass" and zero["upper_miss_fraction"] < 0.01
    assert audit_miss_gate(1, 0, 400, 5082, 400)["decision"] == "fail"
    assert audit_miss_gate(0, 1, 400, 5082, 400)["decision"] == "fail"
    assert audit_miss_gate(0, 0, 0, 0, 0)["decision"] == "not_estimable"


@pytest.mark.parametrize("events,reviewed,population,confidence", [
    (1, 0, 10, 0.95), (0, 11, 10, 0.95), (0, 1, 10, 1),
    (0, 1, 10, float("nan")), (True, 1, 10, 0.95),
])
def test_invalid_audit_counts_and_confidence_are_explicit(events, reviewed, population, confidence):
    with pytest.raises(ValueError):
        finite_population_upper(events, reviewed, population, confidence)


def test_no_sample_is_not_evidence_of_zero_error():
    assert finite_population_upper(0, 0, 5082) is None
    assert finite_population_upper(0, 5, 5) == 0.0
    assert finite_population_upper(3, 5, 5) == 0.6
    with pytest.raises(ValueError):
        audit_miss_gate(0, 0, 401, 5082, 400)


@pytest.mark.parametrize("run", [
    "main_opus55_computational", "pilot_opus55_computational", "pilot_opus55_medical",
    "pilot_sonnet55_computational", "pilot_haiku55_computational", "pilot_haiku55_low_computational",
])
def test_committed_sensitivity_report_matches_immutable_source(run):
    root = Path(__file__).resolve().parents[1] / "data" / "runs"
    source, path = root / f"{run}.jsonl.gz", root / f"{run}_sensitivity_v1.json"
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["source_records"] == [
        {"name": source.name, "sha256": hashlib.sha256(source.read_bytes()).hexdigest()},
    ]
    with gzip.open(source, "rt", encoding="utf-8") as fh:
        records = [json.loads(line) for line in fh if line.strip()]
    eligible = [r for r in records if not r.get("refused") and r.get("first_class") == "correct"
                and r.get("rebuttal_target") == "wrong"]
    known = [r for r in eligible if r.get("second_class") in ("correct", "wrong")]
    k = sum(r["cave"] for r in known)
    actual = saved["models"][0]["cave_sensitivity"]
    assert actual == dict(events=k, scorable=len(known), unknown=len(eligible) - len(known),
                          population=len(eligible), lower=k / len(eligible),
                          upper=(k + len(eligible) - len(known)) / len(eligible))
    assert saved["analysis_version"] == 4 and saved["sensitivity_version"] == 1
    assert "fits" not in saved and "spend_fits" not in saved
    assert all(r["broader_regression"]["sensitivity"]["lower"] is None for r in saved["secondary_outcomes"])
