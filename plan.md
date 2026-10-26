# Zippy Kiddo — Product and Delivery Specification

Status: Draft 1  
Primary objective: produce credible evidence for AI SRE, MLOps, and DevOps interviews  
Product objective: help a parent quickly choose a safe, age-appropriate activity that keeps a child independently engaged while the parent works  
Cost constraint: ₹0; paid cloud resources and paid inference are prohibited

## 1. How this specification is used

Development is requirement-driven. Every implementation change must trace to a
requirement or an explicitly recorded architecture decision in this document.

The delivery loop is:

1. Select one requirement.
2. Add or refine its acceptance examples.
3. Write a failing automated test where practical.
4. Implement the smallest change that satisfies the requirement.
5. Run functional, safety, reliability, and security checks.
6. Record operational evidence and update the requirement status.

A feature is not complete merely because the UI works. It must meet its
acceptance criteria, emit the specified telemetry, and have a documented
failure path.

Requirement states are `Proposed`, `Ready`, `In progress`, `Verified`, and
`Deferred`. A requirement cannot become `Ready` while it depends on an
unanswered product question.

## 2. Product boundaries

### 2.1 Confirmed

- The supported child age range is 3 through 12, inclusive.
- A parent or caregiver is the primary user.
- The service suggests activities; it does not supervise a child.
- The product must operate without paid infrastructure or paid model APIs.
- OCI Always Free is the application runtime.
- The model artifact is versioned and documented on Hugging Face Hub.
- E2 Micro is the immediately deployable fallback.
- A1 Flex remains an optional capacity-dependent upgrade.
- GitHub Actions performs validation and infrastructure deployment.

### 2.2 Not in the MVP

- Medical, developmental, behavioural, or educational diagnosis.
- Activities involving fire, sharp tools, medication, chemicals, choking
  hazards, unsupervised water, heights, roads, or leaving the home alone.
- Collection of a child's name, date of birth, photograph, voice, school,
  precise location, or other identifying information.
- Free-form AI generation of activities without catalogue and safety controls.
- User accounts, payments, advertising, or social features.
- Kubernetes, Istio, Argo CD, Redis, PostgreSQL, or SonarQube merely for tool
  count. They require a demonstrated product or operational need before use.
- AWS or any other paid-cloud extension.

## 3. Users and primary journey

### Persona P-001 — Working parent

A parent needs 10–45 minutes of focused work time. They know the child's age,
available materials, location, and how much supervision they can provide. They
want an idea in under a minute and must be able to understand setup and safety
requirements immediately.

### Primary journey J-001

1. The parent enters non-identifying constraints.
2. Zippy Kiddo validates the inputs.
3. Hard safety and eligibility rules remove unsuitable activities.
4. A versioned model ranks the remaining catalogue entries.
5. The application returns three recommendations with setup, duration,
   materials, supervision level, cleanup, and safety notes.
6. If model inference is unavailable, deterministic ranking returns safe
   recommendations and the UI clearly identifies fallback mode.
7. The parent may record whether a recommendation was useful without providing
   personal information.

## 4. Functional requirements

### FR-001 — Constraint input

Status: Ready

The UI shall accept:

- child age in whole years;
- available time: 5, 10, 15, 30, 45, or 60 minutes;
- setting: indoor or outdoor;
- supervision: continuous, nearby, or independent;
- energy level: calm, moderate, or active;
- zero or more available-material tags.

The form shall not request identifying information.

### FR-002 — Curated activity catalogue

Status: Proposed

Each activity shall have a stable ID and versioned metadata:

- title and short description;
- minimum and maximum age;
- minimum and maximum duration;
- setting, energy level, and supervision requirement;
- required and optional materials;
- numbered instructions;
- setup and cleanup estimates;
- safety exclusions and warnings;
- source or reviewer provenance;
- catalogue version.

The first release shall contain at least 30 manually reviewed activities and at
least five eligible activities for every supported age band.

### FR-003 — Hard eligibility and safety filter

Status: Proposed

Rules shall exclude an activity before model ranking when age, supervision,
setting, duration, materials, or safety constraints do not match. Model output
shall never override a hard exclusion.

Every exclusion rule shall have unit tests covering an allowed and a rejected
case.

### FR-004 — Model-assisted ranking

Status: Proposed

