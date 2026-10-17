"""Two-step diagnosis parsing and deterministic degradation."""

import json
import re
from typing import Any


def parse_identification(text: str, knowledge: Any) -> dict[str, str]:
    cleaned = re.sub(r"```(?:json)?", "", text, flags=re.IGNORECASE).replace("```", "")
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    result: dict[str, Any] = {}
    if match:
        try:
            value = json.loads(match.group(0))
            if isinstance(value, dict):
                result = value
        except json.JSONDecodeError:
            pass
    problem_id = result.get("problem_id")
    if not isinstance(problem_id, str) or knowledge.get(problem_id) is None:
        problem_id = "unknown"
    confidence = str(result.get("confidence", "low")).lower()
    if confidence not in {"low", "medium", "high"}:
        confidence = "low"
    if problem_id == "unknown":
        confidence = "low"
    return {
        "crop": str(result.get("crop", "unknown")),
        "problem_id": problem_id,
        "confidence": confidence,
        "reason": str(result.get("reason", "")),
    }


def deterministic_advice(entry: dict[str, Any] | None) -> str:
    if not entry:
        return (
            "I could not identify the crop problem with confidence. "
            "Please send a clearer close-up photo in daylight, showing both sides of the leaf. "
            "Ask a local agricultural extension officer for help."
        )
    return " ".join(
        str(entry.get(field, "")).strip()
        for field in ("symptoms", "cultural_control", "see_officer_when")
        if entry.get(field)
    )
