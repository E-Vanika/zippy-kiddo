# Candidate idea discovery

Gemini Search grounding can discover candidate screen-free activity concepts.
The daily workflow writes only to `data/candidate-ideas.json`; it cannot change
the live catalogue or train a model.

## Required review

Every candidate has `review_status: pending`. Before it reaches the queue, the
workflow automatically requires a grounded source, validates the schema,
age/time bounds and known materials, rejects high-risk keywords, and filters
near-duplicate titles. Before manually promoting a passed candidate to
`zippy_kiddo/data/activities.json`, check its source URLs, original wording,
age range, materials, supervision, and safety note. Only reviewed catalogue
entries can be recommended or included in Kaggle training.

## Enable daily discovery

1. Confirm that Gemini Search grounding is permitted by your plan at an
   acceptable cost. It is not assumed to be free.
2. In GitHub, open **Settings → Secrets and variables → Actions → Variables**.
3. Add `ENABLE_GEMINI_DAILY_DISCOVERY` with the value `true`.
4. Optionally add `GEMINI_DISCOVERY_MODEL`; the default is `gemini-2.5-flash`.
5. Keep `GEMINI_API_KEY` as a repository secret.

The schedule is 07:00 Asia/Kolkata (01:30 UTC). Use **Actions → Daily
Candidate Idea Discovery → Run workflow** first to validate the credential and
inspect the review queue.

## Training after review

After promoting enough reviewed candidates into the catalogue, run **Model
Training**. The existing pipeline trains in Kaggle when available, publishes an
immutable Hugging Face artifact, then deploys through the normal application
pipeline.

## Weekly maintainer routine

No daily work is required. Once a week:

1. Open GitHub **Actions → Daily Candidate Idea Discovery** and inspect the
   latest `data/candidate-ideas.json` artifact or commit.
2. Consider only candidates with
   `automated_validation.status: "passed"`.
3. Check the source URLs, original wording, age range, materials, supervision,
   and safety note for the five to ten most useful ideas.
4. Move approved candidates into `zippy_kiddo/data/activities.json` and push
   the change.

The catalogue change automatically starts the model-training workflow. It runs
Kaggle training when available (with the GitHub Actions fallback), publishes a
versioned Hugging Face artifact, updates the pinned model revision, then builds,
security-scans, and deploys the application through the normal CI/CD pipeline.