A small open model shall rank only the activities that survive FR-003. The
served artifact shall be pinned by immutable Hugging Face repository revision
or content digest, not a floating branch name.

The service response shall record:

- model repository and revision;
- catalogue version;
- inference duration;
- whether model or fallback ranking was used;
- non-sensitive reason codes for the highest-ranked activities.

The model must be small enough to run within the selected OCI host's measured
memory budget. Hosted Hugging Face Inference Providers are not a runtime
dependency because the free credit is insufficient for reliable operation.

### FR-005 — Recommendation response

Status: Proposed

The API shall return exactly three distinct recommendations when three eligible
activities exist. Each recommendation shall include:

- why it matches the submitted constraints;
- preparation and activity duration;
- materials;
- numbered steps;
- supervision level;
- cleanup guidance;
- safety note.

If fewer than three activities qualify, the response shall explain which
constraint limited the result without weakening a safety constraint.

### FR-006 — Deterministic fallback

Status: Proposed

When the model is missing, loading, timed out, unhealthy, or returns an invalid
result, the service shall rank eligible activities using a deterministic
weighted score. A model failure shall not cause an unsafe or empty response
when eligible catalogue entries exist.

Fallback activation shall increment a metric and add a structured log event.

### FR-007 — Feedback without child data

Status: Deferred until the recommendation flow is verified

The parent may submit `helpful`, `not_helpful`, or `completed`. Feedback shall
reference activity ID, catalogue version, and model revision but no child or
parent identifier. Rate limiting shall protect the endpoint.

### FR-008 — Health and version endpoints

Status: Proposed

The service shall expose:

- `/healthz` for process liveness;
- `/readyz` for catalogue and inference readiness;
- `/version` for application commit, model revision, and catalogue version;
- `/metrics` on the private container network only.

Model unavailability shall not fail `/readyz` while deterministic fallback is
healthy. The readiness response shall report the degraded state.

### FR-009 — Source provenance

Status: Proposed

Every catalogue activity shall identify how it was created:

- `original`, when written independently for Zippy Kiddo;
- `adapted`, when based on a source whose licence permits adaptation; or
- `inspired`, when a public source led to a newly written activity that does
  not copy the source's protected expression.

Where a source exists, the catalogue shall record its URL, publisher or
creator, access date, licence when known, and human reviewer. Source metadata
shall never include social-media usernames belonging to children.

An activity may not enter the approved catalogue until a human reviewer has
confirmed provenance, originality or reuse permission, safety metadata, and
age suitability.

## 5. Safety and privacy requirements

### SAFE-001 — Safety precedence

Status: Proposed

The decision order is fixed:

```text
input validation → hard safety filter → model ranking → output validation
```

No model score or generated text can bypass the hard safety filter.

### SAFE-002 — Output validation

Status: Proposed

The API shall reject unknown activity IDs, duplicate IDs, excluded IDs, invalid
schemas, and model output containing instructions not present in the catalogue.
It shall then use deterministic fallback.

### SAFE-003 — Privacy minimisation

Status: Proposed

Logs, metrics, traces, and feedback shall not contain raw request bodies, IP
addresses, free-form child descriptions, or identifying data. Age shall be
recorded only as a configured band in aggregate metrics.

### SAFE-004 — Clear responsibility

Status: Proposed

The UI shall state that recommendations do not replace adult judgment and that
the parent must check materials, environment, and the child's abilities.
This notice shall not be used as a substitute for product safety controls.

### SAFE-005 — Social and child-content exclusion

Status: Proposed

The research and training pipeline shall not collect social-media photographs,
video, audio, comments, profile information, usernames, engagement histories,
or other personal data. Content depicting or authored by children shall never
be copied into the catalogue or training dataset.

Social platforms may be used only as a discovery mechanism under the sourcing
policy in Section 10. Automated collection requires an approved official API,
a documented permitted use, and a separate specification change.

## 6. Reliability and operational requirements

### NFR-001 — Zero-cost enforcement

Status: In progress

- Only OCI shapes explicitly allowed by the infrastructure policy may deploy:
  `VM.Standard.E2.1.Micro` and `VM.Standard.A1.Flex`.
- CI shall fail if another compute shape is introduced.
- No paid Hugging Face compute or inference endpoint may be configured.
- No secret, private key, saved Terraform plan, `.env`, or state file may be
  committed or uploaded as a workflow artifact.
