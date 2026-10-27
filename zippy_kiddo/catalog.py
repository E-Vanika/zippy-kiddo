import json
from functools import lru_cache
from importlib.resources import files

from pydantic import TypeAdapter

from .schemas import Activity


@lru_cache(maxsize=1)
def load_catalogue() -> tuple[str, tuple[Activity, ...]]:
    path = files("zippy_kiddo").joinpath("data/activities.json")
    payload = json.loads(path.read_text(encoding="utf-8"))

    version = str(payload["catalogue_version"])
    activities = TypeAdapter(list[Activity]).validate_python(payload["activities"])

    ids = [activity.id for activity in activities]
    if len(ids) != len(set(ids)):
        raise ValueError("catalogue contains duplicate activity IDs")
    if len(activities) < 30:
        raise ValueError("catalogue must contain at least 30 activities")

    return version, tuple(activities)
