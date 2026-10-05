"""Phase 31 — realtime WebSocket stability, isolation and event delivery.

Two layers are covered:

1. ConnectionManager unit tests (async logic driven through asyncio.run with
   loop-agnostic fake sockets): org isolation, personal-message targeting,
   single delivery per broadcast, disconnect cleanup.
2. Endpoint integration tests over the real /api/v1/realtime/ws handshake:
   token authentication, membership enforcement (close 1008), presence
   broadcast, and the workflow.* event helper reaching exactly one org.
"""
import asyncio
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect

from app.websockets.manager import ConnectionManager, manager
from app.services.workflow_studio import broadcast_workflow_event


class FakeWebSocket:
    """Loop-agnostic socket stand-in: records what the server would send."""

    def __init__(self, name: str = "ws"):
        self.name = name
        self.accepted = False
        self.closed = False
        self.messages: list = []

    async def accept(self):
        self.accepted = True

    async def send_json(self, message):
        self.messages.append(message)

    async def close(self, code: int = 1000):
        self.closed = True


def _connect(m: ConnectionManager, ws: FakeWebSocket, org_id, user_id=None):
    asyncio.run(m.connect(ws, org_id, user_id or uuid4()))


# ---------------------------------------------------------------------------
# ConnectionManager behavior
# ---------------------------------------------------------------------------

def test_broadcast_never_leaks_across_organizations():
    m = ConnectionManager()
    ws_a, ws_b = FakeWebSocket("a"), FakeWebSocket("b")
    org_a, org_b = uuid4(), uuid4()
    _connect(m, ws_a, org_a)
    _connect(m, ws_b, org_b)

    asyncio.run(m.broadcast_to_org(org_a, {"type": "workflow.updated", "n": 1}))
    asyncio.run(m.broadcast_to_org(org_b, {"type": "job.updated", "n": 2}))

    # Each org only ever sees its own events
    assert [msg["type"] for msg in ws_a.messages] == ["workflow.updated"]
    assert [msg["type"] for msg in ws_b.messages] == ["job.updated"]


def test_broadcast_delivers_exactly_once_per_socket():
    m = ConnectionManager()
    org = uuid4()
    sockets = [FakeWebSocket(f"s{i}") for i in range(3)]
    for s in sockets:
        _connect(m, s, org)

    asyncio.run(m.broadcast_to_org(org, {"type": "notification.created", "seq": 1}))
    asyncio.run(m.broadcast_to_org(org, {"type": "task.updated", "seq": 2}))

    for s in sockets:
        assert len(s.messages) == 2, f"{s.name} got {len(s.messages)} messages"
        assert [msg["seq"] for msg in s.messages] == [1, 2]


def test_personal_message_targets_only_the_recipient():
    m = ConnectionManager()
    org = uuid4()
    user_one, user_two = uuid4(), uuid4()
    ws_one, ws_two = FakeWebSocket("one"), FakeWebSocket("two")
    _connect(m, ws_one, org, user_one)
    _connect(m, ws_two, org, user_two)

    asyncio.run(m.send_personal_message({"type": "DIRECT"}, user_two))

    assert ws_one.messages == []
    assert ws_two.messages == [{"type": "DIRECT"}]


def test_disconnect_removes_socket_from_broadcasts():
    m = ConnectionManager()
    org = uuid4()
    user_one = uuid4()
    ws_one, ws_two = FakeWebSocket("one"), FakeWebSocket("two")
    _connect(m, ws_one, org, user_one)
    _connect(m, ws_two, org)

    m.disconnect(ws_one, org, user_one)
    asyncio.run(m.broadcast_to_org(org, {"type": "deployment.updated"}))

    assert ws_one.messages == []
    assert len(ws_two.messages) == 1
    assert ws_one not in m.active_connections.get(org, [])
    assert user_one not in m.user_connections


def test_unknown_org_broadcast_is_a_safe_noop():
    m = ConnectionManager()
    # Never raised: broadcasting to an org with no sockets must not explode
    asyncio.run(m.broadcast_to_org(uuid4(), {"type": "workflow.updated"}))


# ---------------------------------------------------------------------------
# workflow.* event helper (used by publish/execute/archive endpoints)
# ---------------------------------------------------------------------------

def test_workflow_event_helper_reaches_only_target_org():
    org_a, org_b = uuid4(), uuid4()
    ws_a, ws_b = FakeWebSocket("a"), FakeWebSocket("b")
    manager.active_connections[org_a] = [ws_a]
    manager.active_connections[org_b] = [ws_b]
    try:
        broadcast_workflow_event(org_a, "workflow.published", {"workflow_id": "wf-1"})
    finally:
        manager.active_connections.pop(org_a, None)
        manager.active_connections.pop(org_b, None)

    assert len(ws_a.messages) == 1
    assert ws_a.messages[0]["type"] == "workflow.published"
    assert ws_a.messages[0]["payload"] == {"workflow_id": "wf-1"}
    assert ws_b.messages == []


def test_workflow_event_helper_never_raises():
    # No sockets registered: helper must swallow errors, not break the request
    broadcast_workflow_event(uuid4(), "workflow.execution.failed", {"x": 1})


# ---------------------------------------------------------------------------
# Endpoint integration: auth, membership, presence
# ---------------------------------------------------------------------------

def _register(client: TestClient, email: str):
    client.post("/api/v1/auth/register",
                json={"name": email.split("@")[0], "email": email, "password": "password123"})
    token = client.post("/api/v1/auth/login",
                        json={"email": email, "password": "password123"}).json()["access_token"]
    auth = {"Authorization": f"Bearer {token}"}
    org = client.post("/api/v1/organizations", json={"name": f"Org {email}"}, headers=auth).json()
    return token, org["id"]


