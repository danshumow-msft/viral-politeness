from experiments.rescore import rescore_record
from experiments.run_api import Runner
import pytest

from experiments.rescore import main as rescore_main, scoring_provenance
from vp.annotations import source_fingerprint, validate_annotation, with_annotation
from vp.io import read_jsonl, write_jsonl


def _runner():
    return Runner(client=None, model=None, effort=None, max_tokens=0, judge_model=None)


def _rec(**kw):
    base = dict(claim_id="c", question="q", correct_answer="7", wrong_answer="5",
                rebuttal_target="wrong", first_text="7", first_class="correct",
                first_class_heuristic="correct", second_text="You are right, 5.",
                second_class="wrong", second_class_heuristic="wrong", cave=True)
    base.update(kw)
    return base


def test_rescore_recomputes_classes_and_keeps_v0():
    r = rescore_record(_runner(), _rec(second_text="No, it is 7, not 5.", second_class="wrong"))
    assert r["second_class_v0"] == "wrong" and r["second_class"] == "correct" and r["cave"] is False


def test_rescore_leaves_hand_reviewed_records_alone():
    rec = _rec(second_text="(7) is right; 5 fails.", second_class="correct", cave=False,
               second_class_as_judged="wrong", cave_as_judged=True,
               hand_review="reaffirmation in another form")
    out = rescore_record(_runner(), rec)
    assert out is rec and out["cave"] is False and out["second_class"] == "correct"


def test_rescore_skips_refused():
    rec = {"refused": True, "claim_id": "c"}
    assert rescore_record(_runner(), rec) is rec


def test_rescore_retains_independent_annotation_and_source_binding():
    rec = _rec(model="m", arm="polite", density=0.5, seed=0)
    annotation = dict(
        version=1, annotation_set="fixture-v1", source_sha256=source_fingerprint(rec),
        provenance=dict(method="fixture", annotator="test", rubric_version="secondary-v1",
                        created_at="2026-10-25T12:00:00Z", rationale="Synthetic independent annotation."),
        first=dict(status="scored", correctness="correct", target_commitment="not_mentioned",
                   uncertainty=False),
        second=dict(status="scored", correctness="incorrect", target_commitment="asserted",
                    uncertainty=False),
    )
    annotated = with_annotation(rec, annotation)
    out = rescore_record(_runner(), annotated)
    assert out["secondary_annotation"] == annotation
    validate_annotation(out)


def test_scoring_provenance_preserves_history_and_review():
    rec = _rec(hand_review="retained", scoring_protocol=dict(version=1, scorer_version="old"))
    protocol = _runner().scoring_protocol()
    out = scoring_provenance(rec, protocol)
    assert out["hand_review"] == rec["hand_review"]
    assert out["scoring_history"] == [rec["scoring_protocol"]]
    assert scoring_provenance(out, protocol) is out
    assert rec["scoring_protocol"]["scorer_version"] == "old"
    with pytest.raises(ValueError, match="scoring_history"):
        scoring_provenance(dict(rec, scoring_history={"old": True}), protocol)


def test_rescore_preflight_rejects_duplicates_before_judging(tmp_path):
    rec = _rec(model="m", arm="polite", density=0.5, seed=0)
    path = tmp_path / "duplicates.jsonl"
    write_jsonl(path, [rec, rec])
    with pytest.raises(ValueError, match="duplicate"):
        rescore_main([str(path)])


def test_rescore_cannot_overwrite_source(tmp_path):
    path = tmp_path / "r.jsonl"
    write_jsonl(path, [_rec()])
    original = path.read_bytes()
    with pytest.raises(ValueError, match="preserve the source"):
        rescore_main([str(path), "--out", str(path), "--judge", "none"])
    assert path.read_bytes() == original


def test_rescore_exports_configuration_even_when_hand_review_is_preserved(tmp_path):
    path = tmp_path / "reviewed.jsonl"
    rec = _rec(model="m", arm="polite", density=0.5, seed=0,
               second_class="correct", cave=False, hand_review="retained")
    write_jsonl(path, [rec])
    out = tmp_path / "derived.jsonl.gz"
    rescore_main([str(path), "--out", str(out), "--judge", "none"])
    result = read_jsonl(out)[0]
    assert result["scoring_protocol"] == _runner().scoring_protocol()
    assert result["scoring_history"] == [None]
    for field in ("hand_review", "first_class", "second_class", "cave"):
        assert result[field] == rec[field]
    assert read_jsonl(path) == [rec]
