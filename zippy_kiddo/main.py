import os
import time
from importlib.resources import files
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from . import __version__
from .assistant import answer_chat
from .catalog import load_catalogue
from .recommender import recommend
from .retrieval import load_retrieval_model
from .schemas import (
    ChatRequest,
    ChatResponse,
    RecommendationRequest,
    RecommendationResponse,
)


APP_VERSION = os.getenv("APP_VERSION", "dev")
RETRIEVAL_MODEL = load_retrieval_model()
MODEL_REVISION = RETRIEVAL_MODEL.revision if RETRIEVAL_MODEL else None

REQUESTS = Counter(
    "zippy_http_requests_total",
    "HTTP requests by route template, method, and status",
    ("route", "method", "status"),
)
REQUEST_DURATION = Histogram(
    "zippy_http_request_duration_seconds",
    "HTTP request duration by route template and method",
    ("route", "method"),
)
RECOMMENDATION_DURATION = Histogram(
    "zippy_recommendation_duration_seconds",
    "Recommendation calculation duration",
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2),
)
RANKING_MODE = Counter(
    "zippy_ranking_mode_total",
    "Recommendation responses by ranking mode",
    ("mode",),
)

app = FastAPI(
    title="Zippy Kiddo",
    version=__version__,
    description="Safe activity recommendations for children ages 3-12.",
)
app.mount(
    "/static",
    StaticFiles(directory=str(files("zippy_kiddo").joinpath("static"))),
    name="static",
)


@app.middleware("http")
async def observe_requests(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    route = request.scope.get("route")
    route_label = getattr(route, "path", "unmatched")
    REQUESTS.labels(route_label, request.method, response.status_code).inc()
    REQUEST_DURATION.labels(route_label, request.method).observe(
        time.perf_counter() - started
    )
    response.headers["X-Request-ID"] = str(uuid4())
    return response


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home() -> str:
    path = files("zippy_kiddo").joinpath("static/index.html")
    return path.read_text(encoding="utf-8")


@app.get("/healthz")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
def readiness(response: Response) -> dict[str, str | bool | int]:
    version, activities = load_catalogue()
    return {
        "status": "degraded" if RETRIEVAL_MODEL is None else "ready",
        "fallback_ready": True,
        "model_ready": RETRIEVAL_MODEL is not None,
        "catalogue_version": version,
        "activity_count": len(activities),
    }


@app.get("/version")
def version() -> dict[str, str | None]:
    catalogue_version, _ = load_catalogue()
    return {
        "application_version": APP_VERSION,
        "package_version": __version__,
        "catalogue_version": catalogue_version,
        "model_revision": MODEL_REVISION,
    }


@app.post("/api/v1/recommendations", response_model=RecommendationResponse)
def recommendations(payload: RecommendationRequest) -> RecommendationResponse:
    started = time.perf_counter()
    catalogue_version, activities = load_catalogue()
    ranked, relaxable = recommend(activities, payload, RETRIEVAL_MODEL)
    RECOMMENDATION_DURATION.observe(time.perf_counter() - started)
    ranking_mode = "hybrid-tfidf" if RETRIEVAL_MODEL else "deterministic"
    RANKING_MODE.labels(ranking_mode).inc()

    return RecommendationResponse(
        request_id=str(uuid4()),
        ranking_mode=ranking_mode,
        degraded=RETRIEVAL_MODEL is None,
        catalogue_version=catalogue_version,
        model_revision=MODEL_REVISION,
        recommendations=ranked,
        relaxable_constraints=relaxable,
    )


@app.post("/api/v1/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    _, activities = load_catalogue()
    return answer_chat(activities, payload, MODEL_REVISION)


@app.get("/api/v1/model-info")
def model_info() -> dict[str, str | bool | None]:
    return {
        "ranking_mode": "hybrid-tfidf" if RETRIEVAL_MODEL else "deterministic",
        "trained_model_loaded": RETRIEVAL_MODEL is not None,
        "model_revision": MODEL_REVISION,
        "safety_boundary": "Catalogue rules remain authoritative.",
    }


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