def test_ws_connect_and_presence_broadcast(client: TestClient):
    """The /api/v1/ws endpoint broadcasts presence to the connecting org."""
    token, org_id = _register(client, "ws-presence@example.com")
    with client.websocket_connect(f"/api/v1/ws?token={token}&org_id={org_id}") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "USER_PRESENCE_CHANGED"
        assert msg["status"] == "ONLINE"
        assert msg["user_id"]


def test_ws_rejects_invalid_token(client: TestClient):
    _token, org_id = _register(client, "ws-badtoken@example.com")
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(
            f"/api/v1/realtime/ws?token=not-a-real-token&org_id={org_id}"
        ) as ws:
            ws.receive_json()
    assert exc.value.code == 1008


def test_ws_rejects_non_member_organization(client: TestClient):
    token_a, _org_a = _register(client, "ws-mem-a@example.com")
    _token_b, org_b = _register(client, "ws-mem-b@example.com")

    # A is not a member of org B — connection must be refused
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(
            f"/api/v1/realtime/ws?token={token_a}&org_id={org_b}"
        ) as ws:
            ws.receive_json()
    assert exc.value.code == 1008


def test_ws_organization_isolation_end_to_end(client: TestClient, db):
    """Sockets joined to ORG-A never receive ORG-B presence events, and vice versa.

    Uses the server-loop presence broadcasts of /api/v1/ws: each socket must
    observe EXACTLY its own organization's connect/disconnect sequence.
    """
    from app.models.organization import OrganizationMember, OrganizationRole
    from app.models.user import User
    from uuid import UUID

    token_a, org_a = _register(client, "ws-iso-a@example.com")
    token_b, org_b = _register(client, "ws-iso-b@example.com")

    # Second member for each org (registered via API, membership via db)
    token_c = _register(client, "ws-iso-c@example.com")[0]
    token_d = _register(client, "ws-iso-d@example.com")[0]
    user_c = db.query(User).filter(User.email == "ws-iso-c@example.com").first()
    user_d = db.query(User).filter(User.email == "ws-iso-d@example.com").first()
    db.add(OrganizationMember(organization_id=UUID(str(org_a)), user_id=user_c.id, role=OrganizationRole.MEMBER))
    db.add(OrganizationMember(organization_id=UUID(str(org_b)), user_id=user_d.id, role=OrganizationRole.MEMBER))
    db.commit()

    with client.websocket_connect(f"/api/v1/ws?token={token_a}&org_id={org_a}") as ws_a:
        # 1. A connects -> own ONLINE (ORG-A)
        a1 = ws_a.receive_json()
        assert a1["status"] == "ONLINE" and a1["user_id"]

        with client.websocket_connect(f"/api/v1/ws?token={token_b}&org_id={org_b}") as ws_b:
            # 2. B connects -> own ONLINE (ORG-B). If presence events leaked
            #    across orgs, A's next read would see ONLINE(B) here.
            b1 = ws_b.receive_json()
            assert b1["status"] == "ONLINE"

            with client.websocket_connect(f"/api/v1/ws?token={token_c}&org_id={org_a}") as ws_c:
                # 3. C joins ORG-A: C sees own presence, A sees presence(C)
                c1 = ws_c.receive_json()
                assert c1["status"] == "ONLINE"
                a2 = ws_a.receive_json()
                assert a2["status"] == "ONLINE"
                assert a2["user_id"] == str(user_c.id)

                with client.websocket_connect(f"/api/v1/ws?token={token_d}&org_id={org_b}") as ws_d:
                    # 4. D joins ORG-B: D sees own presence, B sees presence(D)
                    d1 = ws_d.receive_json()
                    assert d1["status"] == "ONLINE"
                    b2 = ws_b.receive_json()
                    assert b2["status"] == "ONLINE"
                    assert b2["user_id"] == str(user_d.id)
                # ws_d exits -> OFFLINE(D) broadcast to ORG-B only
            # ws_c exits -> OFFLINE(C) broadcast to ORG-A only

            # 5. A must now see OFFLINE(C) — and never any ORG-B event
            a3 = ws_a.receive_json()
            assert a3["status"] == "OFFLINE"
            assert a3["user_id"] == str(user_c.id)

            # 6. B must see OFFLINE(D) (queued before any possible leak of
            #    OFFLINE(C), which happened afterwards)
            b3 = ws_b.receive_json()
            assert b3["status"] == "OFFLINE"
            assert b3["user_id"] == str(user_d.id)

            # 7. D rejoins -> B's next message must be ONLINE(D); if ORG-A
            #    traffic had leaked onto B it would surface here first.
            with client.websocket_connect(f"/api/v1/ws?token={token_d}&org_id={org_b}") as ws_d2:
                ws_d2.receive_json()
                b4 = ws_b.receive_json()
                assert b4["status"] == "ONLINE"
                assert b4["user_id"] == str(user_d.id)
        # ws_b exits

        # 8. C rejoins -> A's next message must be ONLINE(C); if any ORG-B
        #    event had leaked into A it would appear here first. Guaranteed
        #    to arrive, so this read can never hang.
        with client.websocket_connect(f"/api/v1/ws?token={token_c}&org_id={org_a}") as ws_c2:
            ws_c2.receive_json()
            a4 = ws_a.receive_json()
            assert a4["status"] == "ONLINE"
            assert a4["user_id"] == str(user_c.id)
