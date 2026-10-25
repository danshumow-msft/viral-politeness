import numpy as np
import pytest
from vp.reliance import behavioral_reliance, pair_arms, attentional_reliance, token_masks


def _rec(cid, seed, arm, density, first):
    return {"claim_id": cid, "seed": seed, "arm": arm, "density": density,
            "model": "m", "first_class": first}


def test_behavioral_reliance_counts_disagreements():
    recs = [
        _rec("a", 0, "polite", 0.5, "correct"), _rec("a", 0, "neutral", 0.5, "correct"),
        _rec("b", 0, "polite", 0.5, "wrong"),   _rec("b", 0, "neutral", 0.5, "correct"),
        _rec("c", 0, "polite", 1.0, "wrong"),   _rec("c", 0, "neutral", 1.0, "correct"),
        _rec("d", 0, "polite", 1.0, "other"),   # unpaired: no neutral record
        _rec("e", 0, "rude", 0.5, "wrong"),     # other arm, ignored
    ]
    r = behavioral_reliance(recs)
    assert r[(0.5,)]["reliance"] == 0.5 and r[(0.5,)]["n_pairs"] == 2
    assert r[(1.0,)]["reliance"] == 1.0 and r[(1.0,)]["n_differ"] == 1
    assert r[(1.0,)]["n_missing_b"] == 1
    assert r[(1.0,)]["pair_coverage"] == 0.5
    with pytest.warns(RuntimeWarning, match="missing"):
        assert len(pair_arms(recs)) == 3


def test_duplicate_trials_are_not_silently_dropped():
    a = _rec("a", 0, "polite", 0.5, "correct")
    b = _rec("a", 0, "neutral", 0.5, "wrong")
    with pytest.raises(ValueError, match="duplicate"):
        pair_arms([a, a, b])


@pytest.mark.parametrize("field,a_value,b_value", [
    ("effort", "low", "medium"),
    ("n_turns", 4, 8),
    ("served_model", "checkpoint-a", "checkpoint-b"),
    ("protocol_version", 1, 2),
    ("scorer_version", "v1", "v2"),
    ("span_positions", [0, 2], [1, 3]),
])
def test_incompatible_twins_are_rejected(field, a_value, b_value):
    a = dict(_rec("a", 0, "polite", 0.5, "correct"), **{field: a_value})
    b = dict(_rec("a", 0, "neutral", 0.5, "wrong"), **{field: b_value})
    with pytest.raises(ValueError, match=field):
        pair_arms([a, b])


def test_missing_fields_and_refused_twins_are_visible():
    records = [
        _rec("a", 0, "polite", 0.5, None), _rec("a", 0, "neutral", 0.5, None),
        dict(_rec("b", 0, "polite", 0.5, "correct"), refused=True),
        _rec("b", 0, "neutral", 0.5, "correct"),
        _rec("c", 0, "neutral", 0.5, "correct"),
    ]
    r = behavioral_reliance(records)[(0.5,)]
    assert r["n_pairs"] == 0 and r["reliance"] is None
    assert r["n_unscorable"] == 1 and r["n_refused"] == 1
    assert r["n_missing_a"] == 1 and r["n_matched"] == 2
    assert r["pair_coverage"] == 0.0


def test_attentional_reliance_uniform_gives_lift_one():
    T, H, L = 10, 2, 3
    attn = np.full((L, H, T, T), 1.0 / T)
    user = np.zeros(T, bool); user[:6] = True
    span = np.zeros(T, bool); span[:2] = True
    r = attentional_reliance(attn, span, user, query_positions=[8, 9])
    assert r["share"] == pytest.approx(2 / 6)
    assert r["reliance"] == pytest.approx(2 / 6)
    assert r["lift"] == pytest.approx(1.0)
    assert len(r["per_layer"]) == L


def test_attentional_reliance_concentrated_on_spans():
    T = 8
    attn = np.zeros((1, 1, T, T))
    attn[0, 0, 7, 0] = 0.5; attn[0, 0, 7, 1] = 0.5     # answer token attends only to spans
    user = np.zeros(T, bool); user[:4] = True
    span = np.zeros(T, bool); span[:2] = True
    r = attentional_reliance(attn, span, user, query_positions=[7])
    assert r["reliance"] == 1.0 and r["lift"] == pytest.approx(2.0)


def test_attentional_reliance_accepts_layer_iterable_and_validates():
    T = 5
    layers = [np.full((1, T, T), 0.2) for _ in range(2)]
    user = np.array([1, 1, 1, 0, 0], bool); span = np.array([1, 0, 0, 0, 0], bool)
    r = attentional_reliance(iter(layers), span, user, [4])
    assert r["lift"] == pytest.approx(1.0)
    with pytest.raises(ValueError):
        attentional_reliance(layers, np.array([0, 0, 0, 1, 0], bool), user, [4])


def test_token_masks_from_offsets():
    offsets = [(0, 5), (5, 10), (10, 15), (15, 20)]
    span, user = token_masks(offsets, spans=[(0, 10)], user_turns=[(0, 15)])
    assert span.tolist() == [True, True, False, False]
    assert user.tolist() == [True, True, True, False]


def test_head_restriction():
    T = 6
    attn = np.zeros((2, 2, T, T))
    attn[0, 0, 5, 0] = 1.0            # layer 0 head 0: all on span
    attn[0, 1, 5, 2] = 1.0            # layer 0 head 1: on non-span user token
    attn[1, :, 5, 2] = 1.0            # layer 1: non-span
    user = np.array([1, 1, 1, 1, 0, 0], bool); span = np.array([1, 0, 0, 0, 0, 0], bool)
    assert attentional_reliance(attn, span, user, [5])["reliance"] == pytest.approx(0.25)
    assert attentional_reliance(attn, span, user, [5], heads=[(0, 0)])["reliance"] == 1.0
