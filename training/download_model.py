import hashlib
import json
import os
import shutil
from pathlib import Path

def main() -> None:
    lock_path = Path("model/model-lock.json")
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if lock.get("source") == "repository":
        downloaded = Path("model/model.json")
    else:
        from huggingface_hub import hf_hub_download

        downloaded = Path(
            hf_hub_download(
                repo_id=lock["repo_id"],
                filename=lock["filename"],
                revision=lock["revision"],
                token=os.environ.get("HF_TOKEN"),
            )
        )
    digest = hashlib.sha256(downloaded.read_bytes()).hexdigest()
    if digest != lock["sha256"]:
        raise RuntimeError("downloaded model checksum does not match model lock")

    destination = Path("zippy_kiddo/model")
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(downloaded, destination / "model.json")
    shutil.copyfile(lock_path, destination / "model-lock.json")


if __name__ == "__main__":
    main()
