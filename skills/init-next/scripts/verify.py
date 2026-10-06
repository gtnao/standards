#!/usr/bin/env python3
"""Verify a generated Next.js scaffold with logs, timings and owned-process cleanup."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from html.parser import HTMLParser
from http.client import HTTPException
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import time
from urllib.error import URLError
from urllib.parse import urljoin
from urllib.request import urlopen
import uuid


STAGES = ("install", "checks", "build", "dev", "docker")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path)
    parser.add_argument("--output", type=Path, required=True, help="Logs directory outside the target, inside the authorized workspace")
    parser.add_argument("--pnpm", default="pnpm", help="pnpm executable (not shell code)")
    parser.add_argument("--only", nargs="+", choices=STAGES, default=list(STAGES))
    args = parser.parse_args()
    target, output = args.target.resolve(), args.output.resolve()
    if not (target / "package.json").is_file():
        parser.error("Target must contain package.json")
    if output == target or target in output.parents:
        parser.error("Keep logs outside the project to avoid lint/build inputs")
    cache_root = output
    output = output / (time.strftime("run-%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6])
    output.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["NEXT_TELEMETRY_DISABLED"] = "1"
    # Keep bootstrap tooling writes within the explicitly selected workspace.
    for key, folder in {
        "XDG_CACHE_HOME": "cache", "XDG_DATA_HOME": "data", "XDG_CONFIG_HOME": "config",
        "PNPM_HOME": "pnpm-home", "COREPACK_HOME": "corepack", "npm_config_cache": "npm-cache",
    }.items():
        env.setdefault(key, str(cache_root / folder))
    results = []

    def run(name, command, timeout=600, extra_env=None):
        log = output / f"{name}.log"
        started = time.monotonic()
        print(f"START {name}", flush=True)
        try:
            with log.open("w") as stream:
                with process(command, target, env | (extra_env or {}), stream) as child:
                    status = child.wait(timeout=timeout)
            if status:
                raise RuntimeError(f"exit {status}; see {log}")
        except Exception as error:
            results.append({"name": name, "status": "failed", "seconds": round(time.monotonic()-started, 2), "log": str(log)})
            raise RuntimeError(f"{name}: {error}") from error
        results.append({"name": name, "status": "passed", "seconds": round(time.monotonic()-started, 2), "log": str(log)})
        print(f"PASS {name} ({results[-1]['seconds']}s)", flush=True)
        return log.read_text()

    def pnpm(name, *command):
        return run(name, [args.pnpm, *command])

    def dev():
        port = free_port()
        with (output / "dev-server.log").open("w") as stream:
            with process([args.pnpm, "run", "dev", "--hostname", "127.0.0.1", "--port", str(port)], target, env, stream) as child:
                check_http(f"http://127.0.0.1:{port}", child)

    def docker():
        run("compose-config", ["docker", "compose", "config", "--quiet"])
        # Reuse healthy running PostgreSQL; only stop a container started here.
        existing = run("compose-existing", ["docker", "compose", "ps", "--status", "running", "-q", "postgres"]).strip()
        owned = None
        container = "init-next-verify-" + uuid.uuid4().hex[:12]
        image = container + ":local"
        try:
            if not existing:
                try:
                    run("postgres-start", ["docker", "compose", "up", "-d", "--wait", "--wait-timeout", "120", "postgres"], extra_env={"POSTGRES_PORT": str(free_port())})
                finally:
                    owned = run("postgres-id", ["docker", "compose", "ps", "-a", "-q", "postgres"]).strip()
            else:
                health = run("postgres-health", ["docker", "inspect", "--format", "{{.State.Health.Status}}", existing]).strip()
                if health != "healthy":
                    raise RuntimeError(f"Existing PostgreSQL is {health}; left unchanged")
            run("docker-build", ["docker", "build", "-t", image, "."], timeout=1200)
            run("docker-start", ["docker", "run", "-d", "--init", "--name", container, "-p", "127.0.0.1::3000", image])
            binding = json.loads(run("docker-port", ["docker", "inspect", "--format", '{{json (index .NetworkSettings.Ports "3000/tcp")}}', container]))
            check_http(f"http://127.0.0.1:{binding[0]['HostPort']}")
            uid = run("runtime-user", ["docker", "exec", container, "id", "-u"]).strip()
            if uid == "0":
                raise RuntimeError("Runtime user is root")
            run("runtime-files", ["docker", "exec", container, "sh", "-c", 'test -w /app/.next && test ! -e /app/.env && test ! -e /app/.env.local && test ! -e /app/.env.production'])
            run("docker-stop", ["docker", "stop", "--time", "10", container])
            code = run("docker-exit", ["docker", "inspect", "--format", "{{.State.ExitCode}}", container]).strip()
            if code not in {"0", "143"}:
                raise RuntimeError(f"Container did not stop gracefully: exit {code}")
        finally:
            with (output / "docker-server.log").open("w") as stream:
                subprocess.run(["docker", "logs", container], cwd=target, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=30)
            # Exact names/IDs only; never prune or remove project data volumes.
            for command in (["docker", "rm", "-f", container], ["docker", "image", "rm", image]):
                subprocess.run(command, cwd=target, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
            if owned:
                subprocess.run(["docker", "stop", owned], cwd=target, env=env, check=True, stdout=subprocess.DEVNULL, timeout=30)

    started = time.monotonic()
    failure = None
    try:
        if "install" in args.only:
            pnpm("frozen-install", "install", "--frozen-lockfile")
        if "checks" in args.only:
            # typecheck and build both generate Next/message types: do not overlap.
            try:
                with translation_probe(target):
                    with ThreadPoolExecutor(max_workers=3) as pool:
                        jobs = [pool.submit(pnpm, name, "run", name) for name in ("lint", "typecheck", "test")]
                        failures = []
                        for job in jobs:
                            try:
                                job.result()
                            except Exception as error:
                                failures.append(str(error))
                        if failures:
                            raise RuntimeError("; ".join(failures))
            finally:
                pnpm("restore-message-types", "exec", "next", "typegen")
            check_git(target, env)
        if "build" in args.only:
            pnpm("build", "run", "build")
        for name, operation in (("dev", dev), ("docker", docker)):
            if name not in args.only:
                continue
            begin = time.monotonic()
            print(f"START {name}", flush=True)
            try:
                operation()
            except Exception:
                results.append({"name": name, "status": "failed", "seconds": round(time.monotonic()-begin, 2)})
                raise
            results.append({"name": name, "status": "passed", "seconds": round(time.monotonic()-begin, 2)})
            print(f"PASS {name} ({results[-1]['seconds']}s)", flush=True)
    except (Exception, KeyboardInterrupt) as error:
        failure = str(error) or "Interrupted"
    finally:
        report = {"target": str(target), "stages": args.only, "seconds": round(time.monotonic()-started, 2), "results": results, "error": failure}
        (output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"{'FAIL' if failure else 'PASS'}: {report['seconds']}s; report: {output / 'summary.json'}", flush=True)
    if failure:
        raise SystemExit(failure)


@contextmanager
def process(command, cwd, env, stream):
    child = subprocess.Popen(command, cwd=cwd, env=env, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        yield child
    finally:
        try:
            os.killpg(child.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait()


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def check_http(base, child=None):
    deadline = time.monotonic() + 120
    while True:
        if child and child.poll() is not None:
            raise RuntimeError("Dev server exited; see dev-server.log")
        try:
            with urlopen(base, timeout=5) as response:
                html = response.read().decode()
            break
        except (URLError, TimeoutError, ConnectionError, HTTPException):
            if time.monotonic() >= deadline:
                raise RuntimeError(f"HTTP readiness timeout: {base}") from None
            time.sleep(0.5)
    parser = Assets()
    parser.feed(html)
    if not parser.japanese or "mantine-" not in html:
        raise RuntimeError("Expected Japanese HTML and Mantine markup")
    if not any('.js' in path for path in parser.paths) or not any('.css' in path for path in parser.paths):
        raise RuntimeError("Expected Next.js JS and CSS assets")
    for path in parser.paths:
        with urlopen(urljoin(base, path), timeout=15) as response:
            if response.status != 200:
                raise RuntimeError(f"Asset request failed: {path}")


class Assets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths = set()
        self.japanese = False

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "html":
            self.japanese = values.get("lang") == "ja"
        for attr in ("src", "href"):
            path = values.get(attr, "")
            if path.startswith("/_next/static/"):
                self.paths.add(path)


@contextmanager
def translation_probe(target):
    messages = target / "messages/ja.json"
    original = messages.read_bytes()
    data = json.loads(original)
    key = "scaffoldProbe" + uuid.uuid4().hex[:8]
    data[key] = {"message": "{value}"}
    probe = target / "src/i18n" / ("verify-messages-" + uuid.uuid4().hex + ".tsx")
    try:
        messages.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        probe.write_text('''import { useTranslations } from "next-intl";

export function VerifyMessages() {
  const translate = useTranslations();
  // @ts-expect-error Unknown translation keys must be rejected.
  translate("INVALID_KEY");
  // @ts-expect-error Required interpolation arguments must be rejected.
  translate("PROBE_KEY.message");
  return translate("PROBE_KEY.message", { value: "ok" });
}
'''.replace("INVALID_KEY", key + "Missing").replace("PROBE_KEY", key))
        yield
    finally:
        messages.write_bytes(original)
        probe.unlink(missing_ok=True)


def check_git(target, env):
    def git(*args):
        return subprocess.run(["git", *args], cwd=target, env=env, capture_output=True, text=True)
    if git("rev-parse", "--show-toplevel").stdout.strip() != str(target):
        raise RuntimeError("Initialize Git in the target; do not use a parent repository")
    for path, ignored in ((".env", True), (".env.example", False), ("messages/ja.d.json.ts", True)):
        result = git("check-ignore", "--no-index", path)
        if result.returncode not in {0, 1} or (result.returncode == 0) != ignored:
            raise RuntimeError(f"Unexpected Git ignore policy: {path}")
    result = git("rev-parse", "--git-path", "hooks/pre-commit")
    hook = Path(result.stdout.strip())
    if not hook.is_absolute():
        hook = target / hook
    if result.returncode or not hook.is_file() or not os.access(hook, os.X_OK) or "lefthook" not in hook.read_text():
        raise RuntimeError("Executable Lefthook pre-commit hook is missing")


if __name__ == "__main__":
    main()
