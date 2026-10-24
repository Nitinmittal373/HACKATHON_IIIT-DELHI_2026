# NeevScore methodology (v1.1)

NeevScore is a deterministic, evidence-based risk indicator from 300 to 900 for an under-construction
housing project and its promoter. Higher means less risk was found **in the records checked**.
The code is `backend/app/scoring.py`; keep this file and the code in sync.

An AI web agent helps *read* pages. It never decides the score.

## Formula

```
P          = Σ (w_i × p_i)              p_i = penalty of category i, 0..100
NeevScore  = clip(900 − 6 × P, 300, 900)
```

## Categories

| ID | Category | Weight | What is checked |
|---|---|---|---|
| P1 | Regulatory compliance (RERA) | 30% | Registration status, extensions, delay, quarterly progress reports, complaints, orders |
| P2 | Delivery track record | 20% | The promoter group's other projects (planned) |
| P3 | Legal & insolvency | 25% | Insolvency proceedings and their scope, pending cases |
| P4 | Company & financial health | 15% | Struck-off or liquidated links, SARFAESI, new charges |
| P5 | Land authority & approvals | 5% | Attributable dues/defaulter records, missing occupancy certificate |
| P6 | News & buyer sentiment | 5% | Distinct credible reports of delays or protests (signal only) |

## Rules

| Code | Signal | Penalty | Evidence needed / safeguard |
|---|---|---|---|
| R01 | Registration lapsed or revoked | P1 = 100, **hard stop** | Official UP-RERA status |
| R02 | Completion date extended | 30 first, +20 each after | Blanket COVID-era force majeure extensions are not counted |
| R03 | Running late | 40 if > 12 months, 70 if > 24 | Revised vs original date on UP-RERA |
| R04 | Progress report not filed | 15 per missing report (last 4) | Only when the page shows it was due |
| R05 | Complaints / penalty orders | 20 per order + 4 per complaint, max 40 | Complaints are allegations, not findings |
| R06 | Insolvency covering this project or the whole company | P3 = 100, **hard stop** | Official IBBI/NCLT record naming the promoter's exact legal name |
| R06S | Insolvency limited to a different project | 60, requires review | Project-wise insolvency is permitted (Supertech, NCLAT 2022, upheld 2023) |
| R06G | Verified group company in insolvency | 50 | Official record and a verified link |
| R06N | Insolvency in news only | 0, requires review | News is a signal, never proof |
| R07 | Struck-off or liquidated links | 40 | Company registry |
| R08 | Land-authority dues | 70 | Official authority page, or news naming the exact legal name |
| R09 | SARFAESI / new charge in 12 months | 60 / 10 | A charge alone is a secured loan, not a default |
| R10 | Pending court cases | 5 each, max 40 | Case status and project link |
| R11 | Adverse news | 10 per distinct story, max 60, requires review | Repeats across outlets count once |
| R12 | Data unavailable | 0 | Lowers confidence, never the score |

## Hard stops (precedence)

1. R01 or R06 → score capped at **449**, band **High risk**, whatever the other categories say.
2. Insolvency limited to another project (R06S) is **not** a hard stop.
3. A hard stop always needs an official record with an exact legal-name match. News never triggers one.

## Bands

- 750–900 **Low risk**. Shown as **Provisional: no red flags yet** when confidence < 80%.
- 600–749 **Watch** · 450–599 **Elevated** · 300–449 **High risk**
- **Not enough data** when UP-RERA could not be read or confidence < 50%. No number is shown.

## Evidence and confidence

- No source, no claim: every claim stores source URL, extract and **original** retrieval time (kept on cache replay).
- Each claim has a status: **Verified** (official), **Partially verified** (registry mirror), **Requires review** (news, inferred scope).
- Each check is recorded: found · not found in checked records · unavailable · CAPTCHA · skipped.
- Confidence = share of 7 key signals that could be read.
- Entity matching is strict: "Supertech Limited" ≠ "Supertech Realtors"; "Eco Village I" ≠ "Eco Village II".
- One story repeated by several outlets counts once.

## Worked example

3 counted extensions (P1 = 70) and promoter insolvency limited to another project (P3 = 60):

```
P = 0.30 × 70 + 0.25 × 60 = 36          NeevScore = 900 − 216 = 684  → Watch
```

If the proceedings covered this project: P = 21 + 25 = 46 → formula 624 → hard stop → **449, High risk**.

## Limitations and validation plan

The weights are initial design choices, not an official formula, and not yet statistically validated.
Planned: back-testing on projects with known outcomes, expert review of each rule, sensitivity tests on
weights, and double-counting checks. NeevCheck is decision support, not legal advice or a guarantee.
