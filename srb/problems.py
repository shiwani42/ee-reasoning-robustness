"""Problem templates: quantitative RF / electrical-engineering problems with exact solvers.

Each template draws random parameter values, solves the problem exactly, and describes its given quantities so that
the perturbations in perturb.py can re-render the same problem in other units, notation or order without changing the
answer.
"""
from __future__ import annotations

import cmath
import math
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Given:
    label: str                    # "supply voltage"
    symbol: str                   # "V_DD"
    alt_symbol: str               # notation used by the notation-change variant
    value: float
    unit: str
    alt: tuple[float, str] | None = None   # same quantity in another unit (unit-change variant)
    text: str | None = None       # full sentence override, e.g. for S-parameters given as magnitude and angle
    alt_text: str | None = None   # sentence used by the unit-change variant when `text` is set


@dataclass
class Template:
    name: str
    topic: str
    intros: list[str]             # three wordings: base and two paraphrases
    questions: list[str]          # three wordings, aligned with intros
    answer_unit: str
    tol: str                      # "rel" (2 %) or "db" (0.2 dB absolute)
    sample: Callable              # rng -> params
    solve: Callable               # params -> answer
    givens: Callable              # params -> list[Given]
    wrong: Callable               # params -> a plausible wrong answer (for the misleading-hint variant)
    notes: str = ""               # assumptions stated in every version of the problem
    extra: dict = field(default_factory=dict)


def fmt(x: float) -> str:
    """Four significant figures, no trailing zeros."""
    return f"{x:.4g}"


def u(rng, lo, hi, nd=2):
    return round(rng.uniform(lo, hi), nd)


def dbm(p_w: float) -> float:
    return 10 * math.log10(p_w * 1e3)


def polar(mag: float, deg: float) -> complex:
    return cmath.rect(mag, math.radians(deg))


# ---------------------------------------------------------------- 1. optimum load resistance (load line)
def _ll_sample(rng):
    return dict(vdd=u(rng, 20, 50, 1), vk=u(rng, 2, 6, 1), imax=u(rng, 0.2, 2.0, 2))


def _ll_givens(p):
    return [Given("drain supply voltage", "V_DD", "V_supply", p["vdd"], "V"),
            Given("knee voltage", "V_k", "V_knee", p["vk"], "V"),
            Given("maximum drain current", "I_max", "I_peak", p["imax"], "A", (p["imax"] * 1e3, "mA"))]


LOAD_LINE_ROPT = Template(
    "load_line_ropt", "power amplifiers",
    ["A transistor is used as a class-A power amplifier.",
     "Consider a class-A RF power amplifier built around a single transistor.",
     "You are designing a class-A amplifier stage with one transistor."],
    ["What load resistance R_opt gives the maximum output power (the Cripps load line)?",
     "Find the optimum load resistance for maximum output power.",
     "Which load resistance should the drain see so that both voltage and current swings reach their limits?"],
    "Ω", "rel", _ll_sample,
    solve=lambda p: 2 * (p["vdd"] - p["vk"]) / p["imax"],
    givens=_ll_givens,
    wrong=lambda p: (p["vdd"] - p["vk"]) / p["imax"],          # forgets that the current swing is I_max/2
)

# ---------------------------------------------------------------- 2. class-A output power from the load line
LOAD_LINE_POUT = Template(
    "load_line_pout", "power amplifiers",
    ["A transistor is used as a class-A power amplifier and is loaded with its optimum load resistance.",
     "Consider a class-A RF power amplifier terminated in its optimum (load-line) resistance.",
     "A single-transistor class-A stage drives its optimum load resistance."],
    ["What is the maximum fundamental output power in watts?",
     "Find the largest output power at the fundamental frequency, in W.",
     "How much RF power at the fundamental can it deliver at most, in watts?"],
    "W", "rel", _ll_sample,
    solve=lambda p: (p["vdd"] - p["vk"]) * p["imax"] / 4,
    givens=_ll_givens,
    wrong=lambda p: (p["vdd"] - p["vk"]) * p["imax"] / 2,      # peak instead of RMS
    notes="Harmonics are short-circuited.",
)


# ---------------------------------------------------------------- 3. drain efficiency vs conduction angle
def _eta(alpha_deg: float) -> float:
    a = math.radians(alpha_deg)
    return (a - math.sin(a)) / (4 * (math.sin(a / 2) - (a / 2) * math.cos(a / 2)))


def _ca_sample(rng):
    return dict(alpha=float(rng.choice([180, 200, 210, 220, 240, 250, 270, 300, 330, 360])))


