"""Shapes for Neev Sentinel: a watch on a project and the alerts its re-checks produce."""

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.api_model import ApiModel
from app.models import DisplayScore, is_new_format, is_uprera_url, normalize_rera_id

Language = Literal["en", "hi"]
# Deliberately simple: one @, something on both sides, a dot in the domain.
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_WATCHES_PER_EMAIL = 3


class WatchCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rera_id: str = Field(max_length=40)
    details_url: str | None = Field(default=None, max_length=500)
    email: str = Field(max_length=254)
    language: Language = "en"

    @field_validator("rera_id")
    @classmethod
    def valid_rera_id(cls, value: str) -> str:
        normalized = normalize_rera_id(value)
        if normalized is None:
            raise ValueError("must be a UP-RERA project number such as UPRERAPRJ8334")
        return normalized

    @field_validator("details_url")
    @classmethod
    def uprera_url_only(cls, value: str | None) -> str | None:
        if value is not None and not is_uprera_url(value):
            raise ValueError("must be an https link on up-rera.in")
        return value

    @field_validator("email")
    @classmethod
    def valid_email(cls, value: str) -> str:
        email = value.strip().lower()
        if not EMAIL_PATTERN.match(email):
            raise ValueError("must be a valid email address")
        return email

    @model_validator(mode="after")
    def new_format_needs_url(self) -> "WatchCreate":
        if is_new_format(self.rera_id) and self.details_url is None:
            raise ValueError("new-format numbers need the details_url returned by search")
        return self


class Watch(ApiModel):
    id: str
    rera_id: str
    email: str
    language: Language
    created_at: datetime
    baseline_check_id: str | None = None


class FindingChange(ApiModel):
    title: str
    source_url: str | None = None


class Diff(ApiModel):
    added: list[FindingChange] = []
    removed: list[FindingChange] = []
    changed: list[FindingChange] = []

    @property
    def is_empty(self) -> bool:
        return not (self.added or self.removed or self.changed)


class Alert(ApiModel):
    id: str
    watch_id: str
    rera_id: str
    project_name: str | None = None
    check_id: str
    created_at: datetime
    # The classic 0-100 scores, kept for older clients; screens show the display scores.
    old_score: int | None
    new_score: int | None
    # The 300-900 scores the project had before and after the change, as they were then.
    old_display_score: DisplayScore | None = None
    new_display_score: DisplayScore | None = None
    added: list[FindingChange]
    removed: list[FindingChange]
    changed: list[FindingChange]
