#!/usr/bin/env python3
"""Copy the CLI template into an empty project directory."""

import argparse
import re
import shutil
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path)
    args = parser.parse_args()
    target = args.target.resolve()
    template = Path(__file__).resolve().parent.parent / "assets" / "template"

    if target.exists() and not target.is_dir():
        parser.error("The target must be a directory.")
    if target.exists() and any(p.name != ".git" for p in target.iterdir()):
        parser.error("The target must be empty except for an optional .git entry.")

    name = re.sub(r"[^a-z0-9._-]+", "-", target.name.lower()).lstrip("._-")
    if not name or len(name) > 214:
        parser.error("The directory name cannot be converted to a valid package name.")

    target.mkdir(parents=True, exist_ok=True)
    shutil.copytree(template, target, dirs_exist_ok=True)
    for relative in ("package.json", "README.md", "src/entrypoints/cli/index.ts"):
        path = target / relative
        path.write_text(path.read_text().replace("__PROJECT_NAME__", name))
    (target / ".env").touch()
    print(f"Created {target}")


if __name__ == "__main__":
    main()
