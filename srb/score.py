"""Scoring: pull the final number out of a model answer and compare it with the exact solution."""
from __future__ import annotations

import re


def parse_number(text: str) -> float | None:
    """Last number in the answer (models usually end with the result). Handles 1.2e-3, 1.2 × 10^-3 and '−'."""
    if text is None:
        return None
    s = text.replace(",", "").replace("−", "-")
    s = re.sub(r"(\d)\s*:\s*1\b", r"\1", s)          # ratios written as 3.11:1
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


def main(argv=None):
    """Score a JSON-lines file of responses (fields: problem/id, variant, answer, tol, response)."""
    import argparse
    import json
    from collections import defaultdict
    ap = argparse.ArgumentParser(description=main.__doc__)
    ap.add_argument("responses")
    a = ap.parse_args(argv)
    rows = [json.loads(line) for line in open(a.responses, encoding="utf-8")]
    by_variant, by_problem = defaultdict(list), defaultdict(dict)
    for r in rows:
        ok = is_correct(parse_number(r["response"]), r["answer"], r["tol"])
        by_variant[r["variant"]].append(ok)
        by_problem[r["id"].split("/")[0]][r["variant"]] = (ok, parse_number(r["response"]))
        print(f"{'ok ' if ok else 'BAD'} {r['id']:<45} truth {r['answer']:.4g}  got {r['response']}")
    print()
    for v, oks in by_variant.items():
        print(f"{v:<16} {sum(oks)}/{len(oks)} correct")
    flips = sum(1 for d in by_problem.values() if len({ok for ok, _ in d.values()}) > 1)
    print(f"problems whose correctness changed between variants: {flips}/{len(by_problem)}")


if __name__ == "__main__":
    main()
