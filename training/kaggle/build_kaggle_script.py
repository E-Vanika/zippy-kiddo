"""Create a standalone Kaggle script containing the reviewed catalogue."""

import argparse
import json
from pathlib import Path


PLACEHOLDER = "EMBEDDED_CATALOGUE: dict[str, object] | None = None"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--catalogue", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    template = args.template.read_text(encoding="utf-8")
    if PLACEHOLDER not in template:
        raise RuntimeError("Kaggle catalogue placeholder was not found")
    catalogue = json.loads(args.catalogue.read_text(encoding="utf-8"))
    standalone = template.replace(PLACEHOLDER, f"EMBEDDED_CATALOGUE = {catalogue!r}")
    args.output.write_text(standalone, encoding="utf-8")


if __name__ == "__main__":
    main()
