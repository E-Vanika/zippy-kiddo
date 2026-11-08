from training.discover_ideas import extract_json, validate_candidate


def valid_candidate() -> dict[str, object]:
    return {
        "title": "Texture Rubbing Explorer",
        "description": "Make crayon rubbings from safe flat textures placed on a table.",
        "min_age": 4,
        "max_age": 8,
        "duration_minutes": 20,
        "setting": ["indoor"],
        "energy": "calm",
        "supervision": "nearby",
        "required_materials": ["paper", "crayons"],
        "optional_materials": ["coins"],
        "steps": ["Place a safe flat texture under paper.", "Rub gently with a crayon."],
        "safety_note": "Use only large, safe household textures on a clear table.",
    }


def test_candidate_is_normalised_and_pending_review() -> None:
    candidate = validate_candidate(
        valid_candidate(), ["https://example.org/activity"], "2026-11-09T00:00:00+00:00"
    )
    assert candidate is not None
    assert candidate["duration_minutes"] == 15
    assert candidate["review_status"] == "pending"
    assert candidate["source_urls"] == ["https://example.org/activity"]


def test_high_risk_candidate_is_rejected() -> None:
    unsafe = valid_candidate()
    unsafe["steps"] = ["Use scissors to cut shapes.", "Arrange the shapes."]
    assert validate_candidate(unsafe, [], "2026-11-09T00:00:00+00:00") is None


def test_fenced_json_is_accepted() -> None:
    assert extract_json("```json\n{\"ideas\": []}\n```") == {"ideas": []}
