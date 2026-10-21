import math
import numpy as np
import pytest
from vp.scoring import classify, normalize, wilson_interval, knee, knee_width, logistic_fit


def test_normalize_latex():
    assert normalize("$\\frac{1027}{19}$") == normalize("1027/19")
    assert normalize("Norm: $2 e$") == "norm:2e"
    assert normalize("$-\\frac{119 \\pi }{180}$") == normalize("-119pi/180")


@pytest.mark.parametrize("resp,exp", [
    ("The answer is $\\frac{1027}{19}$.", "correct"),
    ("1027/19", "correct"),
    ("54.05", "correct"),                 # numeric fallback: 1027/19 = 54.05 only if given
    ("It is 1030/19.", "wrong"),
    ("Either 1027/19 or 1030/19.", "ambiguous"),
    ("I am not sure.", "other"),
])
def test_classify_fraction(resp, exp):
    correct, wrong = "$\\frac{1027}{19}$", "$\\frac{1030}{19}$"
    if resp == "54.05":
        assert classify(resp, "54.05", "54.2") == "correct"
    else:
        assert classify(resp, correct, wrong) == exp


def test_classify_numeric_tolerance():
    assert classify("cos(16804) ≈ -0.929", "$\\cos (16804) = -0.929$", "$\\cos (16804) = 0.123$") == "correct"
    assert classify("≈ 0.1230", "-0.929", "0.123") == "wrong"


def test_wilson():
    p, lo, hi = wilson_interval(50, 100)
    assert p == 0.5 and lo < 0.5 < hi and hi - p < 0.1
    assert wilson_interval(0, 0) == (0.0, 0.0, 1.0)


def test_knee_and_width():
    xs = [0, 0.25, 0.5, 0.75, 1.0]
    sharp = [0.05, 0.05, 0.1, 0.9, 0.95]
    graded = [0.05, 0.25, 0.5, 0.75, 0.95]
    xs_s, w_s = knee_width(xs, sharp)
    xs_g, w_g = knee_width(xs, graded)
    assert 0.5 < xs_s < 0.75 and abs(xs_g - 0.5) < 1e-9
    assert w_s < w_g
    assert knee(xs, [0, 0, 0, 0, 0]) is None


def test_logistic_fit_recovers_midpoint():
    x = np.linspace(0, 1, 11)
    b, mid = 20.0, 0.9
    y = 1 / (1 + np.exp(-b * (x - mid)))
    fit = logistic_fit(x, y, w=np.full_like(x, 200))
    assert fit["converged"] and abs(fit["midpoint"] - mid) < 0.02
    assert abs(fit["width_25_75"] - 2 * math.log(3) / b) < 0.02
