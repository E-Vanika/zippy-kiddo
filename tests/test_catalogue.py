from zippy_kiddo.catalog import load_catalogue


def test_catalogue_has_at_least_thirty_unique_activities() -> None:
    version, activities = load_catalogue()

    assert version
    assert len(activities) >= 30
    assert len({activity.id for activity in activities}) == len(activities)


def test_draft_catalogue_does_not_claim_completed_human_review() -> None:
    _, activities = load_catalogue()

    assert all(activity.reviewer == "project-owner-review-required" for activity in activities)
