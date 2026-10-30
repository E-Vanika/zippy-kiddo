import hashlib
import json
import math
import re
from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import files

from .schemas import RecommendationRequest


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def _tokens(value: str) -> list[str]:
    return TOKEN_PATTERN.findall(value.lower())


@dataclass(frozen=True)
class RetrievalModel:
    revision: str
    catalogue_version: str
    idf: dict[str, float]
    activity_vectors: dict[str, dict[str, float]]

    def score(self, activity_id: str, request: RecommendationRequest) -> float:
        query_parts = [request.setting.value, request.energy.value, request.energy.value]
        for material in request.materials:
            query_parts.extend([material] * 4)
        counts: dict[str, int] = {}
        for token in _tokens(" ".join(query_parts)):
            if token in self.idf:
                counts[token] = counts.get(token, 0) + 1
        weighted = {
            token: count * self.idf[token] for token, count in counts.items()
        }
        magnitude = math.sqrt(sum(value * value for value in weighted.values()))
        if magnitude == 0:
            return 0.0
        vector = self.activity_vectors.get(activity_id, {})
        return sum(
            (value / magnitude) * vector.get(token, 0.0)
            for token, value in weighted.items()
        )


@lru_cache(maxsize=1)
def load_retrieval_model() -> RetrievalModel | None:
    model_path = files("zippy_kiddo").joinpath("model/model.json")
    lock_path = files("zippy_kiddo").joinpath("model/model-lock.json")
    if not model_path.is_file() or not lock_path.is_file():
        return None

    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        model_bytes = model_path.read_bytes()
        if hashlib.sha256(model_bytes).hexdigest() != lock["sha256"]:
            return None
        payload = json.loads(model_bytes)
        if payload.get("format") != "zippy-kiddo-tfidf-v1":
            return None
        return RetrievalModel(
            revision=str(lock["revision"]),
            catalogue_version=str(payload["catalogue_version"]),
            idf={key: float(value) for key, value in payload["idf"].items()},
            activity_vectors={
                activity_id: {
                    key: float(value) for key, value in vector.items()
                }
                for activity_id, vector in payload["activity_vectors"].items()
            },
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None