- The operator must verify account-specific Always Free eligibility and quota
  before the first apply.

### NFR-002 — Resource budget

Status: Proposed

The E2 deployment has a 1 GB memory ceiling. Before public deployment, measured
steady-state memory plus the configured failure margin shall fit within the VM.
Containers shall have explicit memory limits and bounded logs.

The E2 profile shall favour one application process with an embedded inference
adapter. A separate model service is permitted only on A1 or after measurements
prove it safe on E2.

### NFR-003 — Service objectives

Status: Proposed

- Availability SLO: 99.0% successful non-5xx responses over 30 days.
- Recommendation latency SLO: 95% below 2 seconds after model warm-up.
- Safe-response SLO: 100% of automated safety fixtures pass before deployment.
- Fallback success SLO: 99% of injected model failures return a valid safe
  fallback response.

The availability target acknowledges that one free VM is not host- or
availability-zone redundant.

### NFR-004 — Observability

Status: Proposed

Metrics shall use bounded-cardinality labels and include:

- request count, errors, and duration;
- recommendation and inference duration;
- model-load success and failure;
- fallback count and reason;
- eligible-candidate count;
- output-validation failures;
- process memory and CPU saturation;
- application, catalogue, and model versions as build information.

Structured logs shall carry a generated request ID but no user identity.

### NFR-005 — Release and rollback

Status: Proposed

- CI tests the exact Git commit used to build the image.
- Deployment uses immutable Git-SHA image tags.
- Readiness and an external smoke test gate release completion.
- The smoke test verifies application, catalogue, and model revisions.
- Rollback restores the last verified application image and model revision.

### NFR-006 — Security

Status: In progress

- SSH is restricted to the configured administrator CIDR.
- Only ports 80 and 443 are public.
- Application and metrics ports remain private.
- Containers run as non-root where supported.
- Dependencies, container images, IaC, and committed secrets are scanned.
- GitHub Environment secrets provide OCI credentials; no `.tfvars` value file
  is used.

## 7. Acceptance examples

### AC-001 — Normal recommendation

Given a supported age, 30 minutes, indoor setting, nearby supervision, and
paper plus crayons, when the parent requests ideas, then the response contains
three eligible catalogue activities and all required fields from FR-005.

### AC-002 — Age exclusion

Given the youngest supported age, when ranking runs, then no returned activity
has a higher minimum age regardless of its model score.

### AC-003 — Supervision exclusion

Given `independent` supervision, when an activity requires continuous or nearby
supervision, then that activity is excluded before model inference.

### AC-004 — Model outage

Given the model adapter times out, when eligible activities exist, then the API
returns three deterministically ranked activities, marks fallback mode, records
the fallback reason, and does not return a 5xx response.

### AC-005 — Malformed model output

Given a model response containing an unknown or excluded activity ID, when
output validation runs, then the response is discarded and deterministic
fallback supplies the recommendations.

### AC-006 — No eligible result

Given valid but overly restrictive inputs, when fewer than three activities are
eligible, then the API returns the safe subset and identifies relaxable
non-safety constraints. It never suggests relaxing age or supervision safety.

### AC-007 — Version traceability

Given a deployed release, when `/version` and a recommendation response are
inspected, then the Git SHA, catalogue version, and immutable model revision can
be matched to repository and Hugging Face records.

### AC-008 — No model dependency on paid service

Given all external inference access is unavailable, when the deployed service
starts from its packaged or cached model artifact, then recommendation and
fallback behaviour remains available without incurring API charges.

## 8. Target architecture

```text
Browser
  │ HTTPS
  ▼
OCI security list → host firewall → Caddy
                                      │
                                      ▼
                              FastAPI application
                              ├─ input validation
                              ├─ safety filter
                              ├─ ONNX ranking adapter
                              ├─ deterministic fallback
                              └─ versioned activity catalogue
                                      │
                                      ├─ metrics → lightweight remote collector
                                      └─ model artifact ← Hugging Face Hub
```

E2 Micro runs the minimum viable profile. A1 permits additional memory,
separate inference process experiments, and controlled canary deployment, but
the product shall not depend on A1 availability.

The Hugging Face repository is the model registry and portfolio evidence. OCI
is the model-serving runtime. This distinction must be explained accurately in
the README and interviews.

