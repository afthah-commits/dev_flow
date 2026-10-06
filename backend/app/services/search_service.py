"""Centralized org-scoped global search (Phase 43).

Deterministic ranking, permission-aware visibility, parameterized ORM queries
only. Candidate rows are fetched per category with LIMIT clauses (bounded),
then ranked in Python — portable across SQLite and PostgreSQL, no external
search infrastructure.

Ranking (per spec): exact title/name match > starts-with match > contains
match. Deterministic: ties broken by (rank, entity_type, title).

Visibility:
- Documents in PRIVATE spaces are excluded (space-level restricted entity);
  all other space visibilities are org-wide in the existing application.
- Notifications are strictly user-scoped (private to their owner).
- Everything else is org-scoped and visible to all org members, matching the
  existing list endpoints for those entities.
"""
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.task import Task
from app.models.client import Client
from app.models.knowledge import KnowledgeDocument, KnowledgeSpace, SpaceVisibility
from app.models.workflow import Workflow
from app.models.organization import OrganizationMember
from app.models.user import User
from app.models.collaboration import Discussion
from app.models.notification import Notification

# Category fetch limits (bounded before ranking; final result count is
# further bounded by `limit` after ranking).
_PER_CATEGORY_LIMIT = 20

# Deterministic ranking scores.
RANK_EXACT = 3.0
RANK_PREFIX = 2.0
RANK_CONTAINS = 1.0

_PRIVATE_SPACE_IDS_CACHE: Dict[UUID, set] = {}


def _rank(text: str, term: str) -> float:
    """Deterministic rank for a title/name against the lowercase term.

    3.0 exact match, 2.0 starts-with, 1.0 contains, 0.0 no match.
    """
    if text == term:
        return RANK_EXACT
    if text.startswith(term):
        return RANK_PREFIX
    if term in text:
        return RANK_CONTAINS
    return 0.0


def _private_space_ids(db: Session, org_id: UUID) -> set:
    ids = _PRIVATE_SPACE_IDS_CACHE.get(org_id)
    if ids is None:
        rows = db.query(KnowledgeSpace.id).filter(
            KnowledgeSpace.organization_id == org_id,
            KnowledgeSpace.visibility == SpaceVisibility.PRIVATE,
        ).all()
        ids = {r[0] for r in rows}
        # Small bounded memo; org space sets change rarely within a request.
        if len(_PRIVATE_SPACE_IDS_CACHE) > 64:
            _PRIVATE_SPACE_IDS_CACHE.clear()
        _PRIVATE_SPACE_IDS_CACHE[org_id] = ids
    return ids


def _match_text(term: str, *texts: str) -> float:
    """Best rank across the given texts (0.0 when nothing matches)."""
    best = 0.0
    for t in texts:
        if t:
            best = max(best, _rank(t.lower(), term))
    return best


def _item(entity_type: str, entity_id, title: str, snippet: str,
          url: str, score: float, matched_field: str) -> Dict[str, Any]:
    return {
        "entity_type": entity_type,
        "entity_id": str(entity_id),
        "title": title,
        "snippet": snippet[:120] if snippet else "",
        "url": url,
        "score": score,
        "matched_field": matched_field,
    }


