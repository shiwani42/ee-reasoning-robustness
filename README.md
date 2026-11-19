# ee-reasoning-robustness: same problem, different words

Do language models give the same answer to the same engineering problem when it is worded differently?

This repository generates quantitative RF and electrical-engineering problems with exact Python solvers, plus nine
rewordings of each problem that keep the answer unchanged. The goal is to measure how much a model's accuracy drops,
and how often its answer flips, when only the wording changes.

Status: early. The generator, solvers, perturbations and scoring work and are tested; the large-scale evaluation is
planned. A small manual pilot is in [`pilot/`](pilot/).

## Problems

Twelve templates, each with random parameter values and an exact solution:

| Template | Topic | Answer |
|---|---|---|
| `load_line_ropt` | optimum load resistance from the load line, R = 2(V_DD − V_k)/I_max | Ω |
| `load_line_pout` | class-A output power, (V_DD − V_k)·I_max/4 | W |
| `efficiency_conduction_angle` | ideal drain efficiency of a reduced-conduction-angle amplifier | % |
| `watts_to_dbm` | power in dBm | dBm |
| `pae` | power-added efficiency | % |
| `stability_k` | Rollett stability factor K from S-parameters | – |
| `msg` | maximum stable gain, 10·log(\|S21\|/\|S12\|) | dB |
| `mismatch_loss` | mismatch loss from \|Γ\| | dB |
| `vswr` | VSWR of a complex load | – |
| `quarter_wave` | characteristic impedance of a λ/4 transformer | Ω |
| `l_section_capacitor` | shunt capacitor of a low-pass L-section match | pF |
| `junction_temperature` | channel temperature from thermal resistance and dissipated power | °C |

## Rewordings

Each problem comes in ten versions with the same answer:

| Variant | What changes |
|---|---|
| `base` | reference wording |
| `paraphrase_1`, `paraphrase_2` | different sentences for the setting and the question |
| `typos` | letters swapped inside some words (numbers and symbols untouched) |
| `unit_change` | the same quantities in other units: dBm instead of W, mA instead of A, MHz instead of GHz, kΩ, K, S-parameters in dB and radians, return loss instead of \|Γ\| |
| `notation_change` | other symbols for the same quantities (V_supply for V_DD, s_21 for S21, …) |
| `distractor` | one irrelevant fact added |
| `reorder` | the given quantities in another order |
| `few_shot` | two solved examples from other templates placed before the problem |
| `wrong_hint` | "a classmate got …" with a plausible wrong answer from a typical mistake |

The misleading hints come from real mistakes: forgetting that the current swing is I_max/2, using drain efficiency
instead of PAE, dBW instead of dBm, return loss instead of mismatch loss, and so on. A test checks that none of them is
accidentally within tolerance.

## Usage

```
python -m srb.generate --per-template 2 --seed 0 --out problems.jsonl   # 12 × 2 × 10 = 240 prompts
python -m pytest                                                        # solver and variant checks
```

Each line of the output has the prompt, the exact answer, its unit, the tolerance type and the parameters. Scoring
(`srb/score.py`) takes the last number in a model's answer and counts it correct within 2 % (0.2 dB for answers in dB).

No dependencies beyond Python 3.10; `pytest` for the tests.

## Licence

MIT
