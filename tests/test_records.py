import copy

import pytest

from vp.records import completed_trials, trial_identity, validate_records


def _rec(**kw):
    r = dict(model="m", claim_id="c", arm="polite", density=0.5, seed=0)
    r.update(kw)
    return r


def test_identity_normalizes_legacy_length_and_numeric_density():
    assert trial_identity(_rec(density=0)) == trial_identity(_rec(density=0.0, span_length="medium"))
    with pytest.raises(ValueError, match="duplicate"):
        validate_records([_rec(), _rec(span_length="medium")])


@pytest.mark.parametrize("changes,field", [
    ({"model": ""}, "model"), ({"claim_id": None}, "claim_id"), ({"arm": []}, "arm"),
    ({"density": True}, "density"), ({"density": float("nan")}, "density"),
    ({"density": 2}, "density"), ({"seed": True}, "seed"),
    ({"seed": None}, "seed"), ({"seed": -1}, "seed"), ({"span_length": None}, "span_length"),
])
def test_invalid_identity_is_explicit(changes, field):
    with pytest.raises(ValueError, match=field):
        validate_records([_rec(**changes)])


@pytest.mark.parametrize("field,a,b", [
    ("effort", "low", "medium"), ("n_turns", 4, 8),
    ("protocol_version", 1, 2), ("scorer_version", "v1", "v2"),
    ("max_tokens", 64, 128), ("judge_model", None, "judge"),
    ("protocol", {"version": 1, "sampling": "greedy"}, {"version": 1, "sampling": "default"}),
    ("scoring_protocol", {"version": 1, "judge_model": "a"}, {"version": 1, "judge_model": "b"}),
])
def test_incompatible_models_are_not_pooled_across_disjoint_claims(field, a, b):
    with pytest.raises(ValueError, match=field):
        validate_records([_rec(**{field: a}), _rec(claim_id="d", **{field: b})])


def test_missing_metadata_is_reported_but_not_invented():
    r = _rec()
    original = copy.deepcopy(r)
    profiles = validate_records([r])
    assert set(profiles["m"]["unverified_fields"]) == {
        "protocol", "scoring_protocol", "n_turns", "served_model",
    }
    assert r == original
    with pytest.raises(ValueError, match="n_turns"):
        validate_records([r, _rec(claim_id="d", n_turns=8)])


@pytest.mark.parametrize("field", ["correct_answer", "wrong_answer"])
def test_conflicting_claim_references_are_rejected(field):
    with pytest.raises(ValueError, match=field):
        validate_records([_rec(**{field: "7"}), _rec(arm="neutral", **{field: "8"})])


def test_different_models_can_have_different_settings():
    assert len(validate_records([_rec(effort="low"), _rec(model="other", effort="medium")])) == 2


def test_served_model_change_between_calls_is_rejected():
    with pytest.raises(ValueError, match="served_model"):
        validate_records([_rec(served_model="a", served_model2="b")])


def test_layout_checks_also_cover_non_reliance_control_arms():
    with pytest.raises(ValueError, match="span_positions"):
        validate_records([_rec(span_positions=[0, 2]), _rec(arm="rude", span_positions=[1, 3])])


def test_resume_requires_recorded_compatible_generation_and_scoring():
    protocol, scoring = {"version": 1, "max_tokens": 64}, {"version": 1, "judge_model": None}
    r = _rec(protocol=protocol, scoring_protocol=scoring)
    assert completed_trials([r], "m", protocol, scoring) == {trial_identity(r)}
    assert completed_trials([], "m", protocol, scoring) == set()
    with pytest.raises(ValueError, match="protocol"):
        completed_trials([_rec()], "m", protocol, scoring)
    with pytest.raises(ValueError, match="scoring_protocol"):
        completed_trials([r], "m", protocol, dict(scoring, judge_model="judge"))
    with pytest.raises(ValueError, match="another model"):
        completed_trials([r], "different", protocol, scoring)
