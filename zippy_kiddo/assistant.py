from .recommender import recommend
from .schemas import Activity, ChatRequest, ChatResponse


def _known_materials(activities: tuple[Activity, ...]) -> tuple[str, ...]:
    materials = {
        material
        for activity in activities
        for material in (*activity.required_materials, *activity.optional_materials)
    }
    return tuple(sorted(materials, key=lambda value: (-len(value), value)))


def answer_chat(
    activities: tuple[Activity, ...],
    payload: ChatRequest,
    model_revision: str | None = None,
) -> ChatResponse:
    message = payload.message.lower()

    if any(word in message for word in ("hello", "hi ", "hey", "good morning")):
        return ChatResponse(
            reply=(
                "Hi! Select the child's age, time, setting, supervision, energy, "
                "and materials. I can then explain or expand the safe matches."
            ),
            assistant_mode="catalogue",
        )

    if any(word in message for word in ("train", "model", "ai")):
        model_message = (
            f"A catalogue retrieval model is loaded at revision {model_revision}."
            if model_revision
            else "No trained retrieval artifact is currently loaded."
        )
        return ChatResponse(
            reply=(
                f"{model_message} Deterministic safety rules remain authoritative, "
                "and no language model makes child-safety decisions."
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
    context = payload.context.model_copy(
        update={"materials": sorted(selected), "result_limit": 10}
    )
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
    material_text = (
        f" using {', '.join(mentioned)}" if mentioned else " for the current filters"
    )
    return ChatResponse(
        reply=f"Good matches{material_text}: {', '.join(titles)}.",
        assistant_mode="catalogue",
        suggested_activities=titles,
    )
