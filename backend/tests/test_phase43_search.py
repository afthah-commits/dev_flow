"""Phase 43 — Global search & command center.

Covers the authoritative GET /api/v1/search endpoint:
- auth (401), org context, non-member (403), org isolation (no cross-tenant)
- deterministic ranking (exact > prefix > contains)
- multiple entity types, empty query, special characters, result limit
- restricted visibility (private knowledge spaces hidden)
- no-result response
"""
import pytest
from uuid import uuid4

from app.models.user import User
from app.models.organization import Organization, OrganizationMember, OrganizationRole
from app.models.project import Project
from app.models.task import Task
from app.models.client import Client
from app.models.knowledge import (
    KnowledgeSpace, KnowledgeDocument, SpaceVisibility, DocumentStatus,
)
from app.models.workflow import Workflow

URL = "/api/v1/search"


def _register(client, email):
    client.post("/api/v1/auth/register", json={"name": "P43 User", "email": email, "password": "password123"})
    tok = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def _org_with_user(db, client, email):
    headers = _register(client, email)
    user = db.query(User).filter(User.email == email).first()
    org = Organization(id=uuid4(), name=f"Org {uuid4().hex[:6]}",
                       slug=f"p43-{uuid4().hex[:8]}", created_by=user.id)
    db.add(org)
    db.flush()
    db.add(OrganizationMember(id=uuid4(), organization_id=org.id, user_id=user.id,
                              role=OrganizationRole.OWNER))
    db.commit()
    return headers, user, org


def _project(db, org, name):
    p = Project(id=uuid4(), name=name, organization_id=org.id,
                slug=f"p43-p-{uuid4().hex[:8]}", owner_id=org.created_by)
    db.add(p)
    db.commit()
    return p


def _search(client, headers, org, q, limit=None):
    params = {"q": q}
    if limit is not None:
        params["limit"] = limit
    return client.get(URL, headers={**headers, "X-Organization-Id": str(org.id)},
                      params=params)


# ---------------------------------------------------------------------------
# Auth / org context / RBAC
# ---------------------------------------------------------------------------

def test_search_requires_authentication(client):
    assert client.get(URL, params={"q": "x"}).status_code == 401


def test_search_requires_org_header(client):
    headers = _register(client, "p43-noorg@example.com")
    res = client.get(URL, headers=headers, params={"q": "x"})
    assert res.status_code in (400, 403)


def test_search_rejects_non_member(client, db):
    headers = _register(client, "p43-foreign@example.com")
    _, _, org = _org_with_user(db, client, "p43-owner1@example.com")
    res = client.get(URL, headers={**headers, "X-Organization-Id": str(org.id)},
                     params={"q": "x"})
    assert res.status_code == 403


# ---------------------------------------------------------------------------
# Matching & ranking
# ---------------------------------------------------------------------------

def _seed_fixture_org(db, client):
    headers, user, org = _org_with_user(db, client, "p43-main@example.com")
    _project(db, org, "Apollo")
    _project(db, org, "Apollo Redesign")
    _project(db, org, "Project Apollo Rising")
    return headers, org


def test_exact_match_ranks_first(client, db):
    headers, org = _seed_fixture_org(db, client)
    res = _search(client, headers, org, "apollo")
    assert res.status_code == 200
    results = res.json()
    assert results[0]["title"] == "Apollo"
    assert results[0]["score"] == 3.0


def test_prefix_before_contains(client, db):
    headers, org = _seed_fixture_org(db, client)
    results = _search(client, headers, org, "apollo").json()
    titles = [r["title"] for r in results]
    assert titles.index("Apollo Redesign") < titles.index("Project Apollo Rising")
    by_title = {r["title"]: r["score"] for r in results}
    assert by_title["Apollo Redesign"] == 2.0
    assert by_title["Project Apollo Rising"] == 1.0


def test_multiple_entity_types_returned(client, db):
    headers, user, org = _org_with_user(db, client, "p43-multi@example.com")
    p = _project(db, org, "Nebula")
    db.add(Task(id=uuid4(), project_id=p.id, title="Nebula migration",
                creator_id=user.id))
    db.add(Workflow(id=uuid4(), organization_id=org.id, name="Nebula flow"))
    db.add(Client(id=uuid4(), organization_id=org.id, name="Nebula Corp"))
    db.commit()

    results = _search(client, headers, org, "nebula").json()
    types = {r["entity_type"] for r in results}
    assert {"PROJECT", "TASK", "WORKFLOW", "CLIENT"} <= types


def test_members_searchable(client, db):
    headers, user, org = _org_with_user(db, client, "p43-zara@example.com")
    results = _search(client, headers, org, "p43-zara").json()
    assert any(r["entity_type"] == "MEMBER" for r in results)


