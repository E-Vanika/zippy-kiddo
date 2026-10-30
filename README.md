# Zippy Kiddo

Zippy Kiddo helps parents quickly find safe, practical activities that keep
children ages 3–12 engaged while the parent focuses on work. Suggestions adapt
to the child's age, available time, energy level, space, supervision, and
materials already at home.

## Live application

Zippy Kiddo is deployed on Oracle Cloud Infrastructure:

**[Open Zippy Kiddo](https://zippy-kiddo.129-225-85-54.sslip.io)**

The current public URL is also published in the **Live application** notice and
job summary of the latest successful
[Application CD workflow](../../actions/workflows/app-cd.yaml).

The production service exposes:

- `/` — activity recommendation interface
- `/healthz` — process health
- `/readyz` — deployment readiness
- `/version` — deployed application version
- `/docs` — interactive API documentation

## Product capabilities

- Filters activities by age, duration, location, energy, supervision, and
  available materials.
- Returns up to ten ranked suggestions and prioritizes activities that use the
  selected materials.
- Includes a catalogue-backed corner assistant without requiring an external
  AI service.
- Applies deterministic safety rules before presenting recommendations.
- Avoids collecting a child's name, contact information, precise location, or
  other unnecessary personal data.
- Provides a responsive web interface and a documented JSON API.

## Architecture

The FastAPI application serves the web interface and recommendation API from a
container behind Caddy. Curated activity data provides a reliable baseline;
model-assisted ranking can be introduced behind the same safety and fallback
boundaries without making the service dependent on a model provider.

### Recommendation intelligence

Production uses deterministic eligibility rules plus a compact trained ranker.
Age, time, setting, supervision, and required materials remain authoritative.
`/api/v1/model-info` reports whether the immutable model artifact is loaded; if
it is unavailable, the service safely falls back to deterministic ranking.

The model lifecycle runs on free services: Kaggle is the preferred training
runner, with the identical GitHub Actions trainer as a credential/outage
fallback. A quality gate checks retrieval accuracy, and Hugging Face is the
preferred versioned artifact store, with a repository-pinned fallback when its
credentials are unavailable. A checksum-protected model lock pins the exact
artifact used in the OCI image and records the training platform. Hard safety
constraints remain deterministic and the service falls back safely when an
artifact is unavailable. Future preference learning will require genuine,
reviewed, non-personal feedback rather than synthetic labels.

Production runs on an OCI Always Free E2 Micro instance. Terraform manages the
network and compute resources, Ansible reconciles the host, GitHub Actions
builds and deploys immutable container images, and GHCR stores those images.

## Reliability and delivery

- CI runs formatting, linting, type, security, dependency, and automated tests.
- Container images are scanned and addressed by the tested Git commit SHA.
- CD deploys the exact image that passed CI, checks readiness, and rolls back
  automatically when a release is unhealthy.
- Public smoke tests verify both readiness and the deployed version.
- Scheduled infrastructure runs retry OCI A1 capacity while the E2 Micro
  production service remains available.
- Terraform remote state and restricted, temporary SSH access keep deployment
  changes repeatable and auditable.

## Run locally

Requirements: Python 3.12 or Docker with Compose.

```bash
python -m venv .venv
python -m pip install -e ".[test]"
uvicorn zippy_kiddo.main:app --reload
```

Then open <http://127.0.0.1:8000>.

With containers:

```bash
docker compose up --build
```

Then open <http://127.0.0.1>.

## API example

```bash
curl -X POST http://127.0.0.1:8000/api/v1/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "age": 7,
    "duration_minutes": 30,
    "setting": "indoor",
    "energy": "moderate",
    "supervision": "nearby",
    "materials": ["paper", "pencil"]
  }'
```

## Repository layout

- `zippy_kiddo/` — application, recommendation logic, and web interface
- `tests/` — unit and API tests
- `terraform/` — OCI Always Free infrastructure
- `ansible/` — repeatable VM configuration
- `.github/workflows/` — continuous integration and deployment
- `data/` — versioned activity catalogue

## Cost and safety boundaries

Infrastructure is constrained to OCI Always Free resources. Workflows do not
fall back to paid compute shapes. External API credentials are stored only as
GitHub Actions secrets and are never committed to the repository.
