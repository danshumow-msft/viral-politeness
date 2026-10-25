import copy
import hashlib
import json

import pytest

from vp.audit import CASE_FIELDS, main as audit_main, prepare_audit
from vp.io import read_jsonl, write_jsonl


def _record(cid, first="correct", second="correct", **kw):
    r = dict(model="m", claim_id=cid, arm="polite", density=0.5, seed=0,
             question=f"Question {cid}?", correct_answer="7", wrong_answer="5",
             first_class=first, second_class=second, first_text="7", second_text="7",
             first_stop="end_turn", second_stop="end_turn",
             rebuttal_target="correct" if first == "wrong" else "wrong", refused=False,
             cave=first == "correct" and second == "wrong",
             progressive=first == "wrong" and second == "correct")
    r.update(kw)
    return r


def _frame():
    return [
        *[_record(f"n{i}") for i in range(10)],
        _record("p", second="wrong", second_text="5"),
        _record("h", hand_review="prior review", cave_as_judged=True),
        _record("u", first="other", second="other", second_text="Uncertain."),
        _record("r", refused=True, first_text=None, second_text=None, first_stop="refusal"),
        _record("o", first="wrong", second="correct"),
    ]


def test_selection_censuses_exceptions_and_records_sampling_probabilities():
    records = _frame()
    original = copy.deepcopy(records)
    b = prepare_audit(records, {}, negative_sample_size=4, seed=7, blinding_seed=11)
    m = b["manifest"]
    assert len(b["cases"]) == 9 and m["source_record_count"] == 15
    assert m["strata"]["accepted_negative"]["population"] == 10
    assert m["strata"]["accepted_negative"]["selected"] == 4
    for case in m["case_map"].values():
        assert case["inclusion_probability"] == (0.4 if case["stratum"] == "accepted_negative" else 1.0)
    assert {case["stratum"] for case in m["case_map"].values()} == {
        "accepted_negative", "positive", "hand_review", "unscorable", "refused", "other_scorable",
    }
    assert records == original
    assert m["status"] == m["acceptance"]["status"] == "pending_review"
    assert m["acceptance"]["required_independent_reviewers"] == 2


def test_reproducibility_does_not_depend_on_input_order_or_id_seed():
    records = _frame()
    a = prepare_audit(records, {}, negative_sample_size=4, seed=7, blinding_seed=11)
    b = prepare_audit(list(reversed(records)), {}, negative_sample_size=4, seed=7, blinding_seed=11)
    assert a == b
    c = prepare_audit(records, {}, negative_sample_size=4, seed=7, blinding_seed=12)
    assert set(a["manifest"]["case_map"]) != set(c["manifest"]["case_map"])
    assert sorted(v["trial_id"] for v in a["manifest"]["case_map"].values()) == sorted(
        v["trial_id"] for v in c["manifest"]["case_map"].values())


def test_reviewer_allowlist_contains_no_identity_or_previous_judgments():
    b = prepare_audit(_frame(), {}, negative_sample_size=4, blinding_seed=11)
    for case in b["cases"]:
        assert set(case) == set(CASE_FIELDS)
        assert len(case["case_id"]) == 32
        assert case["case_id"] not in {r["claim_id"] for r in _frame()}
    for template in b["review_template"]:
        assert template["first"] is template["second"] is template["reviewer_id"] is None
        assert "model" not in template and "prior_judgments" not in template
    assert any("hand_review" in c["prior_judgments"] for c in b["manifest"]["case_map"].values())


def test_text_is_preserved_not_redacted_to_make_a_stronger_blinding_claim():
    r = _record("c", second_text="I mention politeness and model identity in my own answer.")
    b = prepare_audit([r], {}, blinding_seed=11)
    assert b["cases"][0]["second_text"] == r["second_text"]


def test_question_reconstruction_is_explicit_and_missing_questions_fail():
    r = _record("c")
    del r["question"]
    with pytest.raises(ValueError, match="question"):
        prepare_audit([r], {}, blinding_seed=11)
    b = prepare_audit([r], {"c": "Reconstructed question?"}, blinding_seed=11)
    assert b["cases"][0]["question"] == "Reconstructed question?"
    assert next(iter(b["manifest"]["case_map"].values()))["question_source"] == "claim-bank reconstruction"


def test_an_unrecorded_actual_rebuttal_is_not_guessed_for_reviewers():
    r = _record("c")
    del r["rebuttal_target"]
    b = prepare_audit([r], {}, blinding_seed=11)
    assert b["cases"][0]["rebuttal_answer"] is None


def test_a_small_population_is_a_census_but_still_requires_reviews():
    b = prepare_audit([_record("c")], {}, negative_sample_size=400, blinding_seed=11)
    assert len(b["cases"]) == 1
    assert b["manifest"]["acceptance"]["planned_sample"] == 1
    assert b["manifest"]["acceptance"]["status"] == "pending_review"
    assert next(iter(b["manifest"]["case_map"].values()))["inclusion_probability"] == 1.0


@pytest.mark.parametrize("options", [
    {"negative_sample_size": 0}, {"negative_sample_size": True},
    {"seed": -1}, {"blinding_seed": -1}, {"confidence": 1}, {"max_miss_fraction": 95},
])
def test_invalid_audit_design_is_rejected(options):
    with pytest.raises(ValueError):
        prepare_audit([_record("c")], {}, **options)


def test_duplicate_or_incompatible_sources_fail_before_sampling():
    r = _record("c")
    with pytest.raises(ValueError, match="duplicate"):
        prepare_audit([r, r], {})
    with pytest.raises(ValueError, match="effort"):
        prepare_audit([dict(r, effort="low"), _record("d", effort="medium")], {})


def test_cli_keeps_coordinator_data_separate_and_cannot_overwrite(tmp_path, capsys):
    source, out = tmp_path / "source.jsonl.gz", tmp_path / "audit"
    write_jsonl(source, _frame())
    original = source.read_bytes()
    assert audit_main([str(source), "--out", str(out), "--negative-sample-size", "2"]) == 0
    cases = read_jsonl(out / "reviewer" / "cases.jsonl")
    template = read_jsonl(out / "reviewer" / "reviews-template.jsonl")
    manifest = json.loads((out / "coordinator" / "manifest.json").read_text(encoding="utf-8"))
    assert len(cases) == len(template) == 7
    assert all(set(c) == set(CASE_FIELDS) for c in cases)
    assert manifest["source_records"]["sha256"] == hashlib.sha256(original).hexdigest()
    assert manifest["status"] == "pending_review"
    assert "Reviews and audit decisions are pending" in capsys.readouterr().out
    with pytest.raises(FileExistsError):
        audit_main([str(source), "--out", str(out)])
    assert source.read_bytes() == original
