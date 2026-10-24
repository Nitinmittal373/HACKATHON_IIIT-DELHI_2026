# NeevScore method

NeevScore is a number from 0 to 100. It is **deterministic**: the same records always produce the same score, and every point lost is linked to the record that caused it.

## Formula

```text
NeevScore = round(100 − Σ (weight × penalty))
```

- Each **area** has a weight (they add up to 100%).
- Each **finding** has a penalty from 0 to 100 within its area.
- Penalties within one area are capped at 100.
- A **hard stop** caps the final score at 39 (Critical).

## Weights

| Area | Weight |
| --- | --: |
| UP-RERA compliance | 25% |
| Project execution | 20% |
| Legal and courts | 15% |
| Financial and insolvency | 15% |
| Builder history | 15% |
| News | 10% |

## Rules that keep the score honest

| Rule | Why |
| --- | --- |
| Absence of a record never adds points | "Nothing found" may only mean a site was unreadable |
| An unreadable source lowers confidence, not the score | We never punish a project for a CAPTCHA |
| Insolvency counts fully only when it covers the company or this project | Supertech's process was limited to Eco Village-II by NCLAT |
| A petition that is not yet admitted is a "review" finding | Filing is not the same as admission |
| News is a secondary source | It can only add small penalties and is marked for review |
| COVID-19 force-majeure extensions are not counted as delays | They were granted to all projects |

## Bands

| Band | Range |
| --- | --- |
| Low | 80–100 |
| Moderate | 60–79 |
| High | 40–59 |
| Critical | 0–39 |

## Worked example

Supertech Eco Village-I Phase I-C (`UPRERAPRJ8334`), read 24 Oct 2026:

| Finding | Area | Penalty | Points |
| --- | --- | --: | --: |
| Completion date extended 3 times | Project execution (20%) | 70 | −14 |
| Insolvency limited to another project | Financial and insolvency (15%) | 60 | −9 |
| One news story on delays | News (10%) | 10 | −1 |
| **NeevScore** | | | **76 · Moderate** |

Confidence is 71% because consumer cases (e-Jagriti, CAPTCHA) and delay length could not be read.
