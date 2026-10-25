"""What changed between two checks of the same project.

A finding is identified by a stable key (its source, its kind and, for news, its link), not
by its title: titles carry numbers such as "passed 105 months ago" that move every month
without anything having changed. Two findings with the same key but different facts are a
change; a key that is only on one side is an addition or a removal.

Only sources that both checks really read are compared. A source that was blocked or unreadable
proves nothing, so unread to unread is never a change, a record that disappears because its
source went unread is not "removed", and a source read for the first time is not "added".
"""

from datetime import date

from app.models import Check, Finding, SourceName
from app.sentinel.models import Diff, FindingChange

Key = tuple[str, str, str]
Facts = tuple[int | None, str | None, date | None, str]

# The news source has no key checks, so a completed run is a read even with none listed.
NO_KEY_CHECKS: set[SourceName] = {"news"}


def key_of(finding: Finding) -> Key:
    link = finding.source_url if finding.kind == "news_story" else ""
    return (finding.source, finding.kind, link)


def facts_of(finding: Finding) -> Facts:
    return (finding.count, finding.scope, finding.occurred_on, finding.verdict)


def source_was_read(check: Check, source: SourceName) -> bool:
    run = next((run for run in check.sources if run.source == source), None)
    if run is None or run.status != "completed":
        return False
    return bool(run.checks_read) or source in NO_KEY_CHECKS


def diff_findings(
    old: list[Finding], new: list[Finding], old_check: Check, new_check: Check
) -> Diff:
    """Only sources read in both checks are compared; first reads and lost reads are not changes."""
    comparable = {
        f.source
        for f in [*old, *new]
        if source_was_read(old_check, f.source) and source_was_read(new_check, f.source)
    }
    before = {key_of(f): f for f in old if f.source in comparable}
    after = {key_of(f): f for f in new if f.source in comparable}
    diff = Diff()
    for key, finding in after.items():
        known = before.get(key)
        if known is None:
            diff.added.append(_change(finding))
        elif facts_of(known) != facts_of(finding):
            diff.changed.append(_change(finding))
    for key, finding in before.items():
        if key not in after:
            diff.removed.append(_change(finding))
    return diff


def _change(finding: Finding) -> FindingChange:
    return FindingChange(title=finding.title, source_url=finding.source_url)
