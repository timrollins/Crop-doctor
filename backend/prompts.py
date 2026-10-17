"""Prompt construction for crop diagnosis."""


def diagnosis_prompt(question: str, knowledge: dict | None = None) -> str:
    context = knowledge or {}
    return (
        "You are Crop Doctor, a cautious agricultural assistant. "
        "Give practical, low-risk advice and clearly state uncertainty.\n"
        f"Reference information: {context}\n"
        f"Farmer's question: {question}\n"
        "Answer with likely issue, immediate steps, and when to seek local expert help."
    )
