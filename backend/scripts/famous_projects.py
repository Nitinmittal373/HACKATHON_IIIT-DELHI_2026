"""Fifteen well-known projects, and how to tell whether a resolver found the right one.

Shared by the baseline script and the live test of the open-web search. A project counts as
found when a candidate's name or promoter holds every word of its `expect` pattern, so a
different project of the same builder does not pass.
"""

import re
from dataclasses import dataclass

from app.models import Project


@dataclass(frozen=True)
class Famous:
    query: str
    # Regex that the right candidate's "name promoter" text must match.
    expect: str

    def matches(self, project: Project) -> bool:
        text = f"{project.name or ''} {project.promoter or ''}"
        return bool(re.search(self.expect, text, re.IGNORECASE))


FAMOUS = (
    Famous("Lodha World Towers", r"world towers"),
    Famous("Prestige Lakeside Habitat", r"lakeside habitat"),
    Famous("DLF The Camellias", r"camellias"),
    Famous("Godrej Woods Noida", r"godrej woods"),
    Famous("M3M Golf Estate", r"golf estate"),
    Famous("Sobha Dream Acres", r"dream acres"),
    Famous("Brigade Utopia", r"utopia"),
    Famous("Hiranandani Fortune City", r"fortune city"),
    Famous("Tata Housing Eureka Park", r"eureka park"),
    Famous("Mahagun Mywoods", r"my\s?woods"),
    Famous("ATS Pristine", r"pristine"),
    Famous("Gaur City", r"gaur city"),
    Famous("My Home Bhooja", r"bhooja"),
    Famous("Puravankara Purva Atmosphere", r"atmosphere"),
    Famous("Shapoorji Pallonji Joyville Gurugram", r"joyville"),
)
