"""Generate the public contract without loading secrets, models or a database."""

import json
from pathlib import Path

from services.api.app import create_app
from services.api.settings import ApiSettings


def main() -> None:
    path = Path(__file__).resolve().parents[1] / "docs/api/openapi.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(create_app(ApiSettings()).openapi(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("OpenAPI contract generated")


if __name__ == "__main__":
    main()