# ---------------------------------------------------------------------------
# Safety / limits
# ---------------------------------------------------------------------------

def test_empty_query_returns_empty_list(client, db):
    headers, _, org = _org_with_user(db, client, "p43-empty@example.com")
    _project(db, org, "Anything")
    res = _search(client, headers, org, "")
    assert res.status_code == 200
    assert res.json() == []
    res = _search(client, headers, org, "   ")
    assert res.json() == []


def test_special_characters_safe_and_literal(client, db):
    headers, _, org = _org_with_user(db, client, "p43-special@example.com")
    _project(db, org, "Alpha Project")
    for q in ["%", "_", "\\", "'; DROP TABLE projects;--", "%百分"]:
        res = _search(client, headers, org, q)
        assert res.status_code == 200
        # Wildcards are treated literally: "%" must not match everything.
        if q in ("%", "_"):
            assert res.json() == []


def test_result_limit_bounded(client, db):
    headers, _, org = _org_with_user(db, client, "p43-limit@example.com")
    for i in range(10):
        _project(db, org, f"Limit Test {i}")
    results = _search(client, headers, org, "limit", limit=4).json()
    assert len(results) == 4
    # API caps limit at 50
    res = client.get(URL, headers={**headers, "X-Organization-Id": str(org.id)},
                     params={"q": "limit", "limit": 500})
    assert res.status_code == 422


def test_no_results_returns_empty_list(client, db):
    headers, _, org = _org_with_user(db, client, "p43-nores@example.com")
    res = _search(client, headers, org, "zzz-nothing-matches-zzz")
    assert res.status_code == 200
    assert res.json() == []


# ---------------------------------------------------------------------------
# Visibility & isolation
# ---------------------------------------------------------------------------

def test_private_knowledge_space_docs_hidden(client, db):
    headers, user, org = _org_with_user(db, client, "p43-privdoc@example.com")
    private_space = KnowledgeSpace(id=uuid4(), organization_id=org.id,
                                   name=f"priv-{uuid4().hex[:6]}",
                                   slug=f"priv-{uuid4().hex[:6]}",
                                   visibility=SpaceVisibility.PRIVATE)
    open_space = KnowledgeSpace(id=uuid4(), organization_id=org.id,
                                name=f"open-{uuid4().hex[:6]}",
                                slug=f"open-{uuid4().hex[:6]}",
                                visibility=SpaceVisibility.ORGANIZATION)
    db.add_all([private_space, open_space])
    db.flush()
    db.add(KnowledgeDocument(
        id=uuid4(), organization_id=org.id, space_id=private_space.id,
        title="Secret Handshake Guide", slug=f"secret-{uuid4().hex[:6]}",
        status=DocumentStatus.PUBLISHED, content="hidden"))
    db.add(KnowledgeDocument(
        id=uuid4(), organization_id=org.id, space_id=open_space.id,
        title="Public Handshake Guide", slug=f"public-{uuid4().hex[:6]}",
        status=DocumentStatus.PUBLISHED, content="visible"))
    db.commit()

    results = _search(client, headers, org, "handshake").json()
    titles = [r["title"] for r in results]
    assert "Public Handshake Guide" in titles
    assert "Secret Handshake Guide" not in titles


def test_no_cross_tenant_leakage(client, db):
    headers_a = _register(client, "p43-leak-a@example.com")
    user_a = db.query(User).filter(User.email == "p43-leak-a@example.com").first()
    org_a = Organization(id=uuid4(), name=f"Org {uuid4().hex[:6]}",
                         slug=f"p43-a-{uuid4().hex[:8]}", created_by=user_a.id)
    db.add(org_a)
    db.flush()
    db.add(OrganizationMember(id=uuid4(), organization_id=org_a.id,
                              user_id=user_a.id, role=OrganizationRole.OWNER))
    _project(db, org_a, "Confidential Fusion Reactor")
    db.commit()

    headers_b, _, org_b = _org_with_user(db, client, "p43-leak-b@example.com")
    results = _search(client, headers_b, org_b, "fusion").json()
    assert results == []
    # Owner still sees it
    results_a = _search(client, headers_a, org_a, "fusion").json()
    assert any(r["title"] == "Confidential Fusion Reactor" for r in results_a)


def test_result_item_shape(client, db):
    headers, _, org = _org_with_user(db, client, "p43-shape@example.com")
    _project(db, org, "Shape Check")
    results = _search(client, headers, org, "shape").json()
    assert results, "expected at least one result"
    item = results[0]
    assert set(item.keys()) == {
        "entity_type", "entity_id", "title", "snippet", "url", "score",
        "matched_field",
    }
    assert item["url"].startswith("/")
