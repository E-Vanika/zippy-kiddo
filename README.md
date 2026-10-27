# Zippy Kiddo

Zippy Kiddo is a zero-cost, safety-first activity recommender for parents of
children ages 3–12. It is also an AI SRE/DevOps portfolio project: the system is
designed to stay useful when a model is unavailable, expose operational health,
and run within Oracle Cloud Always Free limits.

## Current state

- FastAPI service and responsive web interface
- 32 original draft activities with hard age, time, setting, material, and
  supervision filters
- deterministic ranking fallback (no external API or paid service required)
- health, readiness, version, and Prometheus metrics endpoints
- non-root, read-only application container and a small Caddy reverse proxy
- Terraform for OCI A1 Flex plus E2 Micro Always Free fallback

The activity catalogue is deliberately labelled `project-owner-review-required`.
It must be reviewed before this project claims that the content is human-approved
or ready for public use.

## Run locally

With Python 3.12:

```bash
python -m venv .venv
python -m pip install -e ".[test]"
python -m pytest
uvicorn zippy_kiddo.main:app --reload
```

Open `http://127.0.0.1:8000`.

Or use containers:

```bash
docker compose up --build
```

## API example

```bash
curl -X POST http://127.0.0.1:8000/api/v1/recommendations \
  -H "Content-Type: application/json" \
  -d '{"age":6,"duration_minutes":30,"setting":"indoor","supervision":"nearby","energy":"moderate","materials":[]}'
```

The API collects no name, email, precise location, photo, or other child
identity data. Invalid or unknown input fields are rejected.

## Reliability design

`/healthz` reports process liveness. `/readyz` separately reports whether the
optional model is available and confirms that the deterministic fallback is
ready. `/metrics` is available inside the application network but blocked by
Caddy from public access. See [plan.md](plan.md) for the product specification,
safety gates, ML plan, SLOs, and interview evidence map.

## Cost boundary

The deployment supports only `VM.Standard.E2.1.Micro` and
`VM.Standard.A1.Flex`. The Terraform workflow verifies those shape names and
does not fall back to a paid compute shape. A1 capacity is retried hourly while
the E2 instance remains the dependable Always Free baseline.

For the exact credential names and setup screens, follow
[docs/credentials-setup.md](docs/credentials-setup.md). The running application
does not currently require Hugging Face, Kaggle, YouTube, or any paid API.
