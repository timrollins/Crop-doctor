from __future__ import annotations

import json
import re
from pathlib import Path

from backend.knowledge import KnowledgeBase


REQUIRED_FIELDS = {
    "id",
    "crop",
    "problem",
    "symptoms",
    "cause",
    "cultural_control",
    "chemical_option",
    "prevention",
    "see_officer_when",
    "source",
    "review_status",
}


def test_knowledge_entries_load_and_validate(tmp_path: Path) -> None:
    knowledge_dir = Path("knowledge")
    knowledge = KnowledgeBase(knowledge_dir)
    entries = knowledge.list()

    assert len(entries) >= 10

    seen_ids: set[str] = set()
    for path in sorted(knowledge_dir.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        data = raw[0] if isinstance(raw, list) else raw
        assert isinstance(data, dict)
        assert data["id"] == path.stem
        assert data["id"] not in seen_ids
        seen_ids.add(data["id"])

        loaded = knowledge.get(data["id"])
        assert loaded is not None

        for field in REQUIRED_FIELDS:
            value = loaded.get(field)
            assert isinstance(value, str) and value.strip(), f"{path.name}:{field}"

        assert not re.search(r"\d+\s*(?:ml|g|kg|l|%)\b", loaded["chemical_option"], flags=re.IGNORECASE)


def test_banana_bxw_mentions_officer() -> None:
    knowledge = KnowledgeBase(Path("knowledge"))
    entry = knowledge.get("banana_bxw")
    assert entry is not None
    assert "officer" in entry["see_officer_when"].lower()