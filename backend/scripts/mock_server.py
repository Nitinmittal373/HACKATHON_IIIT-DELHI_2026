"""Run the API with TinyFish replaced by slow fake data. For frontend work and rehearsals: costs no credits.

    python -m scripts.mock_server        (from the backend folder) -> http://localhost:8000

Every report it produces is SAMPLE data. Never present it as a real check.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import uvicorn  # noqa: E402

from app import main, tf  # noqa: E402
from tests.test_api_flow import fake_agent, fake_search  # noqa: E402

STEPS = ["Opening the page", "Reading the main details", "Opening the next tab", "Extracting the fields"]


async def slow_search(*a, **kw):
    await asyncio.sleep(0.8)
    return await fake_search(*a, **kw)


async def slow_agent(lane, url, goal, schema, emit, **kw):
    await emit({"lane": lane, "type": "progress", "message": "Waiting for a free agent slot..."})
    for step in STEPS:
        await asyncio.sleep(1.2)
        await emit({"lane": lane, "type": "progress", "message": step})
    return await fake_agent(lane, url, goal, schema, emit)


tf.search, tf.agent = slow_search, slow_agent
uvicorn.run(main.app, host="127.0.0.1", port=8000)
