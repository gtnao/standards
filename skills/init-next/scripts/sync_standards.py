#!/usr/bin/env python3
"""Bundle repository standards for standalone skill distribution."""

import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    skill = Path(__file__).resolve().parent.parent
    source = skill.parent.parent / "docs"
    if not (source / "nextjs/README.md").is_file():
        parser.error("Run this maintainer script in the standards repository.")
    target = skill / "assets/template/docs/standards"
    expected = {p.relative_to(source): p.read_text().replace(
        "../../skills/init-ts-cli/SKILL.md",
        "https://github.com/gtnao/standards/blob/main/skills/init-ts-cli/SKILL.md",
    ).encode() for p in source.rglob("*.md")}
    actual = {p.relative_to(target): p.read_bytes() for p in target.rglob("*.md")}
    changed = sorted(path for path in expected.keys() | actual.keys()
                     if expected.get(path) != actual.get(path))
    if args.check:
        if changed:
            parser.exit(1, "Bundled standards differ: " + ", ".join(map(str, changed)) + "\n")
        print("Bundled standards match docs/.")
        return
    for path in changed:
        destination = target / path
        if path not in expected:
            destination.unlink()
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(expected[path])
    print(f"Synced {len(changed)} documents.")


if __name__ == "__main__":
    main()
