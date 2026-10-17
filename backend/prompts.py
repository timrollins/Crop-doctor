"""Prompt construction for crop diagnosis."""

import json
from typing import Any


def identification_prompt(question: str, catalog: list[dict[str, str]]) -> str:
    return (
        "Identify the crop problem from the farmer question and photo if provided. "
        "Choose only an id from the catalog, or unknown. Return ONLY JSON with keys "
        "crop, problem_id, confidence, and reason. Confidence must be low, medium, or high.\n"
        f"Catalog: {json.dumps(catalog)}\nFarmer question: {question}"
    )


def advice_prompt(
    question: str, entry: dict[str, Any] | None, language: str, confidence: str
) -> str:
    context = json.dumps(entry or {}, ensure_ascii=False)
    return (
        f"Write advice in {language}. Use simple everyday words for a farmer. "
        "Write 3 to 5 short plain sentences only: no markdown, bullets, emojis, or numbering. "
        "Base advice only on the provided knowledge entry. Never invent pesticide doses or brands. "
        "For chemicals, mention only generic names in the entry, protective clothing, and the "
        "pre-harvest interval on the label. Always end with see_officer_when guidance. "
        f"If confidence is {confidence}, do not name a disease with certainty when it is low; "
        "ask for a clearer close-up photo in daylight showing both sides of the leaf and "
        "recommend an extension officer.\n"
        f"Confidence: {confidence}\nKnowledge entry: {context}\nFarmer question: {question}"
    )


def diagnosis_prompt(question: str, knowledge: dict | None = None) -> str:
    return advice_prompt(question, knowledge, "English", "medium" if knowledge else "low")