EFFICIENCY_ANGLE = Template(
    "efficiency_conduction_angle", "power amplifiers",
    ["An ideal transistor amplifier is biased so that drain current flows for only part of each RF cycle.",
     "A reduced-conduction-angle power amplifier uses an ideal transistor.",
     "Consider an ideal power amplifier whose drain current is cut off for part of the RF period."],
    ["What is the maximum drain efficiency, in percent?",
     "Find the ideal maximum drain efficiency (in %).",
     "What drain efficiency, in percent, can it reach at most?"],
    "%", "rel", _ca_sample,
    solve=lambda p: 100 * _eta(p["alpha"]),
    givens=lambda p: [Given("conduction angle", "α", "2θ", p["alpha"], "degrees",
                            (math.radians(p["alpha"]), "radians"))],
    wrong=lambda p: 50.0 if p["alpha"] != 360 else 78.54,       # class-A / class-B value regardless of angle
    notes="The knee voltage is zero, the current pulses are truncated sinusoids and all harmonics are short-circuited.",
)

# ---------------------------------------------------------------- 4. watts to dBm
DBM = Template(
    "watts_to_dbm", "power units",
    ["An amplifier delivers a certain RF output power.",
     "The output power of an RF stage has been measured.",
     "A power meter reads the RF output of an amplifier."],
    ["Express this power in dBm.",
     "What is the power in dBm?",
     "Convert the reading to dBm."],
    "dBm", "db",
    sample=lambda rng: dict(p=u(rng, 0.01, 20, 3)),
    solve=lambda p: dbm(p["p"]),
    givens=lambda p: [Given("output power", "P_out", "P_RF", p["p"], "W", (p["p"] * 1e3, "mW"))],
    wrong=lambda p: 10 * math.log10(p["p"]),                    # dBW instead of dBm
)


# ---------------------------------------------------------------- 5. power-added efficiency
def _pae_sample(rng):
    pdc = u(rng, 2, 20, 2)
    pout = round(pdc * rng.uniform(0.4, 0.7), 3)
    pin = round(pout / 10 ** (rng.uniform(6, 12) / 10), 4)    # gain at the measured drive (near compression)
    return dict(pdc=pdc, pout=pout, pin=pin)


PAE = Template(
    "pae", "power amplifiers",
    ["A power amplifier is measured at one drive level.",
     "The following was measured on an RF power amplifier.",
     "During a power sweep, one operating point of an amplifier gives these values."],
    ["What is the power-added efficiency (PAE) in percent?",
     "Find the PAE, in %.",
     "Compute the power-added efficiency (%)."],
    "%", "rel", _pae_sample,
    solve=lambda p: 100 * (p["pout"] - p["pin"]) / p["pdc"],
    givens=lambda p: [Given("RF output power", "P_out", "P_L", p["pout"], "W", (dbm(p["pout"]), "dBm")),
                      Given("RF input power", "P_in", "P_drive", p["pin"], "W", (dbm(p["pin"]), "dBm")),
                      Given("DC supply power", "P_DC", "P_supply", p["pdc"], "W")],
    wrong=lambda p: 100 * p["pout"] / p["pdc"],                 # drain efficiency
)


# ---------------------------------------------------------------- 6. Rollett stability factor K
def _s_sample(rng):
    return dict(s11=(u(rng, 0.5, 0.9), u(rng, -170, -40, 0)), s21=(u(rng, 2, 6), u(rng, 60, 170, 0)),
                s12=(u(rng, 0.02, 0.15, 3), u(rng, 10, 80, 0)), s22=(u(rng, 0.3, 0.8), u(rng, -90, -10, 0)))


def _k(p):
    s11, s21, s12, s22 = (polar(*p[k]) for k in ("s11", "s21", "s12", "s22"))
    d = s11 * s22 - s12 * s21
    num = 1 - abs(s11) ** 2 - abs(s22) ** 2 + abs(d) ** 2
    return num / (2 * abs(s12 * s21))


def _s_givens(p, keys=("s11", "s21", "s12", "s22")):
    out = []
    for k in keys:
        m, a = p[k]
        name = "S" + k[1:]
        out.append(Given(name, name, name.replace("S", "s_"), m, "", None,
                         text=f"{{sym}} = {fmt(m)} ∠ {fmt(a)}°.",
                         alt_text=f"{{sym}} has a magnitude of {fmt(20 * math.log10(m))} dB and an angle of "
                                  f"{fmt(math.radians(a))} rad."))
    return out


