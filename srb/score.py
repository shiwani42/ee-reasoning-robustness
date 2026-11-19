"""Scoring: pull the final number out of a model answer and compare it with the exact solution."""
from __future__ import annotations

import re


def parse_number(text: str) -> float | None:
    """Last number in the answer (models usually end with the result). Handles 1.2e-3, 1.2 × 10^-3 and '−'."""
    if text is None:
        return None
    s = text.replace(",", "").replace("−", "-")
    m = list(re.finditer(r"[-+]?\d+(?:\.\d+)?(?:\s*(?:[eE]|[×x]\s*10\^?)\s*[-+]?\d+)?", s))
    if not m:
        return None
    tok = m[-1].group(0).replace(" ", "")
    tok = re.sub(r"[×x]10\^?", "e", tok)
    try:
        return float(tok)
    except ValueError:
        return None


def is_correct(value: float | None, truth: float, tol: str) -> bool:
    if value is None:
        return False
    if tol == "db":
        return abs(value - truth) <= 0.2
    return abs(value - truth) <= 0.02 * abs(truth)
