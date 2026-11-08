"""Discover Gemini Search-grounded candidates; never publish them directly."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ALLOWED_DURATIONS = (5, 10, 15, 30, 45, 60)
ALLOWED_SETTINGS = {"indoor", "outdoor"}
ALLOWED_ENERGY = {"calm", "moderate", "active"}
ALLOWED_SUPERVISION = {"independent", "nearby", "continuous"}
MAX_CANDIDATES_PER_RUN = 10
TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:60]


def normalise_duration(value: object) -> int | None:
    if not isinstance(value, int):
        return None
    return max((item for item in ALLOWED_DURATIONS if item <= value), default=None)


def string_list(value: object, *, limit: int = 12) -> list[str] | None:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        return None
    cleaned = [" ".join(item.strip().lower().split()) for item in value]
    if any(not item or len(item) > 80 for item in cleaned):
        return None
    return list(dict.fromkeys(cleaned))[:limit]


def title_tokens(value: str) -> set[str]:
    return set(TOKEN_PATTERN.findall(value.lower()))


def is_near_duplicate(title: str, known_titles: set[str]) -> bool:
    """Reject exact and high-overlap title duplicates before human review."""
    candidate_tokens = title_tokens(title)
    for known_title in known_titles:
        if title.lower() == known_title:
            return True
        known_tokens = title_tokens(known_title)
        overlap = len(candidate_tokens & known_tokens)
        union = len(candidate_tokens | known_tokens)
        if union and overlap / union >= 0.8:
            return True
    return False


def validate_candidate(
    raw: object,
    source_urls: list[str],
    discovered_at: str,
    *,
    known_titles: set[str] | None = None,
    allowed_materials: set[str] | None = None,
) -> dict[str, object] | None:
    """Turn untrusted model output into a bounded pending-review record."""
    if not isinstance(raw, dict):
        return None
    title, description, energy = raw.get("title"), raw.get("description"), raw.get("energy")
    supervision, safety_note = raw.get("supervision"), raw.get("safety_note")
    min_age, max_age = raw.get("min_age"), raw.get("max_age")
    duration = normalise_duration(raw.get("duration_minutes"))
    steps = string_list(raw.get("steps"), limit=5)
    required = string_list(raw.get("required_materials", []))
    optional = string_list(raw.get("optional_materials", []))
    settings = string_list(raw.get("setting"), limit=2)
    if not all(isinstance(item, str) for item in (title, description, energy, supervision, safety_note)):
        return None
    title, description, safety_note = (" ".join(item.split()) for item in (title, description, safety_note))
    if not source_urls or not (
        4 <= len(title) <= 80 and 20 <= len(description) <= 300 and 10 <= len(safety_note) <= 300
        and steps is not None and 2 <= len(steps) <= 5 and required is not None and optional is not None
        and settings is not None and settings and set(settings).issubset(ALLOWED_SETTINGS)
        and energy in ALLOWED_ENERGY and supervision in ALLOWED_SUPERVISION
        and isinstance(min_age, int) and isinstance(max_age, int) and 3 <= min_age <= max_age <= 12
        and duration is not None
    ):
        return None
    blocked = re.compile(r"\b(?:knife|scissors|fire|flame|stove|oven|chemical|battery|balloon|climb|trampoline|road)\b", re.I)
    text = " ".join([title, description, safety_note, *steps, *required, *optional])
    if blocked.search(text):
        return None
    if known_titles is not None and is_near_duplicate(title, known_titles):
        return None
    if allowed_materials is not None and not set(required + optional).issubset(allowed_materials):
        return None
    fingerprint = hashlib.sha256(title.lower().encode("utf-8")).hexdigest()[:12]
    return {
        "candidate_id": f"gemini-{discovered_at[:10]}-{slugify(title)}-{fingerprint}",
        "title": title, "description": description, "min_age": min_age, "max_age": max_age,
        "duration_minutes": duration, "setting": settings, "energy": energy,
        "supervision": supervision, "required_materials": required,
        "optional_materials": optional, "steps": steps, "safety_note": safety_note,
        "source_urls": source_urls, "discovered_at": discovered_at,
        "automated_validation": {
            "status": "passed",
            "checks": [
                "grounded-source-present",
                "schema-and-age-time-bounds",
                "low-risk-keyword-screen",
                "duplicate-title-screen",
                "known-materials-only",
            ],
        },
        "review_status": "pending", "reviewer": None,
    }


def extract_json(text: str) -> object:
    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    return json.loads(fenced.group(1) if fenced else text)


def response_text_and_sources(payload: dict[str, object]) -> tuple[str, list[str]]:
    candidates = payload.get("candidates", [])
    if not isinstance(candidates, list) or not candidates or not isinstance(candidates[0], dict):
        raise ValueError("Gemini returned no candidates")
    candidate = candidates[0]
    content = candidate.get("content", {})
    parts = content.get("parts", []) if isinstance(content, dict) else []
    text = "".join(part.get("text", "") for part in parts if isinstance(part, dict))
    metadata = candidate.get("groundingMetadata", {})
    chunks = metadata.get("groundingChunks", []) if isinstance(metadata, dict) else []
    urls: list[str] = []
    for chunk in chunks:
        web = chunk.get("web", {}) if isinstance(chunk, dict) else {}
        uri = web.get("uri") if isinstance(web, dict) else None
        if isinstance(uri, str) and uri.startswith("https://"):
            urls.append(uri)
    return text, list(dict.fromkeys(urls))[:10]


def gemini_discover(api_key: str, model: str) -> tuple[object, list[str]]:
    prompt = """Use Google Search to find 6 to 10 low-risk, screen-free activity concepts for children aged 3 to 12. Sources are inspiration only: write original wording, not copied steps. Exclude food, medical advice, water, sharp tools, heat, electricity, chemicals, balloons, climbing, roads, and specialist equipment. Every idea must suit a parent working nearby. Return JSON only: {"ideas":[{"title":"...","description":"...","min_age":3,"max_age":6,"duration_minutes":10,"setting":["indoor"],"energy":"calm|moderate|active","supervision":"independent|nearby|continuous","required_materials":[],"optional_materials":[],"steps":["...","..."],"safety_note":"..."}]}. Do not include source URLs."""
    body = {"contents": [{"parts": [{"text": prompt}]}], "tools": [{"google_search": {}}], "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}}
    request = Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
        data=json.dumps(body).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urlopen(request, timeout=90) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        raise RuntimeError(f"Gemini API returned HTTP {error.code}") from error
    except URLError as error:
        raise RuntimeError("Gemini API request failed") from error
    text, sources = response_text_and_sources(payload)
    return extract_json(text), sources


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalogue", type=Path, required=True)
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--model", default=os.getenv("GEMINI_DISCOVERY_MODEL", "gemini-2.5-flash"))
    args = parser.parse_args()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("GEMINI_API_KEY is required")
    catalogue = json.loads(args.catalogue.read_text(encoding="utf-8"))
    queue = json.loads(args.queue.read_text(encoding="utf-8"))
    known_titles = {item["title"].strip().lower() for item in catalogue["activities"]}
    known_titles.update(item["title"].strip().lower() for item in queue["candidates"])
    allowed_materials = {
        material
        for activity in catalogue["activities"]
        for material in (*activity["required_materials"], *activity["optional_materials"])
    }
    discovered_at = datetime.now(UTC).isoformat()
    generated, sources = gemini_discover(api_key, args.model)
    ideas = generated.get("ideas", []) if isinstance(generated, dict) else []
    accepted: list[dict[str, object]] = []
    for idea in ideas[:MAX_CANDIDATES_PER_RUN]:
        candidate = validate_candidate(
            idea,
            sources,
            discovered_at,
            known_titles=known_titles,
            allowed_materials=allowed_materials,
        )
        if candidate:
            accepted.append(candidate)
            known_titles.add(str(candidate["title"]).lower())
    queue["last_run"] = {"at": discovered_at, "model": args.model, "source_count": len(sources), "generated_count": len(ideas), "accepted_count": len(accepted)}
    queue["candidates"].extend(accepted)
    args.queue.write_text(json.dumps(queue, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(queue["last_run"], sort_keys=True))


if __name__ == "__main__":
    main()