STABILITY_K = Template(
    "stability_k", "S-parameters and stability",
    ["A transistor has the following S-parameters (50 Ω reference) at the design frequency.",
     "The S-parameters of a transistor, measured in a 50 Ω system at one frequency, are listed below.",
     "At the operating frequency, a transistor's 50 Ω S-parameters are as follows."],
    ["What is the Rollett stability factor K?",
     "Compute the stability factor K.",
     "Find K, the Rollett stability factor."],
    "", "rel", _s_sample,
    solve=_k,
    givens=_s_givens,
    wrong=lambda p: 2 * _k(p),                                  # forgets the factor 2 in the denominator
)

# ---------------------------------------------------------------- 7. maximum stable gain
MSG = Template(
    "msg", "S-parameters and stability",
    ["A transistor is potentially unstable at the design frequency.",
     "At one frequency a transistor is not unconditionally stable.",
     "A device has K < 1 at the frequency of interest."],
    ["What is its maximum stable gain (MSG) in dB?",
     "Find the maximum stable gain, in dB.",
     "Compute the MSG in dB."],
    "dB", "db", _s_sample,
    solve=lambda p: 10 * math.log10(p["s21"][0] / p["s12"][0]),
    givens=lambda p: _s_givens(p, ("s21", "s12")),
    wrong=lambda p: 20 * math.log10(p["s21"][0] / p["s12"][0]),  # 20 log of a power ratio
)

# ---------------------------------------------------------------- 8. mismatch loss
MISMATCH = Template(
    "mismatch_loss", "matching",
    ["A load is connected to a matched source and reflects part of the incident wave.",
     "A matched generator drives a load that is not perfectly matched.",
     "A source with the reference impedance feeds a mismatched load."],
    ["What is the mismatch loss in dB?",
     "Find the mismatch loss (dB).",
     "How many dB are lost to the mismatch?"],
    "dB", "db",
    sample=lambda rng: dict(g=u(rng, 0.1, 0.6)),
    solve=lambda p: -10 * math.log10(1 - p["g"] ** 2),
    givens=lambda p: [Given("load reflection coefficient", "|Γ_L|", "|ρ|", p["g"], "",
                            text=f"The magnitude of the load reflection coefficient is {{sym}} = {fmt(p['g'])}.",
                            alt_text=f"The load has a return loss of {fmt(-20 * math.log10(p['g']))} dB.")],
    wrong=lambda p: -20 * math.log10(p["g"]),                   # return loss instead of mismatch loss
)

# ---------------------------------------------------------------- 9. VSWR of a complex load
VSWR = Template(
    "vswr", "matching",
    ["A load impedance terminates a transmission line.",
     "A line is terminated in a complex load.",
     "Consider a transmission line ending in the load below."],
    ["What is the voltage standing-wave ratio (VSWR) on the line?",
     "Find the VSWR.",
     "Compute the standing-wave ratio."],
    "", "rel",
    sample=lambda rng: dict(r=u(rng, 10, 150, 1), x=rng.choice([-1, 1]) * u(rng, 20, 80, 1),
                            z0=float(rng.choice([50, 75]))),
    solve=lambda p: (lambda g: (1 + g) / (1 - g))(abs((complex(p["r"], p["x"]) - p["z0"]) /
                                                      (complex(p["r"], p["x"]) + p["z0"]))),
    givens=lambda p: [Given("characteristic impedance", "Z_0", "Z_c", p["z0"], "Ω", (p["z0"] / 1e3, "kΩ")),
                      Given("load resistance", "R_L", "Re(Z_L)", p["r"], "Ω", (p["r"] / 1e3, "kΩ")),
                      Given("load reactance", "X_L", "Im(Z_L)", p["x"], "Ω", (p["x"] / 1e3, "kΩ"))],
    wrong=lambda p: max(p["r"], p["z0"]) / min(p["r"], p["z0"]),  # ignores the reactance
)

