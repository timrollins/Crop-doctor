"""Knowledge-base lookup by problem identifier."""

import json
from pathlib import Path
from typing import Any


class KnowledgeBase:
    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)

    def get(self, problem_id: str) -> dict[str, Any] | None:
        path = self.directory / f"{problem_id}.json"
        if not path.is_file():
            return None
        with path.open(encoding="utf-8") as file:
            value = json.load(file)
        return value if isinstance(value, dict) else None

    def list(self) -> list[dict[str, Any]]:
        entries = []
        for path in sorted(self.directory.glob("*.json")):
            with path.open(encoding="utf-8") as file:
                value = json.load(file)
            if isinstance(value, dict):
                entries.append(value)
        return entries
