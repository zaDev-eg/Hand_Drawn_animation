"""Check that the login page and the FastAPI backend are wired together.

Run:  python verify_connection.py

The static and in-process checks need no running database. The last section
also checks a live server on http://localhost:8000 when one is running.
"""

import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = "http://localhost:8000"

ENDPOINTS = [
    "/register",
    "/login",
    "/logout",
    "/forgot-password",
    "/reset-password",
]

failures = 0


def check(label, ok, detail=""):
    global failures
    if not ok:
        failures += 1
    print(f"[{'OK  ' if ok else 'FAIL'}] {label}" + (f" -> {detail}" if detail else ""))


def request(path, method="GET", headers=None, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        BASE + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json", **(headers or {})},
    )
    try:
        with urllib.request.urlopen(req, timeout=3) as res:
            return res.status, dict(res.headers), res.read().decode(errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode(errors="replace")


def static_checks():
    print("\n--- static wiring ---")
    html = (ROOT / "frontend" / "login.html").read_text(encoding="utf-8")
    router = (ROOT / "src" / "routers" / "user_router.py").read_text(encoding="utf-8")
    main = (ROOT / "src" / "main.py").read_text(encoding="utf-8")

    for endpoint in ENDPOINTS:
        check(f"page calls {endpoint}", f'api("{endpoint}"' in html)
        check(
            f"backend defines {endpoint}",
            re.search(rf'@router\.post\(\s*"{re.escape(endpoint)}"', router)
            is not None,
        )

    check("page has API base URL", "API_BASE=" in html)
    check("page stores tokens", "hand_drawn_session" in html)
    check("CORS enabled", "CORSMiddleware" in main)
    check("page served at /login", '@app.get("/login"' in main)


def in_process_checks():
    print("\n--- in-process API checks (no DB needed) ---")
    try:
        import src.main as main_module
        from fastapi.testclient import TestClient
    except Exception as exc:
        print(f"[SKIP] backend dependencies are not installed ({exc})")
        print("       run: pip install -r requirements.txt")
        return

    async def noop():
        pass

    # Startup would normally create the DB tables; skip that here.
    main_module.init_db = noop

    from src.database.db_connection import get_session

    class FakeResult:
        def scalars(self):
            return self

        def first(self):
            return None

    class FakeSession:
        async def execute(self, *args, **kwargs):
            return FakeResult()

    async def fake_session():
        yield FakeSession()

    main_module.app.dependency_overrides[get_session] = fake_session
    client = TestClient(main_module.app)

    r = client.get("/")
    check("GET /", r.status_code == 200, str(r.status_code))

    r = client.get("/login")
    check(
        "GET /login serves the page",
        r.status_code == 200 and "text/html" in r.headers.get("content-type", ""),
        str(r.status_code),
    )

    r = client.options(
        "/api/v1/users/login",
        headers={
            "Origin": "null",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,authorization",
        },
    )
    check(
        "CORS allows a file:// page",
        r.status_code < 400
        and r.headers.get("access-control-allow-origin") is not None,
        f"status {r.status_code}, allow-origin={r.headers.get('access-control-allow-origin')}",
    )

    paths = main_module.app.openapi()["paths"]
    for endpoint in ENDPOINTS:
        check(
            f"openapi has POST /api/v1/users{endpoint}",
            "post" in paths.get(f"/api/v1/users{endpoint}", {}),
        )

    r = client.post(
        "/api/v1/users/login",
        json={"email": "nobody@example.com", "password": "wrong-password"},
    )
    check(
        "POST /login reaches auth logic",
        r.status_code == 401 and r.json().get("detail") == "Incorrect email or password",
        f"status {r.status_code}, body {r.text[:100]}",
    )

    r = client.post(
        "/api/v1/users/forgot-password",
        json={"email": "nobody@example.com"},
    )
    check("POST /forgot-password", r.status_code == 200, str(r.status_code))

    r = client.post(
        "/api/v1/users/reset-password",
        json={"token": "bad.token.value", "password": "newpassword1"},
    )
    check(
        "POST /reset-password rejects bad token",
        r.status_code == 400,
        f"status {r.status_code}, body {r.text[:100]}",
    )


def live_server_checks():
    print("\n--- live server ---")
    try:
        request("/")
    except Exception as exc:
        print(f"[SKIP] server is not running on {BASE} ({exc})")
        print("       start it with: uvicorn src.main:app --reload --port 8000")
        return

    status, _, body = request("/")
    check("GET /", status == 200, body[:80])

    status, _, body = request("/openapi.json")
    if status != 200:
        check("GET /openapi.json", False, f"status {status}")
        return
    paths = json.loads(body).get("paths", {})
    for endpoint in ENDPOINTS:
        check(
            f"openapi has /api/v1/users{endpoint}",
            f"/api/v1/users{endpoint}" in paths,
        )


if __name__ == "__main__":
    static_checks()
    in_process_checks()
    live_server_checks()
    print(
        "\nResult:",
        "ALL CHECKS PASSED" if failures == 0 else f"{failures} CHECK(S) FAILED",
    )
    sys.exit(1 if failures else 0)
