"""Fill the local database with one SAMPLE report so the frontend can be built without spending credits.

    python -m scripts.seed_sample        (run from the backend folder)

The sample is clearly labelled as sample data in the app. Never present it as a real check.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import main, store, tf  # noqa: E402
from tests.test_api_flow import fake_agent, fake_search  # noqa: E402


async def run() -> None:
    store.init()
    tf.search, tf.agent = fake_search, fake_agent
    inv = "sample0001"
    main.JOBS[inv] = {"query": "Sample data: Supertech Eco Village", "events": [], "status": "running",
                      "cond": asyncio.Condition()}
    await main._run(inv)
    r = store.get_report(inv)
    r.demo_replay = True
    store.save_report(r)
    print(f"Saved sample report {inv}: {r.score['score']} {r.score['band']}")


asyncio.run(run())