## 9. Architecture decisions

### ADR-001 — Docker Compose before Kubernetes

Decision: use Docker Compose on a single VM.

Reason: Kubernetes on one constrained VM adds control-plane cost without
providing host redundancy. Compose keeps inference reliability, release safety,
resource limits, and observability visible. Kubernetes may be added only as a
separately justified learning environment.

### ADR-002 — Curated catalogue plus ranking model

Decision: the model ranks reviewed activities instead of freely inventing
activities.

Reason: this creates enforceable safety boundaries, reproducible evaluation,
clear fallback behaviour, and a measurable model-serving workload.

### ADR-003 — Hugging Face Hub, not paid hosted inference

Decision: publish model artifacts and model cards to Hugging Face Hub while
serving inference on OCI.

Reason: free hosted inference credits are not sufficient for a dependable
public demo. The Hub still provides versioning, provenance, reproducibility,
and visible ML portfolio evidence.

### ADR-004 — Stateless MVP

Decision: store the initial reviewed catalogue in version-controlled data and
avoid Postgres and Redis.

Reason: the MVP has no account or transactional requirement. Adding databases
would consume scarce memory without improving the primary user journey.

## 10. Data sourcing and model-training specification

### 10.1 Governing principle

Publicly visible content is not automatically licensed for reuse or model
training. The project uses search to discover ideas, then creates an original,
structured, human-reviewed activity catalogue. It does not train on copied
social posts, captions, comments, photographs, audio, or video.

This is both a legal/safety boundary and an engineering decision: the model's
job is to rank reviewed activities, not reproduce source material or generate
unbounded instructions.

### 10.2 Permitted discovery sources

| Source | MVP policy | Data that may be retained |
|---|---|---|
| Original Zippy Kiddo ideas | Preferred | Complete original activity and review record |
| Public-domain or compatible open-licence sources | Preferred | Adapted activity, source URL, author, licence, access date |
| YouTube | Official API search and manual review | Video ID/URL, title, channel, access date, reviewer notes written in original language |
| Google Search | Manual discovery only | Destination URL and provenance; not copied search-result text |
| Instagram | Manual inspiration only | Source URL and original reviewer notes; no post media, caption, comments, or account data |
| Facebook | Manual inspiration from public pages only | Source URL and original reviewer notes; no post media, comments, reactions, or account data |
| Parent contribution | Deferred | Only deliberately submitted activity content under explicit reuse terms |

The pipeline shall not scrape YouTube, Google, Facebook, or Instagram. It shall
not download YouTube video/audio, scrape captions, or ingest comments. The
official YouTube Data API may be used to find candidate videos and retain
permitted discovery metadata. Instagram and Facebook automation is excluded
from the MVP because their access and permission model is not required to prove
the product.

Google Custom Search JSON API is not a dependency because it is closed to new
customers and scheduled for discontinuation. Research remains a bounded manual
curation task for the initial catalogue.

### 10.3 Research-to-catalogue workflow

```text
search/discovery
  → provenance record
  → reviewer writes an original structured activity
  → safety and age review
  → duplicate/originality check
  → second review or explicit approval
  → approved catalogue
```

Discovery records and approved activities shall be separate datasets. A URL in
the discovery queue does not make its content eligible for training.

### 10.4 Ranking dataset

The training dataset contains structured scenarios and relevance judgments,
not raw source content. Each row shall contain:

```json
{
  "scenario": {
    "age": 5,
    "duration_minutes": 30,
    "setting": "indoor",
    "supervision": "nearby",
    "energy": "calm",
    "materials": ["paper", "crayons"]
  },
  "activity_id": "draw-a-treasure-map",
  "relevance": 3,
  "safety_eligible": true,
  "label_source": "human-review",
  "dataset_version": "v1"
}
```

Relevance labels are:

- `0`: unsuitable match;
- `1`: weak match;
- `2`: good match;
- `3`: excellent match.

The hard safety filter creates eligibility. The ranking label describes quality
only among candidates and cannot make an excluded activity eligible.

### 10.5 Dataset construction

The initial dataset shall be built as follows:

1. Write and approve at least 30 catalogue activities.
2. Create 100–200 realistic, non-identifying parent scenarios spanning the
   supported ages and constraints.
