import re

from .recommender import recommend
from .schemas import Activity, ChatRequest, ChatResponse


AGE_PATTERN = re.compile(r"\b(1[0-2]|[3-9])\s*(?:years?\s*old|years?|yo)\b")


def _known_materials(activities: tuple[Activity, ...]) -> tuple[str, ...]:
    materials = {
        material
        for activity in activities
        for material in (*activity.required_materials, *activity.optional_materials)
    }
    return tuple(sorted(materials, key=lambda value: (-len(value), value)))


def _mentioned_age(message: str) -> int | None:
    match = AGE_PATTERN.search(message)
    return int(match.group(1)) if match else None


def answer_chat(
    activities: tuple[Activity, ...],
    payload: ChatRequest,
    model_revision: str | None = None,
) -> ChatResponse:
    message = payload.message.lower()

    if message.strip() in {"hi", "hello", "hey"} or "good morning" in message:
        return ChatResponse(
            reply=(
                "Hi! I can help with a safe, practical activity. Try: 'ideas for my "
                "4-year-old with paper and crayons' or tell me the time and materials "
                "you have."
            ),
            assistant_mode="catalogue",
        )

    if "train" in message and any(
        word in message for word in ("regular", "schedule", "often", "daily", "when")
    ):
        return ChatResponse(
            reply=(
                "The current model is not retrained continuously. It is retrained when "
                "the reviewed activity catalogue or training pipeline changes, or when a "
                "maintainer starts the Model Training workflow. Each approved run is "
                "quality-checked and deployed as an immutable version."
            ),
            assistant_mode="hybrid-tfidf" if model_revision else "catalogue",
        )

    if any(word in message for word in ("train", "model", "ai")):
        model_message = (
            f"A catalogue retrieval model is loaded at revision {model_revision}. It was "
            f"trained on {len(activities)} reviewed activity records, quality-checked, "
            "versioned in Hugging Face, and runs locally in this service."
            if model_revision
            else "No trained retrieval artifact is currently loaded."
        )
        return ChatResponse(
            reply=(
                f"{model_message} It does not train on child conversations or personal "
                "data. Deterministic safety rules remain authoritative, and no language "
                "model makes child-safety decisions."
            ),
            assistant_mode="hybrid-tfidf" if model_revision else "catalogue",
        )

    if any(word in message for word in ("safe", "danger", "supervision", "alone")):
        return ChatResponse(
            reply=(
                "Use the supervision filter and read each safety note. Suggestions "
                "support adult judgment; stop any activity that does not fit the "
                "child's abilities or environment."
            ),
            assistant_mode="catalogue",
        )

    if payload.context is None:
        return ChatResponse(
            reply=(
                "Set the activity filters first so I can answer using the child's "
                "age, available time, and supervision level."
            ),
            assistant_mode="catalogue",
        )

    mentioned = [
        material for material in _known_materials(activities) if material in message
    ]
    selected = set(payload.context.materials)
    selected.update(mentioned)
    updates: dict[str, object] = {"materials": sorted(selected), "result_limit": 10}
    if age := _mentioned_age(message):
        updates["age"] = age
    context = payload.context.model_copy(update=updates)
    matches, _ = recommend(activities, context)

    if not matches:
        return ChatResponse(
            reply=(
                "I could not find a safe match with those filters. Try more time, "
                "another setting or energy level, or add ordinary household materials."
            ),
            assistant_mode="catalogue",
        )

    titles = [match.title for match in matches[:5]]
    age_text = f" for a {context.age}-year-old" if "age" in updates else ""
    material_text = f" using {', '.join(mentioned)}" if mentioned else ""
    return ChatResponse(
        reply=(
            f"Here are safe, practical ideas{age_text}{material_text}: "
            f"{', '.join(titles)}. Select one below for its steps and safety note."
        ),
        assistant_mode="catalogue",
        suggested_activities=titles,
    )