# ---------------------------------------------------------------- 10. quarter-wave transformer
QUARTER_WAVE = Template(
    "quarter_wave", "matching",
    ["A quarter-wave transmission line is used to match two resistances.",
     "Two real impedances are to be matched with a λ/4 line.",
     "A quarter-wavelength transformer connects a source resistance to a load resistance."],
    ["What characteristic impedance must the line have?",
     "Find the required characteristic impedance of the λ/4 section.",
     "Which characteristic impedance gives a perfect match at the design frequency?"],
    "Ω", "rel",
    sample=lambda rng: dict(rs=u(rng, 3, 30, 1), rl=float(rng.choice([50, 75, 100])), f=u(rng, 1, 12, 1)),
    solve=lambda p: math.sqrt(p["rs"] * p["rl"]),
    givens=lambda p: [Given("source resistance", "R_S", "R_in", p["rs"], "Ω", (p["rs"] / 1e3, "kΩ")),
                      Given("load resistance", "R_L", "R_out", p["rl"], "Ω", (p["rl"] / 1e3, "kΩ")),
                      Given("design frequency", "f_0", "f_c", p["f"], "GHz", (p["f"] * 1e3, "MHz"))],
    wrong=lambda p: (p["rs"] + p["rl"]) / 2,
)


# ---------------------------------------------------------------- 11. L-section matching capacitor
def _lsec(p):
    q = math.sqrt(p["rh"] / p["rl"] - 1)
    return 1 / (2 * math.pi * p["f"] * 1e9 * (p["rh"] / q)) * 1e12


L_SECTION = Template(
    "l_section_capacitor", "matching",
    ["A low-pass L-section (series inductor, shunt capacitor) matches a low resistance to a higher one.",
     "An L-network with a series L and a shunt C is used to match two resistances.",
     "A two-element low-pass matching network (series inductor, then a shunt capacitor) is designed."],
    ["What shunt capacitance, in pF, is needed? The capacitor is across the higher resistance.",
     "Find the shunt capacitor value (pF); it sits across the larger resistance.",
     "How large must the shunt capacitor be, in pF, if it is placed across the higher resistance?"],
    "pF", "rel",
    sample=lambda rng: dict(rl=u(rng, 3, 25, 1), rh=float(rng.choice([50, 75])), f=u(rng, 1, 10, 1)),
    solve=_lsec,
    givens=lambda p: [Given("low resistance", "R_low", "R_1", p["rl"], "Ω", (p["rl"] / 1e3, "kΩ")),
                      Given("high resistance", "R_high", "R_2", p["rh"], "Ω", (p["rh"] / 1e3, "kΩ")),
                      Given("frequency", "f", "f_0", p["f"], "GHz", (p["f"] * 1e3, "MHz"))],
    wrong=lambda p: 1 / (2 * math.pi * p["f"] * 1e9 * p["rl"] * math.sqrt(p["rh"] / p["rl"] - 1)) * 1e12,
)


# ---------------------------------------------------------------- 12. junction temperature
def _tj_sample(rng):
    pdc = u(rng, 2, 30, 2)
    pout = round(pdc * rng.uniform(0.4, 0.65), 3)
    pin = round(pout / 10 ** (rng.uniform(10, 18) / 10), 4)
    return dict(tc=u(rng, 25, 85, 0), rth=u(rng, 2, 15, 1), pdc=pdc, pout=pout, pin=pin)


JUNCTION_T = Template(
    "junction_temperature", "thermal",
    ["A power transistor operates under RF drive on a heat sink.",
     "An RF power transistor is mounted on a temperature-controlled base plate and driven with an RF signal.",
     "Under RF drive, a transistor dissipates heat through its thermal resistance to the case."],
    ["What is the channel (junction) temperature in °C?",
     "Find the junction temperature, in °C.",
     "Estimate the channel temperature (°C)."],
    "°C", "rel", _tj_sample,
    solve=lambda p: p["tc"] + p["rth"] * (p["pdc"] + p["pin"] - p["pout"]),
    givens=lambda p: [Given("case temperature", "T_case", "T_c", p["tc"], "°C", (p["tc"] + 273.15, "K")),
                      Given("junction-to-case thermal resistance", "R_th", "θ_jc", p["rth"], "K/W"),
                      Given("DC supply power", "P_DC", "P_supply", p["pdc"], "W"),
                      Given("RF input power", "P_in", "P_drive", p["pin"], "W", (dbm(p["pin"]), "dBm")),
                      Given("RF output power", "P_out", "P_L", p["pout"], "W", (dbm(p["pout"]), "dBm"))],
    wrong=lambda p: p["tc"] + p["rth"] * p["pdc"],             # all DC power treated as heat
)

TEMPLATES: list[Template] = [LOAD_LINE_ROPT, LOAD_LINE_POUT, EFFICIENCY_ANGLE, DBM, PAE, STABILITY_K, MSG,
                             MISMATCH, VSWR, QUARTER_WAVE, L_SECTION, JUNCTION_T]
BY_NAME = {t.name: t for t in TEMPLATES}
