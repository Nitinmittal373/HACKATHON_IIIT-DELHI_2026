"""Write the API contract (contracts/openapi.json) from the FastAPI app.

The frontend generates its types from this file, so a backend change reaches the frontend
as a type error instead of a runtime surprise. No server and no network are needed.
Run from backend/:  python -m scripts.export_openapi
"""

import json
import os
import tempfile
from pathlib import Path

# app.main builds a module-level app on import, which needs a key; none is ever used here.
os.environ.setdefault("TINYFISH_API_KEY", "contract-export-not-a-key")

from app.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402

CONTRACT = Path(__file__).resolve().parents[2] / "contracts" / "openapi.json"


def contract_text() -> str:
    """The schema with sorted keys, so the same API always gives byte-identical text."""
    with tempfile.TemporaryDirectory() as folder:
        settings = Settings(
            _env_file=None,  # type: ignore[call-arg]
            tinyfish_api_key="contract-export-not-a-key",  # type: ignore[arg-type]
            database_url=f"sqlite:///{Path(folder, 'contract.db').as_posix()}",
        )
        schema = create_app(settings, cache_dir=None).openapi()
    return json.dumps(schema, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main() -> None:
    CONTRACT.parent.mkdir(parents=True, exist_ok=True)
    CONTRACT.write_text(contract_text(), encoding="utf-8", newline="\n")
    print(f"wrote {CONTRACT.relative_to(CONTRACT.parents[1])}")


if __name__ == "__main__":
    main()
