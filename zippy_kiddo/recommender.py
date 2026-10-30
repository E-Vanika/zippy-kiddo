from dataclasses import dataclass
from typing import Protocol

from .schemas import Activity, Recommendation, RecommendationRequest, Supervision


SUPERVISION_CAPABILITY = {
    Supervision.INDEPENDENT: 0,
    Supervision.NEARBY: 1,
    Supervision.CONTINUOUS: 2,
}


@dataclass(frozen=True)
class RankedActivity:
    activity: Activity
    score: float
    reasons: tuple[str, ...]


class ActivityScorer(Protocol):
    def score(self, activity_id: str, request: RecommendationRequest) -> float: ...


def activity_category(activity: Activity) -> str:
    """Assign a stable broad category for varied result sets.

    This is presentation diversity only; eligibility constraints always run first.
    """
    text = " ".join((activity.title, activity.description)).lower()
    categories = (
        ("movement", ("move", "dance", "balance", "hop", "path", "freeze")),
        ("art", ("draw", "colour", "collage", "comic", "sticker", "pixel")),
        ("music-and-sound", ("sound", "music", "rhythm")),
        ("reading-and-stories", ("book", "story", "reading", "alphabet")),
        ("building-and-puzzles", ("build", "tower", "bridge", "puzzle", "shape")),
        ("nature-and-observation", ("nature", "leaf", "cloud", "shadow", "senses")),
    )
    for name, terms in categories:
        if any(term in text for term in terms):
            return name
    return "household-play"


def diversify(ranked: list[RankedActivity]) -> list[RankedActivity]:
    """Keep the best match from each category before returning close alternatives."""
    selected: list[RankedActivity] = []
    remaining: list[RankedActivity] = []
    seen_categories: set[str] = set()
    for item in ranked:
        category = activity_category(item.activity)
        if category not in seen_categories:
            selected.append(item)
            seen_categories.add(category)
        else:
            remaining.append(item)
    return selected + remaining


def is_eligible(activity: Activity, request: RecommendationRequest) -> bool:
    available_materials = set(request.materials)
    required_materials = set(activity.required_materials)

    return all(
        (
            activity.min_age <= request.age <= activity.max_age,
            request.duration_minutes >= activity.duration_minutes,
            request.setting in activity.setting,
            SUPERVISION_CAPABILITY[request.supervision]
            >= SUPERVISION_CAPABILITY[activity.supervision],
            required_materials.issubset(available_materials),
        )
    )


def rank_activity(
    activity: Activity,
    request: RecommendationRequest,
    model: ActivityScorer | None = None,
) -> RankedActivity:
    score = 0.0
    reasons: list[str] = []

    if activity.energy == request.energy:
        score += 4.0
        reasons.append(f"matches the requested {request.energy.value} energy level")
    else:
        score += 1.0

    remaining_time = request.duration_minutes - activity.duration_minutes
    score += max(0.0, 3.0 - remaining_time / 15)
    reasons.append(f"fits within {request.duration_minutes} minutes")

    if activity.supervision == request.supervision:
        score += 2.0
        reasons.append(f"matches {request.supervision.value} supervision")
    else:
        score += 1.0
        reasons.append("requires less supervision than is available")

    optional_match_count = len(
        set(activity.optional_materials).intersection(request.materials)
    )
    required_match_count = len(activity.required_materials)
    score += min(required_match_count, 3) * 2.5
    score += min(optional_match_count, 2) * 1.0

    if not activity.required_materials:
        reasons.append("needs no special materials")
    else:
        matched = ", ".join(activity.required_materials)
        reasons.append(f"uses your selected materials: {matched}")

    if optional_match_count:
        reasons.append("also uses optional materials you have")

    if model is not None:
        retrieval_score = model.score(activity.id, request)
        score += retrieval_score * 3.0
        if retrieval_score > 0:
            reasons.append("ranked by the deployed catalogue retrieval model")

    return RankedActivity(activity=activity, score=score, reasons=tuple(reasons))


def recommend(
    activities: tuple[Activity, ...],
    request: RecommendationRequest,
    model: ActivityScorer | None = None,
) -> tuple[list[Recommendation], list[str]]:
    eligible = [activity for activity in activities if is_eligible(activity, request)]
    unseen = [
        activity
        for activity in eligible
        if activity.id not in request.exclude_activity_ids
    ]
    # Never turn a safe request into an empty page merely because every safe
    # catalogue item has already been shown in this browser session.
    if unseen:
        eligible = unseen
    ranked = sorted(
        (rank_activity(activity, request, model) for activity in eligible),
        key=lambda item: (-item.score, item.activity.id),
    )

    recommendations = [
        Recommendation(
            activity_id=item.activity.id,
            title=item.activity.title,
            description=item.activity.description,
            why_it_matches=list(item.reasons),
            duration_minutes=item.activity.duration_minutes,
            setup_minutes=item.activity.setup_minutes,
            cleanup_minutes=item.activity.cleanup_minutes,
            materials=item.activity.required_materials,
            steps=item.activity.steps,
            supervision=item.activity.supervision,
            safety_note=item.activity.safety_note,
            score=round(item.score, 3),
        )
        for item in diversify(ranked)[: request.result_limit]
    ]

    relaxable: list[str] = []
    if len(recommendations) < request.result_limit:
        relaxable.extend(
            [
                "Select a longer available time.",
                "Add more ordinary household materials.",
                "Try another energy level or setting.",
            ]
        )

    return recommendations, relaxable