def global_search(db: Session, org_id: UUID, user_id: UUID, term: str,
                  limit: int = 25) -> List[Dict[str, Any]]:
    """Search the organization's projects, tasks, clients, documents,
    workflows, members, discussions and the calling user's notifications.

    Returns a ranked list (exact > prefix > contains; ties broken
    deterministically), bounded to `limit` items.
    """
    term = (term or "").strip().lower()
    if not term or len(term) > 200:
        return []

    # Guard LIKE wildcards: the term is used in ilike() contains clauses for
    # candidate fetching; escape user-supplied % and _ so queries stay safe.
    like_term = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    contains = f"%{like_term}%"

    candidates: List[Dict[str, Any]] = []

    # --- Projects ---------------------------------------------------------
    projects = db.query(Project).filter(
        Project.organization_id == org_id,
        Project.name.ilike(contains, escape="\\"),
    ).limit(_PER_CATEGORY_LIMIT).all()
    for p in projects:
        score = _match_text(term, p.name)
        if score:
            candidates.append(_item(
                "PROJECT", p.id, p.name, (p.description or ""), f"/projects/{p.id}",
                score, "name"))

    # --- Tasks (org-scoped via Project join) ------------------------------
    tasks = db.query(Task).join(Project, Task.project_id == Project.id).filter(
        Project.organization_id == org_id,
        Task.title.ilike(contains, escape="\\"),
    ).limit(_PER_CATEGORY_LIMIT).all()
    for t in tasks:
        score = _match_text(term, t.title)
        if score:
            candidates.append(_item(
                "TASK", t.id, t.title, (t.description or ""),
                f"/projects/{t.project_id}/tasks/{t.id}", score, "title"))

    # --- Clients (accounts; CRM contacts live on the client record) -------
    clients = db.query(Client).filter(
        Client.organization_id == org_id,
        or_(
            Client.name.ilike(contains, escape="\\"),
            Client.company_name.ilike(contains, escape="\\"),
        ),
    ).limit(_PER_CATEGORY_LIMIT).all()
    for c in clients:
        score = max(_match_text(term, c.name), _match_text(term, c.company_name or ""))
        if score:
            candidates.append(_item(
                "CLIENT", c.id, c.name, (c.company_name or ""), f"/clients",
                score, "name/company"))

    # --- Knowledge documents (exclude PRIVATE spaces) ---------------------
    private_ids = _private_space_ids(db, org_id)
    doc_query = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.organization_id == org_id,
        KnowledgeDocument.title.ilike(contains, escape="\\"),
    )
    if private_ids:
        doc_query = doc_query.filter(~KnowledgeDocument.space_id.in_(private_ids))
    docs = doc_query.limit(_PER_CATEGORY_LIMIT).all()
    for d in docs:
        score = _match_text(term, d.title)
        if score:
            candidates.append(_item(
                "DOCUMENT", d.id, d.title, (d.content or "")[:120],
                f"/knowledge/documents/{d.id}", score, "title"))

    # --- Workflows ----------------------------------------------------------
    workflows = db.query(Workflow).filter(
        Workflow.organization_id == org_id,
        Workflow.name.ilike(contains, escape="\\"),
    ).limit(_PER_CATEGORY_LIMIT).all()
    for w in workflows:
        score = _match_text(term, w.name)
        if score:
            candidates.append(_item(
                "WORKFLOW", w.id, w.name, (w.description or ""),
                f"/workflows/{w.id}/studio", score, "name"))

    # --- Members (users of this org) ---------------------------------------
    members = db.query(OrganizationMember, User).join(
        User, OrganizationMember.user_id == User.id
    ).filter(
        OrganizationMember.organization_id == org_id,
        or_(
            User.name.ilike(contains, escape="\\"),
            User.email.ilike(contains, escape="\\"),
        ),
    ).limit(_PER_CATEGORY_LIMIT).all()
    for member, user in members:
        score = max(_match_text(term, user.name), _match_text(term, user.email or ""))
        if score:
            candidates.append(_item(
                "MEMBER", user.id, user.name, user.email or "",
                f"/settings/team", score, "name/email"))

    # --- Discussions --------------------------------------------------------
    discussions = db.query(Discussion).filter(
        Discussion.organization_id == org_id,
        Discussion.title.ilike(contains, escape="\\"),
    ).limit(_PER_CATEGORY_LIMIT).all()
    for d in discussions:
        score = _match_text(term, d.title)
        if score:
            candidates.append(_item(
                "DISCUSSION", d.id, d.title, (d.content or "")[:120],
                f"/projects/{d.project_id}/discussions/{d.id}", score, "title"))

    # --- Notifications (strictly the calling user's) ------------------------
    notifications = db.query(Notification).filter(
        Notification.user_id == user_id,
        or_(
            Notification.organization_id == org_id,
            Notification.organization_id.is_(None),
        ),
        or_(
            Notification.title.ilike(contains, escape="\\"),
            Notification.message.ilike(contains, escape="\\"),
        ),
    ).order_by(Notification.created_at.desc()).limit(_PER_CATEGORY_LIMIT).all()
    for n in notifications:
        score = max(_match_text(term, n.title), _match_text(term, n.message or ""))
        if score:
            candidates.append(_item(
                "NOTIFICATION", n.id, n.title, (n.message or ""),
                "/notifications", score, "title/message"))

    # Deterministic ordering: rank desc, then entity_type, then title.
    candidates.sort(key=lambda r: (-r["score"], r["entity_type"], r["title"]))
    return candidates[:limit]
