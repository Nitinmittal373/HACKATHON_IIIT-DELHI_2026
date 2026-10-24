from datetime import UTC, date, datetime
from pathlib import Path

from app.db import make_engine, make_session_factory
from app.models import AreaScore, Driver, Finding, Project, Score, SourceRun
from app.store import Store

NOW = datetime(2026, 10, 25, 9, 0, tzinfo=UTC)
PROJECT = Project(
    rera_id="UPRERAPRJ8334",
    name="SUPERTECH ECO VILLAGE-I PHASE I-C",
    promoter="SUPERTECH LIMITED",
    registered_on=date(2017, 8, 9),
    district="Gautam Buddha Nagar",
    details_url="https://www.up-rera.in/Frm_View_Project_Details.aspx?id=8334",
)


def make_store(tmp_path: Path) -> Store:
    engine = make_engine(f"sqlite:///{(tmp_path / 'store.db').as_posix()}")
    return Store(make_session_factory(engine))


def test_check_round_trip(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    store.save_project(PROJECT)
    store.create_check("c" * 32, PROJECT.rera_id, NOW)
    store.save_source_run("c" * 32, SourceRun(source="uprera", status="running"))
    store.save_source_run(
        "c" * 32, SourceRun(source="uprera", status="completed", checks_read=["registration"])
    )
    store.set_check_status("c" * 32, "completed", NOW)

    check = store.get_check("c" * 32)
    assert check is not None
    assert check.status == "completed"
    assert check.started_at == NOW
    assert check.started_at.tzinfo is not None
    assert check.details_url == PROJECT.details_url
    assert [run.status for run in check.sources] == ["completed"]
    assert check.sources[0].checks_read == ["registration"]
    assert store.get_project(PROJECT.rera_id) == PROJECT


def test_score_sets_points_on_findings(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    store.save_project(PROJECT)
    store.create_check("d" * 32, PROJECT.rera_id, NOW)
    finding = Finding(
        id="f1",
        source="uprera",
        kind="past_end_date",
        title="Running 34 months past the latest approved end date",
        area="execution",
        verdict="red_flag",
        reliability="primary",
        source_url=PROJECT.details_url,
        read_on=date(2026, 10, 25),
        months=34,
    )
    store.add_finding("d" * 32, finding)
    score = Score(
        value=86,
        band="Low",
        confidence=0.29,
        hard_stop=False,
        drivers=[
            Driver(finding_id="f1", title=finding.title, area="execution", penalty=70, points=-14)
        ],
        areas=[AreaScore(area="execution", label="Project execution", weight=0.2, penalty=70)],
        checks_unread=["extensions"],
    )
    store.save_score("d" * 32, score)

    assert store.get_score("d" * 32) == score
    assert store.list_findings("d" * 32) == [finding]
