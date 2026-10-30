import json
import os
from pathlib import Path

from huggingface_hub import HfApi


def main() -> None:
    token = os.environ["HF_TOKEN"]
    api = HfApi(token=token)
    owner = api.whoami()["name"]
    requested = os.getenv("HF_MODEL_REPO", "").strip()
    repo_id = requested or f"{owner}/zippy-kiddo-ranker"
    if "/" not in repo_id:
        repo_id = f"{owner}/{repo_id}"

    api.create_repo(repo_id=repo_id, repo_type="model", private=False, exist_ok=True)
    commit = api.upload_folder(
        repo_id=repo_id,
        repo_type="model",
        folder_path=Path("model-output"),
        commit_message="Publish validated Kaggle training artifact",
    )
    print(json.dumps({"repo_id": repo_id, "revision": commit.oid}))


if __name__ == "__main__":
    main()
