# Manual pilot, 19 November 2026

Ten problems (one per template, seed 2026, `python -m srb.generate --per-template 1 --seed 2026 --variants base unit_change`),
each asked twice: in the base wording and with only the units changed (mA instead of A, radians instead of degrees,
dBm instead of W, S-parameters in dB and radians, return loss instead of |Γ|, kΩ instead of Ω, MHz instead of GHz,
kelvin instead of °C). Each of the 20 prompts was sent in a new temporary chat in the ChatGPT web app with its default
model, so no answer could see another. Responses are model-generated and copied verbatim into `responses.jsonl`;
`prompts.jsonl` has the exact prompts and solutions.

Score with `python -m srb.score pilot/responses.jsonl` (2 % tolerance, 0.2 dB for dB answers):

| | Correct |
|---|---|
| base wording | 7 / 10 |
| units changed | 8 / 10 |
| problems whose correctness changed with the units alone | 1 / 10 |

What went wrong:

- **L-section capacitor:** 0.593 pF in the base wording (correct: 5.94 pF), but 5.94 pF when the same resistances were
  given in kΩ and the frequency in MHz. Only the units differed.
- **Optimum load resistance:** 17.5 Ω in both wordings (correct: 35 Ω): the current swing was taken as I_max instead of
  I_max/2, the error the `wrong_hint` variant uses.
- **Maximum stable gain:** 34.8 dB in both wordings (correct: 17.4 dB): 20·log of the ratio |S21|/|S12|, which is
  already a power ratio.

This is one sample per prompt from one model, so it shows that the effects exist, not how often they occur. The full
study repeats each prompt several times, across all nine variants and several models.
