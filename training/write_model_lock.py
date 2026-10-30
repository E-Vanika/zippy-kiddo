import argparse
import hashlib
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-id", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    metrics = json.loads(args.metrics.read_text(encoding="utf-8"))
    lock = {
        "repo_id": args.repo_id,
        "revision": args.revision,
        "filename": "model.json",
        "sha256": hashlib.sha256(args.model.read_bytes()).hexdigest(),
        "catalogue_version": metrics["catalogue_version"],
        "metrics": {
            "self_retrieval_top1_accuracy": metrics[
                "self_retrieval_top1_accuracy"
            ],
            "vocabulary_size": metrics["vocabulary_size"],
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
