"""What the app needs to draw the score: the scale, the band edges and the pillars.

The numbers come from the scoring constants, so the frontend never keeps its own copy.
"""

from typing import Literal

from app.api_model import ApiModel
from app.models import PillarId
from app.scoring.v2 import weights as w
from app.scoring.v2.reasons import DATA_UNAVAILABLE, LABELS

ScoreVersion = Literal["v2"]
RangeBandKey = Literal["Low", "Watch", "Elevated", "High"]


class Scale(ApiModel):
    min: int
    max: int


class BandRange(ApiModel):
    key: RangeBandKey
    min: int
    max: int


class PillarWeight(ApiModel):
    id: PillarId
    weight: float


class ReasonCodeId(ApiModel):
    code: str


class Meta(ApiModel):
    scale: Scale
    # Highest band first. A score outside every band is "not enough evidence", which has no range.
    bands: list[BandRange]
    pillars: list[PillarWeight]
    reason_codes: list[ReasonCodeId]
    score_version: ScoreVersion


def build_meta() -> Meta:
    bands: list[BandRange] = []
    top = w.SCALE_TOP
    for floor, key in w.BANDS:
        low = max(floor, w.SCALE_FLOOR)
        bands.append(BandRange(key=key, min=low, max=top))
        top = low - 1
    codes = sorted({*LABELS, DATA_UNAVAILABLE})
    return Meta(
        scale=Scale(min=w.SCALE_FLOOR, max=w.SCALE_TOP),
        bands=bands,
        pillars=[PillarWeight(id=id_, weight=weight) for id_, weight in w.PILLAR_WEIGHTS.items()],
        reason_codes=[ReasonCodeId(code=code) for code in codes],
        score_version="v2",
    )
