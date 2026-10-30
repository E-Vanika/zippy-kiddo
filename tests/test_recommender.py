from zippy_kiddo.catalog import load_catalogue
from zippy_kiddo.recommender import is_eligible, recommend
from zippy_kiddo.schemas import Energy, RecommendationRequest, Setting, Supervision


class PreferCupTower:
    def score(self, activity_id: str, request: RecommendationRequest) -> float:
        return 100.0 if activity_id == "cup-tower" else 0.0


def request_for(**overrides: object) -> RecommendationRequest:
    values: dict[str, object] = {
        "age": 6,
        "duration_minutes": 30,
        "setting": Setting.INDOOR,
        "supervision": Supervision.NEARBY,
        "energy": Energy.MODERATE,
        "materials": [],
    }
    values.update(overrides)
    return RecommendationRequest(**values)


def test_normal_request_returns_six_deterministic_recommendations() -> None:
    _, activities = load_catalogue()
    payload = request_for()

    first, _ = recommend(activities, payload)
    second, _ = recommend(activities, payload)

    assert len(first) == 6
    assert [item.activity_id for item in first] == [
        item.activity_id for item in second
    ]


def test_age_is_a_hard_constraint() -> None:
    _, activities = load_catalogue()
    activity = next(item for item in activities if item.id == "mini-comic")

    assert not is_eligible(activity, request_for(age=6, materials=["paper", "pencil"]))


def test_supervision_is_a_hard_constraint() -> None:
    _, activities = load_catalogue()
    activity = next(item for item in activities if item.id == "pillow-path")

    assert not is_eligible(
        activity,
        request_for(
            age=5,
            supervision=Supervision.NEARBY,
            materials=["pillows"],
        ),
    )


def test_required_materials_are_a_hard_constraint() -> None:
    _, activities = load_catalogue()
    activity = next(item for item in activities if item.id == "cup-tower")

    assert not is_eligible(activity, request_for(age=8))
    assert is_eligible(activity, request_for(age=8, materials=["plastic cups"]))


def test_selected_material_changes_the_top_recommendation() -> None:
    _, activities = load_catalogue()

    without_cups, _ = recommend(activities, request_for(age=8))
    with_cups, _ = recommend(
        activities, request_for(age=8, materials=["plastic cups"])
    )

    assert without_cups[0].activity_id != "cup-tower"
    assert with_cups[0].activity_id == "cup-tower"


def test_result_limit_is_respected() -> None:
    _, activities = load_catalogue()
    three, _ = recommend(activities, request_for(result_limit=3))
    nine, _ = recommend(activities, request_for(result_limit=9))

    assert len(three) == 3
    assert 3 < len(nine) <= 9


def test_model_ranking_cannot_bypass_material_safety_constraint() -> None:
    _, activities = load_catalogue()

    ranked, _ = recommend(activities, request_for(age=8), PreferCupTower())

    assert all(item.activity_id != "cup-tower" for item in ranked)