3. Run hard rules to identify eligible candidates.
4. Have a human assign relevance labels to candidate pairs.
5. Include difficult but safe alternatives as hard negatives.
6. Version the catalogue, scenarios, labels, and reviewer rubric together.
7. Split training, validation, and test data by activity ID, with an additional
   held-out scenario set, to reduce memorisation and leakage.

Synthetic scenarios may improve constraint coverage, but synthetic relevance
labels shall not replace the human-reviewed evaluation set. No model-generated
activity enters the catalogue automatically.

### 10.6 Baseline before fine-tuning

The first production candidate shall use:

1. hard eligibility and safety rules;
2. deterministic weighted ranking as the operational fallback; and
3. a pretrained `sentence-transformers/all-MiniLM-L6-v2` embedding model as the
   initial ML ranking candidate.

The chosen starting model has an Apache-2.0 licence. Its exact Hugging Face
revision shall be recorded. Catalogue activity embeddings shall be computed
ahead of time; only the small scenario query requires runtime encoding.

Fine-tuning is allowed only after the baseline evaluation and sufficient
human-labelled pairs exist. A fine-tuned model must outperform the deterministic
and pretrained baselines on the frozen test set without weakening any safety
test.

### 10.7 Free training environment

Training and experiment notebooks shall run on Kaggle's free environment. GPU
use is optional for the baseline and may be enabled for fine-tuning within
Kaggle's current free quota. No paid Kaggle or cloud integration may be enabled.

Every training run intended for comparison shall record:

- source commit and dataset version;
- base model and immutable revision;
- random seed and data split IDs;
- dependencies and training configuration;
- evaluation metrics;
- output artifact checksum;
- elapsed training time and hardware type.

### 10.8 Evaluation and promotion

A candidate model may be promoted only when:

- all prohibited-activity fixtures remain excluded by hard rules;
- ranking quality beats the deterministic baseline on the frozen test set;
- no test activity or near-duplicate leaked into training;
- inference latency and peak memory meet the E2 budget;
- invalid model output activates fallback correctly;
- licence and model-card documentation are complete;
- a human approves the evaluation report.

The initial ranking report shall include at least Recall@3, nDCG@3, inference
latency percentiles, peak resident memory, fallback rate under injected
failures, and results sliced by approved age band.

### 10.9 Model packaging and publication

The approved model shall be exported to ONNX and validated against the source
model within a documented numerical tolerance. The following shall be
published to a Zippy Kiddo Hugging Face model repository:

- ONNX model and tokenizer assets;
- model card;
- base-model attribution and licence;
- intended and prohibited uses;
- supported language and age range;
- training-data description without restricted source content;
- evaluation metrics and known limitations;
- catalogue compatibility version;
- artifact checksums.

Deployment shall pin an immutable Hugging Face commit revision or verified
artifact digest. OCI downloads or packages that artifact and performs inference
locally; paid Hugging Face inference is not used.

### 10.10 Retraining trigger

Retraining is not scheduled merely to claim continuous training. A new training
run is justified when sufficient reviewed feedback exists, catalogue semantics
change materially, evaluation reveals a ranking weakness, or monitored
recommendation distributions indicate a reviewed issue. Every new model must
pass the same promotion gate and support rollback to the prior revision.

## 11. Verification strategy

### Unit tests

- input schema and boundary values;
- every safety exclusion rule;
- deterministic scoring and tie-breaking;
- model-output validation;
- fallback reason mapping;
- version metadata.

### Contract tests

- API response schema;
- catalogue schema and unique stable IDs;
- model input/output contract;
- `/healthz`, `/readyz`, `/version`, and `/metrics` behaviour.

### Model evaluation

- fixed ranking fixtures reviewed by a human;
- safety-filter recall must be 100% on prohibited fixtures;
- ranking quality compared with deterministic baseline;
- inference latency and peak memory on E2-class CPU constraints;
- artifact checksum and revision reproducibility.

### Integration and resilience tests

- service starts with the pinned model artifact;
- unavailable Hugging Face Hub after initial deployment;
- corrupt or missing model artifact;
- inference timeout and invalid output;
- container restart;
- memory pressure within safe test bounds;
- rollback restores known application and model versions.

### CI gates

```text
format/lint
  → unit and contract tests
  → catalogue and safety evaluation
  → model evaluation threshold
  → IaC and secret scans
  → container build
  → container vulnerability scan
  → immutable image publication
  → deployment
  → readiness and external smoke test
```

