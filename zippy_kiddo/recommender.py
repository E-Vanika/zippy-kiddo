from dataclasses import dataclass

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
    activity: Activity, request: RecommendationRequest
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
    score += min(optional_match_count, 2) * 0.5

    if not activity.required_materials:
        reasons.append("needs no special materials")
    else:
        reasons.append("uses only the materials you selected")

    return RankedActivity(activity=activity, score=score, reasons=tuple(reasons))


def recommend(
    activities: tuple[Activity, ...], request: RecommendationRequest
) -> tuple[list[Recommendation], list[str]]:
    eligible = [activity for activity in activities if is_eligible(activity, request)]
    ranked = sorted(
        (rank_activity(activity, request) for activity in eligible),
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
        for item in ranked[:3]
    ]

    relaxable: list[str] = []
    if len(recommendations) < 3:
        relaxable.extend(
            [
                "Select a longer available time.",
                "Add more ordinary household materials.",
                "Try another energy level or setting.",
            ]
        )

    return recommendations, relaxable
