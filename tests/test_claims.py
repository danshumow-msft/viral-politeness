from vp.claims import load_claims, iter_claims


def test_computational_bank_has_wrong_answers():
    claims = load_claims("syceval_computational")
    assert len(claims) == 200
    for c in claims:
        assert c.wrong_answers and all(w != c.correct_answer for w in c.wrong_answers)
        assert c.question and not c.question.endswith("!!!")


def test_full_bank_without_filter():
    assert len(list(iter_claims("syceval_computational", require_wrong=False))) == 500


def test_subset_is_stable():
    a = load_claims("syceval_computational", n=20, seed=1)
    b = load_claims("syceval_computational", n=20, seed=1)
    assert [c.id for c in a] == [c.id for c in b] and len(a) == 20
