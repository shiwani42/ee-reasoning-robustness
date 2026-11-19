"""Solver checks against hand calculations and a textbook example."""
import math
import random

import pytest

from srb import problems as P
from srb.generate import generate
from srb.perturb import VARIANTS
from srb.score import is_correct, parse_number


def approx(a, b, rel=1e-3):
    return abs(a - b) <= rel * abs(b)


def test_load_line():
    p = dict(vdd=28, vk=4, imax=1.0)
    assert approx(P.LOAD_LINE_ROPT.solve(p), 48.0)       # 2(28 - 4)/1
    assert approx(P.LOAD_LINE_POUT.solve(p), 6.0)        # 24 * 1 / 4


def test_efficiency_limits():
    assert approx(P.EFFICIENCY_ANGLE.solve(dict(alpha=360)), 50.0)          # class A
    assert approx(P.EFFICIENCY_ANGLE.solve(dict(alpha=180)), 100 * math.pi / 4)  # class B


def test_dbm_and_pae():
    assert approx(P.DBM.solve(dict(p=2.0)), 33.0103)
    assert approx(P.PAE.solve(dict(pout=10, pin=0.5, pdc=20)), 47.5)


def test_stability_pozar():
    # Pozar, Microwave Engineering: S11 0.894∠-60.6°, S21 3.122∠123.6°, S12 0.020∠62.4°, S22 0.781∠-27.6° -> K = 0.607
    p = dict(s11=(0.894, -60.6), s21=(3.122, 123.6), s12=(0.020, 62.4), s22=(0.781, -27.6))
    assert abs(P.STABILITY_K.solve(p) - 0.607) < 0.002
    assert approx(P.MSG.solve(p), 10 * math.log10(3.122 / 0.020))


def test_matching():
    assert approx(P.MISMATCH.solve(dict(g=0.5)), -10 * math.log10(0.75))
    assert approx(P.VSWR.solve(dict(r=100, x=0, z0=50)), 2.0)
    assert approx(P.QUARTER_WAVE.solve(dict(rs=12.5, rl=50, f=6)), 25.0)
    assert approx(P.L_SECTION.solve(dict(rl=12.5, rh=50, f=1.0)), 5.513)   # Q = sqrt(3), X_C = 28.87 ohm


def test_junction_temperature():
    p = dict(tc=85, rth=10, pdc=4.16, pin=0.046, pout=2.23)
    assert approx(P.JUNCTION_T.solve(p), 85 + 10 * (4.16 + 0.046 - 2.23))


def test_variants_keep_answer_and_differ():
    rows = list(generate(per_template=2, seed=1))
    assert len(rows) == len(P.TEMPLATES) * 2 * len(VARIANTS)
    by_problem = {}
    for r in rows:
        by_problem.setdefault(r["problem"], []).append(r)
    for prob, rs in by_problem.items():
        assert len({r["answer"] for r in rs}) == 1, prob
        base = next(r["prompt"] for r in rs if r["variant"] == "base")
        for r in rs:
            if r["variant"] != "base":
                assert r["prompt"] != base, (prob, r["variant"])


def test_wrong_hint_is_wrong():
    rng = random.Random(0)
    for t in P.TEMPLATES:
        for _ in range(20):
            p = t.sample(rng)
            assert not is_correct(t.wrong(p), t.solve(p), t.tol), t.name


@pytest.mark.parametrize("text,val", [("so P = 33.0 dBm", 33.0), ("K ≈ 0.61", 0.61), ("C = 5.5 pF.", 5.5),
                                      ("about 1.2 × 10^-3 W", 1.2e-3), ("−3.5 dB", -3.5), ("1,250 Ω", 1250.0), ("3.11:1", 3.11)])
def test_parse(text, val):
    assert approx(parse_number(text), val)
