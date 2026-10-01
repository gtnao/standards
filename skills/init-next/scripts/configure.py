#!/usr/bin/env python3
"""Apply project standards to a fresh create-next-app --skip-install scaffold."""

import argparse
import json
import re
from pathlib import Path


RUNTIME = {
    "next", "react", "react-dom", "@mantine/core", "@mantine/hooks",
    "@tabler/icons-react", "next-intl", "react-hook-form", "@hookform/resolvers", "zod",
}
DEVELOPMENT = {
    "typescript", "@types/node", "@types/react", "@types/react-dom",
    "@biomejs/biome", "babel-plugin-react-compiler", "postcss",
    "postcss-preset-mantine", "postcss-simple-vars", "vitest",
}
GENERATED = {
    "README.md", "tsconfig.json", "biome.json", "next.config.ts",
    "pnpm-workspace.yaml", "src/app/layout.tsx", "src/app/page.tsx",
    "postcss.config.mjs",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path)
    parser.add_argument("--versions", type=Path, required=True)
    args = parser.parse_args()
    target = args.target.resolve()
    skill = Path(__file__).resolve().parent.parent
    template = skill / "assets/template"

    try:
        versions = json.loads(args.versions.read_text())
        package = json.loads((target / "package.json").read_text())
        assert "next" in package.get("dependencies", {}), "Expected a create-next-app project."
        assert (target / "src/app/layout.tsx").is_file(), "Expected the src App Router layout."
        assert (target / "AGENTS.md").is_file(), "Generate AGENTS.md with create-next-app."
        assert "typecheck" not in package.get("scripts", {}), "Expected a fresh scaffold."
        for path in ("node_modules", ".next", "pnpm-lock.yaml", ".env"):
            assert not (target / path).exists(), f"Expected an uninstalled scaffold: {path} exists."
        for group, required in (("dependencies", RUNTIME), ("devDependencies", DEVELOPMENT)):
            pins = versions[group]
            assert required <= pins.keys(), f"Missing {group}: {sorted(required - pins.keys())}"
            assert package.get(group, {}).keys() <= pins.keys(), f"Review newly generated {group} before replacing them."
            for name, version in pins.items():
                assert re.fullmatch(r"\d+\.\d+\.\d+", version), f"Use an exact stable version: {name}"
        for name in ("node", "pnpm", "aquaRegistry", "lefthook", "pinact"):
            assert re.fullmatch(r"\d+\.\d+\.\d+", versions[name]), f"Invalid version: {name}"
        assert versions["dependencies"]["react"] == versions["dependencies"]["react-dom"], "Match React versions."
        assert versions["dependencies"]["@mantine/core"] == versions["dependencies"]["@mantine/hooks"], "Match Mantine versions."
        for name, prefix in (("nodeImage", "node:"), ("postgresImage", "postgres:")):
            assert versions[name].startswith(prefix) and re.fullmatch(r"[\w./:-]+@sha256:[a-f0-9]{64}", versions[name]), f"Pin image tag and digest: {name}"
        assert versions["nodeImage"].startswith(f'node:{versions["node"]}-'), "Match Docker and package.json Node versions."
        for name in ("checkout", "pnpmAction"):
            assert re.fullmatch(r"[a-f0-9]{40}", versions[name]), f"Resolve Action SHA: {name}"
        name = package["name"]
        assert re.fullmatch(r"[a-z0-9][a-z0-9._-]*", name), "Expected an unscoped package name."
        files = {str(p.relative_to(template)): p.read_text() for p in template.rglob("*") if p.is_file()}
        for rel in {*files, "package.json", "AGENTS.md", "CLAUDE.md", ".gitignore", ".env"}:
            path = target / rel
            assert not any(p.is_symlink() for p in [path, *path.parents] if p != target.parent), f"Symlink in output path: {rel}"
            if rel in files and path.exists():
                assert rel in GENERATED, f"Refusing to replace existing file: {rel}"
        agents = (target / "AGENTS.md").read_text()
        assert "## Project standards" not in agents, "Standards are already applied."
    except (AssertionError, KeyError, ValueError, OSError, TypeError) as error:
        parser.error(str(error))

    package.pop("version", None)
    package.update({
        "private": True, "type": "module", "packageManager": f'pnpm@{versions["pnpm"]}',
        "devEngines": {"runtime": {"name": "node", "version": f'^{versions["node"]}', "onFail": "download"}},
        "scripts": {
            "dev": "next dev", "build": "next build", "start": "next start",
            "typecheck": "next typegen && tsc --noEmit",
            "lint": "biome check --error-on-warnings .",
            "lint:fix": "biome check --write --error-on-warnings .",
            "test": "vitest run", "test:watch": "vitest",
        },
        "dependencies": versions["dependencies"], "devDependencies": versions["devDependencies"],
    })
    files["package.json"] = json.dumps(package, indent=2) + "\n"
    biome = json.loads(files["biome.json"])
    biome["$schema"] = f'https://biomejs.dev/schemas/{versions["devDependencies"]["@biomejs/biome"]}/schema.json'
    files["biome.json"] = json.dumps(biome, indent=2) + "\n"
    files["Dockerfile"] = re.sub(r"FROM node:[^ ]+ AS base", f'FROM {versions["nodeImage"]} AS base', files["Dockerfile"]).replace("id=my-app-pnpm", f"id={name}-pnpm")
    files["compose.yaml"] = re.sub(r"image: postgres:\S+", f'image: {versions["postgresImage"]}', files["compose.yaml"])
    files["aqua.yaml"] = f'''registries:
  - type: standard
    ref: v{versions["aquaRegistry"]} # renovate: depName=aquaproj/aqua-registry

packages:
  - name: evilmartians/lefthook@v{versions["lefthook"]}
  - name: suzuki-shunsuke/pinact@v{versions["pinact"]}
'''
    ci = files[".github/workflows/ci.yml"]
    ci = re.sub(r"actions/checkout@[^\n]+", f'actions/checkout@{versions["checkout"]}', ci)
    files[".github/workflows/ci.yml"] = re.sub(r"pnpm/action-setup@[^\n]+", f'pnpm/action-setup@{versions["pnpmAction"]}', ci)
    files["AGENTS.md"] = agents.rstrip() + "\n\n" + (skill / "references/agents-append.md").read_text()
    claude = (target / "CLAUDE.md").read_text() if (target / "CLAUDE.md").exists() else ""
    if "@AGENTS.md" not in claude:
        files["CLAUDE.md"] = claude.rstrip() + "\n\n@AGENTS.md\n" if claude else "@AGENTS.md\n"
    ignore = (target / ".gitignore").read_text() if (target / ".gitignore").exists() else ""
    files[".gitignore"] = ignore.rstrip() + "\n\n.env\n.env.*\n!.env.example\n/messages/*.d.json.ts\n.vitest/\n"
    files[".env"] = ""
    for rel, contents in files.items():
        path = target / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents.replace("__PROJECT_NAME__", name))
    print(f"Configured {target}. Review dependency build scripts before installation.")


if __name__ == "__main__":
    main()
