#!/usr/bin/env python3
"""Generate the reviewed scaffold and prepare dependencies and Git hooks."""

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path)
    parser.add_argument("--name", help="Package name; defaults to the target directory name")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--files-only", action="store_true", help="Copy files without installing tools or initializing Git")
    mode.add_argument("--prepare-only", action="store_true", help="Prepare an existing scaffold without rewriting files")
    mode.add_argument("--prepare", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--cache-dir", type=Path, help="Tool caches within the authorized workspace (required unless --files-only)")
    parser.add_argument("--pnpm", default="pnpm")
    parser.add_argument("--aqua", default="aqua")
    args = parser.parse_args()
    target = args.target.absolute()
    name = args.name or target.name
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", name):
        parser.error("Use a lowercase unscoped package name")
    if any(p.is_symlink() for p in (target, *target.parents)):
        parser.error("Target must not traverse symlinks")
    if args.prepare_only:
        for required in ("package.json", "pnpm-lock.yaml", "pnpm-workspace.yaml", "aqua.yaml", "lefthook.yml"):
            if not (target / required).is_file() or (target / required).is_symlink():
                parser.error(f"Expected a generated scaffold: {required}")
        if args.name:
            parser.error("--name cannot be used with --prepare-only")
    if not args.prepare_only and target.exists() and (not target.is_dir() or any(p.name != ".git" for p in target.iterdir())):
        parser.error("Target must be empty except for an optional .git directory")
    if (target / ".git").is_symlink() or ((target / ".git").exists() and not (target / ".git").is_dir()):
        parser.error("Use a standalone repository, not a linked worktree")
    if not args.files_only and not args.cache_dir:
        parser.error("Preparation requires --cache-dir inside the authorized workspace")
    env = os.environ.copy()
    if not args.files_only:
        for executable in (args.pnpm, args.aqua, "git"):
            if not shutil.which(executable):
                parser.error(f"Required executable not found: {executable}")
        cache = args.cache_dir.resolve()
        if cache == target or target in cache.parents:
            parser.error("Keep tool caches outside the generated project")
        for key, folder in {
            "XDG_CACHE_HOME": "cache", "XDG_DATA_HOME": "data", "XDG_CONFIG_HOME": "config",
            "PNPM_HOME": "pnpm-home", "COREPACK_HOME": "corepack", "npm_config_cache": "npm-cache",
            "AQUA_ROOT_DIR": "aqua",
        }.items():
            env[key] = str(cache / folder)
    template = Path(__file__).resolve().parent.parent / "assets/template"
    if not args.prepare_only:
        target.mkdir(parents=True, exist_ok=True)
        for source in template.rglob("*"):
            if not source.is_file():
                continue
            destination = target / source.relative_to(template)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(source.read_text().replace("__PROJECT_NAME__", name))
        (target / ".env").write_text("")
    if not args.files_only:
        if not (target / ".git").exists():
            subprocess.run(["git", "init", "-b", "main"], cwd=target, env=env, check=True)
        for command in ([args.pnpm, "install", "--frozen-lockfile"], [args.aqua, "install"], [args.aqua, "exec", "--", "lefthook", "install"]):
            subprocess.run(command, cwd=target, env=env, check=True)
    package = json.loads((target / "package.json").read_text())
    print(f"Prepared {target}." if args.prepare_only else f"Generated {target} using the reviewed snapshot ({package['packageManager']}).")
    print("Dependencies and hooks prepared." if not args.files_only else "Files only. Dependencies, hooks and services have not been started.")


if __name__ == "__main__":
    main()
