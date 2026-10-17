"""Knowledge-base loading and safe problem lookup."""

import json
import logging
from pathlib import Path
import re
from typing import Any

logger = logging.getLogger(__name__)
VALID_ID = re.compile(r"^[a-z0-9_-]+$")


class KnowledgeBase:
    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)
        self._entries: dict[str, dict[str, Any]] = {}
        self.reload()

    def reload(self) -> None:
        entries: dict[str, dict[str, Any]] = {}
        if self.directory.is_dir():
            for path in sorted(self.directory.iterdir()):
                if path.suffix.lower() != ".json":
                    continue
                try:
                    with path.open(encoding="utf-8") as file:
                        value = json.load(file)
                    values = value if isinstance(value, list) else [value]
                    for entry in values:
                        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
                            raise ValueError("entry must be an object with a string id")
                        problem_id = entry["id"]
                        if not VALID_ID.fullmatch(problem_id):
                            raise ValueError(f"invalid id {problem_id!r}")
                        if problem_id in entries:
                            logger.warning("Duplicate knowledge id %s in %s", problem_id, path)
                        entries[problem_id] = entry
                except (OSError, json.JSONDecodeError, ValueError) as exc:
                    logger.warning("Skipping invalid knowledge file %s: %s", path, exc)
        self._entries = entries

    def get(self, problem_id: str | None) -> dict[str, Any] | None:
        if not problem_id or not VALID_ID.fullmatch(problem_id):
            return None
        return self._entries.get(problem_id)

    def list(self) -> list[dict[str, Any]]:
        return list(self._entries.values())

    def catalog(self) -> list[dict[str, str]]:
        return [
            {"id": entry["id"], "crop": str(entry.get("crop", "")), "problem": str(entry.get("problem", ""))}
            for entry in self._entries.values()
        ]
