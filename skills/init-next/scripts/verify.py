#!/usr/bin/env python3
"""Verify a generated Next.js scaffold with logs, timings and owned-process cleanup."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from html.parser import HTMLParser
from http.client import HTTPException
from http.cookiejar import CookieJar
import json
import os
from pathlib import Path
import secrets
import signal
import socket
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import HTTPCookieProcessor, Request, build_opener, urlopen
import uuid


STAGES = ("install", "checks", "build", "dev", "docker")
# Better Auth compares the Origin header with BETTER_AUTH_URL, not with the published port.
ORIGIN = "http://localhost:3000"
EMAIL = "verify@example.com"


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
    output = output / (time.strftime("run-%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6])
    output.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["NEXT_TELEMETRY_DISABLED"] = "1"
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

    auth = {}

    def psql(statement):
        return ["docker", "compose", "exec", "-T", "postgres", "psql", "-U", "app", "-d", "app", "-v", "ON_ERROR_STOP=1", "-c", statement]

    def prepare_auth():
        # Every page reads a database session, so both servers need a migrated database and an administrator.
        if auth:
            return auth
        run("compose-config", ["docker", "compose", "config", "--quiet"])
        # Reuse healthy running PostgreSQL; only stop a container started here.
        existing = run("compose-existing", ["docker", "compose", "ps", "--status", "running", "-q", "postgres"]).strip()
        if not existing:
            try:
                run("postgres-start", ["docker", "compose", "up", "-d", "--wait", "--wait-timeout", "120", "postgres"], extra_env={"POSTGRES_PORT": str(free_port())})
            finally:
                auth["owned"] = run("postgres-id", ["docker", "compose", "ps", "-a", "-q", "postgres"]).strip()
        else:
            health = run("postgres-health", ["docker", "inspect", "--format", "{{.State.Health.Status}}", existing]).strip()
            if health != "healthy":
                raise RuntimeError(f"Existing PostgreSQL is {health}; left unchanged")
        auth["postgres"] = existing or auth["owned"]
        # A throwaway database: the development data and migration history stay untouched.
        address = run("postgres-port", ["docker", "compose", "port", "postgres", "5432"]).strip()
        database = "verify_" + uuid.uuid4().hex[:12]
        run("database-create", psql(f'CREATE DATABASE "{database}"'))
        auth["database"] = database
        auth["secrets"] = {"BETTER_AUTH_URL": ORIGIN, "BETTER_AUTH_SECRET": secrets.token_urlsafe(32)}
        auth["host_env"] = auth["secrets"] | {"DATABASE_URL": f"postgresql://app:local-password@{address}/{database}"}
        run("migrate-deploy", [args.pnpm, "run", "db:deploy"], extra_env=auth["host_env"])
        auth["password"] = secrets.token_urlsafe(18)
        run("create-admin", [args.pnpm, "run", "auth:create-admin", "--email", EMAIL, "--name", "Verify", "--role", "admin", "--no-email-verified", "--password", auth["password"]], extra_env=auth["host_env"])
        return auth

    def cleanup_auth():
        # Exact names/IDs only; never prune or remove project data volumes.
        if "database" in auth:
            subprocess.run(psql(f'DROP DATABASE IF EXISTS "{auth["database"]}" WITH (FORCE)'), cwd=target, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
        if auth.get("owned"):
            subprocess.run(["docker", "stop", auth["owned"]], cwd=target, env=env, stdout=subprocess.DEVNULL, timeout=30)

    def dev():
        host_env = prepare_auth()["host_env"]
        port = free_port()
        with (output / "dev-server.log").open("w") as stream:
            with process([args.pnpm, "run", "dev", "--hostname", "127.0.0.1", "--port", str(port)], target, env | host_env, stream) as child:
                check_http(f"http://127.0.0.1:{port}/sign-in", child)

    def docker():
        prepare_auth()
        container = "init-next-verify-" + uuid.uuid4().hex[:12]
        image = container + ":local"
        try:
            run("docker-build", ["docker", "build", "-t", image, "."], timeout=1200)
            # Join the Compose network: PostgreSQL is published on the host loopback only.
            network = run("postgres-network", ["docker", "inspect", "--format", "{{range $name, $_ := .NetworkSettings.Networks}}{{$name}}{{end}}", auth["postgres"]]).strip()
            app_env = auth["secrets"] | {"DATABASE_URL": f"postgresql://app:local-password@postgres:5432/{auth['database']}"}
            run("docker-start", ["docker", "run", "-d", "--init", "--name", container, "--network", network, "-p", "127.0.0.1::3000", *(part for key, value in app_env.items() for part in ("-e", f"{key}={value}")), image])
            binding = json.loads(run("docker-port", ["docker", "inspect", "--format", '{{json (index .NetworkSettings.Ports "3000/tcp")}}', container]))
            base = f"http://127.0.0.1:{binding[0]['HostPort']}"
            check_http(base + "/sign-in")
            check_auth(base, auth["password"])
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
            for command in (["docker", "rm", "-f", container], ["docker", "image", "rm", image]):
                subprocess.run(command, cwd=target, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)

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
        cleanup_auth()
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


def check_auth(base, password):
    opener = build_opener(HTTPCookieProcessor(CookieJar()))

    def post(path, body):
        request = Request(base + path, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "Origin": ORIGIN})
        try:
            with opener.open(request, timeout=15) as response:
                return response.status
        except HTTPError as error:
            return error.code

    def landing(path):
        with opener.open(base + path, timeout=15) as response:
            return response.url.removeprefix(base)

    def home_has_navbar():
        with opener.open(base + "/", timeout=15) as response:
            return "mantine-AppShell-navbar" in response.read().decode()

    checks = (
        ("Home must redirect to sign-in without a session", lambda: landing("/") == "/sign-in"),
        ("Public sign-up must be disabled", lambda: post("/api/auth/sign-up/email", {"email": "new@example.com", "password": password, "name": "New"}) == 400),
        ("A wrong password must be rejected", lambda: post("/api/auth/sign-in/email", {"email": EMAIL, "password": password + "x"}) == 401),
        ("The administrator must be able to sign in", lambda: post("/api/auth/sign-in/email", {"email": EMAIL, "password": password}) == 200),
        ("Home must render inside the app layout with a session", lambda: landing("/") == "/" and home_has_navbar()),
        ("Sign-in must redirect to home with a session", lambda: landing("/sign-in") == "/"),
        ("Sign-out must end the session", lambda: post("/api/auth/sign-out", {}) == 200 and landing("/") == "/sign-in"),
    )
    for message, passed in checks:
        if not passed():
            raise RuntimeError(message)


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
    for path, ignored in ((".env", True), (".env.example", False), ("messages/ja.d.json.ts", True), ("src/prisma/generated/client.ts", True)):
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