## 12. Delivery increments

### Increment 0 — Specification and infrastructure baseline

Exit criteria:

- product questions required for FR-001 are resolved;
- E2 and A1 Terraform definitions are validated in CI;
- E2 deployment can succeed independently of A1 capacity;
- workflow accepts only approved free compute shapes;
- no saved Terraform plan is uploaded;
- infrastructure README matches the workflow.

### Increment 1 — Safe deterministic MVP

Exit criteria:

- reviewed catalogue with coverage across supported ages;
- input UI and recommendation API;
- safety filter and deterministic ranking;
- health, readiness, and version endpoints;
- unit, contract, and acceptance tests for AC-001 through AC-006;
- local container run documented.

### Increment 2 — Model registry and inference

Exit criteria:

- baseline and candidate model evaluations are reproducible;
- approved artifact and model card published on Hugging Face Hub;
- immutable revision is deployed on OCI;
- output validation and fallback are verified;
- model latency and memory measurements satisfy NFR-002 and NFR-003.

### Increment 3 — AI SRE operations

Exit criteria:

- metrics dashboard covers application and model signals;
- availability, latency, and fallback alerts are defined;
- immutable CI/CD deployment and rollback are demonstrated;
- controlled model timeout and corrupt-artifact drills are recorded;
- one blameless postmortem includes detection, diagnosis, recovery, and
  prevention evidence.

### Increment 4 — Interview package

Exit criteria:

- public README explains the user problem and architecture trade-offs;
- live demo and health/version evidence are accessible when free resources are
  available;
- architecture diagram, dashboard, evaluation report, runbook, and postmortem
  are linked;
- a five-minute demo script and concise STAR project story are rehearsable;
- limitations accurately state single-VM, free-capacity, and model boundaries.

## 13. Interview evidence map

| Interview topic | Evidence to produce |
|---|---|
| AI/ML systems | Model card, evaluation dataset, baseline comparison, immutable revision |
| Model serving | ONNX runtime, resource measurements, timeout, validation, fallback |
| SRE | SLOs, dashboard, alerts, failure drill, postmortem, rollback |
| DevOps | Terraform, CI gates, immutable images, environment secrets, deployment evidence |
| DevSecOps | Safety tests, secret scan, IaC scan, dependency and image scan |
| Cost engineering | E2-first profile, A1 optionality, no paid inference, measured resource limits |
| Architecture judgment | Curated catalogue, stateless MVP, Compose-over-Kubernetes ADRs |

## 14. Definition of done

A requirement is `Verified` only when:

- its acceptance criteria pass;
- relevant automated tests are committed;
- logs and metrics contain no prohibited data;
- error and fallback paths have been exercised;
- documentation reflects actual behaviour;
- evidence can be shown from a reproducible commit or immutable artifact;
- no paid service is required.

## 15. Open questions

### OQ-001 — Age bands — blocking catalogue coverage and aggregate metrics

Confirmed range: ages 3 through 12, inclusive.  
Required decision: the age bands used for catalogue coverage, safety fixtures,
and privacy-preserving aggregate metrics.

### OQ-002 — Default supervision policy — blocking catalogue approval

Should age 3–5 recommendations always require at least nearby supervision, even
when an activity would otherwise be tagged independent?

### OQ-003 — Initial language — blocking final UI copy

Should the MVP be English only, or should it include another language from the
first release?

### OQ-004 — OCI quota confirmation — blocking first infrastructure apply

Confirm that the existing `solo-sre-project` uses one E2 Micro and that the OCI
Console still marks a second E2 Micro and the planned block storage as Always
Free-eligible.

## 16. Current implementation gaps

- GAP-001: Terraform and workflow changes have not yet run through GitHub CI.
- GAP-002: Verify in GitHub Actions that an A1 `Out of host capacity` response
  produces a warning after E2 deployment, while other A1 errors still fail the
  workflow.
- GAP-003: `allowed_ssh_cidr` still defaults to a value in source instead of a
  GitHub Environment secret or variable.
- GAP-004: No application, catalogue, model, or evaluation suite exists yet.
- GAP-005: The age-band grouping and supervision policy are unresolved.
- GAP-006: The provenance record, reviewer rubric, and training-dataset schema
  described in Section 10 have not yet been implemented.
