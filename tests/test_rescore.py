from experiments.rescore import rescore_record
from experiments.run_api import Runner


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
