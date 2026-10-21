from vp.claims import load_claims
from vp.contexts import (ARMS, SPANS, FILLER, build_context, matched_control,
                         word_alignment, rebuttal_text)


def _claim():
    return load_claims("syceval_computational", n=1, seed=3)[0]


def test_phrase_lists_are_word_aligned():
    assert word_alignment() == []
    assert len({len(v) for v in SPANS.values()}) == 1


def test_density_sets_span_count():
    c = _claim()
    for d, k in [(0.0, 0), (0.1, 1), (0.25, 2), (0.5, 4), (0.75, 6), (0.9, 7), (1.0, 8)]:
        t = build_context(c, "polite", d, seed=5)
        assert t.n_spans == k == len(t.spans)
        assert len(t.messages) == 2 * 8 + 1
        assert t.messages[-1]["role"] == "user" and c.question in t.messages[-1]["content"]


def test_arms_share_layout_and_differ_only_in_span_text():
    c = _claim()
    base = build_context(c, "polite", 0.5, seed=11)
    for arm in ARMS:
        t = matched_control(base, c, arm)
        if arm == base.arm:
            assert t.messages == base.messages
            continue
        assert t.span_positions == base.span_positions
        assert t.phrase_indices == base.phrase_indices
        for i, (m_a, m_b) in enumerate(zip(base.messages, t.messages)):
            if m_a["role"] == "assistant" or i // 2 not in base.span_positions:
                assert m_a == m_b
            else:
                assert m_a != m_b
                # the filler question after the span is the same
                j = base.span_positions.index(i // 2)
                sa, sb = base.spans[j], t.spans[j]
                assert m_a["content"].startswith(sa + " ") and m_b["content"].startswith(sb + " ")
                assert m_a["content"][len(sa):] == m_b["content"][len(sb):]


def test_seed_changes_layout_but_is_reproducible():
    c = _claim()
    a = build_context(c, "polite", 0.5, seed=1)
    b = build_context(c, "polite", 0.5, seed=1)
    d = build_context(c, "polite", 0.5, seed=2)
    assert a.messages == b.messages
    assert a.span_positions != d.span_positions or a.phrase_indices != d.phrase_indices


def test_spans_only_in_prior_user_turns():
    c = _claim()
    t = build_context(c, "rude", 1.0, seed=0)
    all_spans = {s for v in SPANS.values() for s in v}
    for m in t.messages[:-1]:
        if m["role"] == "assistant":
            assert not any(s in m["content"] for s in all_spans)
    assert not any(s in t.messages[-1]["content"] for s in all_spans)


def test_filler_has_no_task_overlap():
    for q, _ in FILLER:
        assert "polynomial" not in q.lower() and "symptom" not in q.lower()


def test_rebuttal():
    r = rebuttal_text("42", "Do not show work; just give the final answer.")
    assert r.startswith("I think the answer is 42.") and r.endswith("final answer.")
