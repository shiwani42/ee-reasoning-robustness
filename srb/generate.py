"""Generate problem instances and all their variants as JSON lines.

    python -m srb.generate --per-template 2 --seed 0 --out problems.jsonl
"""
from __future__ import annotations

import argparse
import json
import random
import sys

from .perturb import VARIANTS, build
from .problems import TEMPLATES


def generate(per_template: int, seed: int, variants=VARIANTS, templates=TEMPLATES):
    rng = random.Random(seed)
    for t in templates:
        for i in range(per_template):
            params = t.sample(rng)
            answer = t.solve(params)
            pid = f"{t.name}-{seed}-{i}"
            for v in variants:
                yield dict(id=f"{pid}/{v}", problem=pid, template=t.name, topic=t.topic, variant=v,
                           prompt=build(t, params, v, random.Random(f"{pid}/{v}")),
                           answer=answer, unit=t.answer_unit, tol=t.tol, params=params)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--per-template", type=int, default=2)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--variants", nargs="*", default=VARIANTS, choices=VARIANTS)
    ap.add_argument("--out", default="-")
    a = ap.parse_args(argv)
    f = sys.stdout if a.out == "-" else open(a.out, "w", encoding="utf-8")
    n = 0
    for row in generate(a.per_template, a.seed, a.variants):
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
        n += 1
    if f is not sys.stdout:
        f.close()
        print(f"wrote {n} prompts to {a.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
