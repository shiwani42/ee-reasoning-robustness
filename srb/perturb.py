"""Answer-preserving perturbations of a problem instance.

Every variant keeps the exact same physical problem, so the solver's answer is unchanged:
base, paraphrase_1, paraphrase_2, typos, unit_change, notation_change, distractor, reorder, few_shot, wrong_hint.
"""
from __future__ import annotations

import random
import re

from .problems import TEMPLATES, Given, Template, fmt

VARIANTS = ["base", "paraphrase_1", "paraphrase_2", "typos", "unit_change", "notation_change", "distractor",
            "reorder", "few_shot", "wrong_hint"]

ANSWER_LINE = "Give the final answer as a single number with its unit."

DISTRACTORS = [
    "The device is a GaN HEMT on a 100 µm thick SiC substrate.",
    "The gate length of the transistor is 0.25 µm.",
    "The bias network uses a 1 nF DC block and a 10 µH choke.",
    "The measurement was repeated three times on the same day.",
    "The circuit board is 0.5 mm thick Rogers RO4350B.",
    "The input is fed through a 30 cm long cable.",
]


def render_given(g: Given, unit_change=False, notation=False) -> str:
    sym = g.alt_symbol if notation else g.symbol
    if g.text:
        return (g.alt_text if unit_change and g.alt_text else g.text).format(sym=sym)
    v, unit = g.alt if (unit_change and g.alt) else (g.value, g.unit)
    return f"The {g.label} {sym} is {fmt(v)} {unit}".rstrip() + "."


def add_typos(text: str, rng: random.Random, rate=0.18) -> str:
    """Swap two interior letters in some words. Numbers, symbols and short words are left alone."""
    def swap(m):
        w = m.group(0)
        if len(w) < 5 or rng.random() > rate:
            return w
        i = rng.randrange(1, len(w) - 2)
        return w[:i] + w[i + 1] + w[i] + w[i + 2:]
    return re.sub(r"(?<![_\w])[A-Za-z]{5,}(?![_\w])", swap, text)


def build(t: Template, params: dict, variant: str, rng: random.Random) -> str:
    k = {"paraphrase_1": 1, "paraphrase_2": 2}.get(variant, 0)
    intro, question = t.intros[k], t.questions[k]
    givens = t.givens(params)
    lines = [render_given(g, unit_change=variant == "unit_change", notation=variant == "notation_change")
             for g in givens]
    question_first = False
    if variant == "reorder":
        if len(lines) > 1:
            order = list(range(len(lines)))
            while order == sorted(order):
                rng.shuffle(order)
            lines = [lines[i] for i in order]
        else:
            question_first = True          # one given only: ask first, then state it
    if variant == "distractor":
        lines.insert(rng.randrange(len(lines) + 1), rng.choice(DISTRACTORS))
    parts = [intro, question, *lines, t.notes] if question_first else [intro, *lines, t.notes, question]
    body = " ".join(parts).replace("  ", " ").strip()
    if variant == "typos":
        noisy = body
        while noisy == body:               # at least one typo
            noisy = " ".join([add_typos(intro, rng), *lines, t.notes, add_typos(question, rng)])
            noisy = noisy.replace("  ", " ").strip()
        body = noisy
    if variant == "wrong_hint":
        body += f" (A classmate who solved this got {fmt(t.wrong(params))} {t.answer_unit}.)".replace(" .", ".")
    text = body + " " + ANSWER_LINE
    if variant == "few_shot":
        text = few_shot_prefix(t, rng) + "Problem: " + text
    return text


def few_shot_prefix(exclude: Template, rng: random.Random, n=2) -> str:
    """Two worked examples from other templates, with their exact answers."""
    others = [t for t in TEMPLATES if t.name != exclude.name]
    out = []
    for t in rng.sample(others, n):
        p = t.sample(rng)
        out.append(f"Problem: {build(t, p, 'base', rng)}\nAnswer: {fmt(t.solve(p))} {t.answer_unit}".rstrip())
    return "\n\n".join(out) + "\n\n"
