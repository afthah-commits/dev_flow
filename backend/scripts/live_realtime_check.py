#!/usr/bin/env python3
"""Phase 31 — LIVE realtime validation (production topology).

Starts the real ASGI app under uvicorn on a throwaway database, opens a real
WebSocket client, then triggers broadcasts the same way production does:

1. broadcast_workflow_event() called from a SYNC THREAD (as FastAPI sync
   endpoints execute on the threadpool).
2. A direct cross-thread broadcast (as the job scheduler does).

Asserts the connected client actually receives both messages. This exercises
the cross-event-loop path that in-process TestClient tests cannot reach.

Usage:
    cd backend
    python scripts/live_realtime_check.py

Exit codes: 0 = delivered, 1 = not delivered, 2 = setup error.
"""
import os
import sys
import threading
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

LIVE_DB = os.path.join(BASE, "live_realtime_check.db")
if os.path.exists(LIVE_DB):
    os.remove(LIVE_DB)
os.environ["DATABASE_URL"] = f"sqlite:///{LIVE_DB}"

import httpx  # noqa: E402
import uvicorn  # noqa: E402
import websocket  # noqa: E402  (websocket-client)

from sqlalchemy import create_engine  # noqa: E402
from app.db.base import Base  # noqa: E402

engine = create_engine(os.environ["DATABASE_URL"])
Base.metadata.create_all(bind=engine)

from app.main import app  # noqa: E402

PORT = 8124
BASE_URL = f"http://127.0.0.1:{PORT}"


def run_server():
    config = uvicorn.Config(app, host="127.0.0.1", port=PORT, log_level="warning")
    server = uvicorn.Server(config)
    server.run()


def main() -> int:
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Wait for the server to accept connections
    deadline = time.time() + 20
    client = httpx.Client(base_url=BASE_URL, timeout=2)
    ready = False
    last_err = None
    while time.time() < deadline:
        try:
            client.get("/docs")
            ready = True
            break
        except Exception as exc:
            last_err = f"{type(exc).__name__}: {exc}"
            time.sleep(0.3)
    if not ready:
        print(f"ERROR: server did not start ({last_err})")
        return 2

    # Seed a user + org via the real API
    email = "live_rt@example.com"
    client.post("/api/v1/auth/register", json={"name": "Live", "email": email, "password": "password123"})
    token = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"}).json()["access_token"]
    auth = {"Authorization": f"Bearer {token}"}
    org = client.post("/api/v1/organizations", json={"name": "Live RT Org"}, headers=auth).json()
    org_id = org["id"]

    # Real WebSocket connection (what a browser would open)
    received = []
    def on_message(_ws, message):
        received.append(message)

    ws = websocket.WebSocketApp(
        f"ws://127.0.0.1:{PORT}/api/v1/realtime/ws?token={token}&org_id={org_id}",
        on_message=on_message,
    )
    ws_thread = threading.Thread(target=ws.run_forever, daemon=True)
    ws_thread.start()
    time.sleep(1.5)  # let the handshake complete

    # 1) Production sync-endpoint path: called from a thread WITHOUT a loop
    from app.services.workflow_studio import broadcast_workflow_event
    from uuid import UUID

    t = threading.Thread(
        target=broadcast_workflow_event,
        args=(UUID(str(org_id)), "workflow.published", {"workflow_id": "live-1"}),
    )
    t.start()
    t.join(timeout=10)

    got_workflow = any("workflow.published" in m for m in received)
    print(f"workflow.* via sync thread (broadcast_workflow_event): "
          f"{'DELIVERED' if got_workflow else 'NOT DELIVERED'}")

    # 2) Scheduler-style path: run_until_complete on an external thread
    def scheduler_style():
        import asyncio
        from app.websockets.manager import manager
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(manager.broadcast_to_org(
                UUID(str(org_id)), {"type": "job.updated", "payload": {"job_id": "live-2"}}))
        finally:
            loop.close()

    t2 = threading.Thread(target=scheduler_style)
    t2.start()
    t2.join(timeout=10)
    time.sleep(0.5)

    got_job = any("job.updated" in m for m in received)
    print(f"job.updated via external loop (scheduler style):      "
          f"{'DELIVERED' if got_job else 'NOT DELIVERED'}")

    ws.close()
    try:
        os.remove(LIVE_DB)
    except OSError:
        pass

    if got_workflow and got_job:
        print("RESULT: PASS — cross-thread realtime delivery works")
        return 0
    print("RESULT: FAIL — realtime events were not delivered to the client")
    return 1


if __name__ == "__main__":
    sys.exit(main())
