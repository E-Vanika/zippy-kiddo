"""Fit the Zippy Kiddo catalogue TF-IDF retrieval model on Kaggle."""

import hashlib
import json
import math
import os
import re
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
STOP_WORDS = {
    "a", "an", "and", "are", "at", "for", "from", "in", "into", "is",
    "it", "of", "on", "or", "the", "to", "with",
}


def tokens(value: str) -> list[str]:
    return [
        token for token in TOKEN_PATTERN.findall(value.lower()) if token not in STOP_WORDS
    ]


def activity_document(activity: dict[str, object]) -> str:
    materials = [
        *activity["required_materials"],  # type: ignore[index]
        *activity["optional_materials"],  # type: ignore[index]
    ]
    return " ".join(
        [
            str(activity["title"]),
            str(activity["description"]),
            " ".join(str(value) for value in activity["steps"]),  # type: ignore[index]
            " ".join(str(value) for value in materials * 4),
            " ".join(str(value) for value in activity["setting"]),  # type: ignore[index]
            f"{activity['energy']} {activity['energy']}",
            str(activity["supervision"]),
        ]
    )


def normalise(weights: dict[str, float]) -> dict[str, float]:
    magnitude = math.sqrt(sum(value * value for value in weights.values()))
    if magnitude == 0:
        return {}
    return {token: round(value / magnitude, 8) for token, value in weights.items()}


def cosine(left: dict[str, float], right: dict[str, float]) -> float:
    return sum(value * right.get(token, 0.0) for token, value in left.items())


def main() -> None:
    source = Path(__file__).with_name("activities.json")
    if not source.is_file():
        source = Path(__file__).resolve().parents[2] / "zippy_kiddo/data/activities.json"
    payload = json.loads(source.read_text(encoding="utf-8"))
    activities = payload["activities"]
    documents = {
        activity["id"]: tokens(activity_document(activity)) for activity in activities
    }

    document_frequency: Counter[str] = Counter()
    for document in documents.values():
        document_frequency.update(set(document))
    count = len(documents)
    idf = {
        token: math.log((1 + count) / (1 + frequency)) + 1
        for token, frequency in document_frequency.items()
    }

    vectors: dict[str, dict[str, float]] = {}
    for activity_id, document in documents.items():
        term_frequency = Counter(document)
        vectors[activity_id] = normalise(
            {token: frequency * idf[token] for token, frequency in term_frequency.items()}
        )

    top_one_hits = 0
    for activity in activities:
        query = tokens(
            " ".join(
                [
                    str(activity["title"]),
                    " ".join(activity["required_materials"]),
                    str(activity["energy"]),
                ]
            )
        )
        query_counts = Counter(query)
        query_vector = normalise(
            {
                token: frequency * idf[token]
                for token, frequency in query_counts.items()
                if token in idf
            }
        )
        best = max(vectors, key=lambda key: cosine(query_vector, vectors[key]))
        top_one_hits += int(best == activity["id"])

    top_one_accuracy = top_one_hits / count
    if top_one_accuracy < 0.80:
        raise RuntimeError(
            f"retrieval quality gate failed: top1={top_one_accuracy:.3f}"
        )

    trained_at = datetime.now(UTC).isoformat()
    model = {
        "format": "zippy-kiddo-tfidf-v1",
        "trained_at": trained_at,
        "catalogue_version": payload["catalogue_version"],
        "document_count": count,
        "idf": {token: round(value, 8) for token, value in sorted(idf.items())},
        "activity_vectors": vectors,
    }
    metrics = {
        "trained_at": trained_at,
        "training_platform": os.getenv("TRAINING_PLATFORM", "kaggle"),
        "catalogue_version": payload["catalogue_version"],
        "document_count": count,
        "vocabulary_size": len(idf),
        "self_retrieval_top1_accuracy": round(top_one_accuracy, 4),
        "quality_gate": "passed",
    }

    output = Path(os.getenv("MODEL_OUTPUT_DIR", "/kaggle/working"))
    if not output.parent.is_dir():
        output = Path(__file__).resolve().parent / "output"
    output.mkdir(parents=True, exist_ok=True)
    model_path = output / "model.json"
    model_path.write_text(json.dumps(model, indent=2, sort_keys=True), encoding="utf-8")
    metrics["model_sha256"] = hashlib.sha256(model_path.read_bytes()).hexdigest()
    (output / "metrics.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True), encoding="utf-8"
    )
    (output / "README.md").write_text(
        "# Zippy Kiddo Catalogue Ranker\n\n"
        "A compact TF-IDF retrieval model trained on the reviewed activity "
        "catalogue. Hard age, time, materials, setting, and supervision rules "
        "remain outside the model and authoritative.\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics, sort_keys=True))


if __name__ == "__main__":
    main()
