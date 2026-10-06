from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Any, List
from sqlalchemy.orm import Session
from uuid import UUID

from app.api import deps
from app.api.v1.reports import check_permission
from app.models.user import User
from app.services.search_service import global_search

router = APIRouter()

@router.get("")
def search_global(
    q: str = Query(default="", max_length=200),
    limit: int = Query(default=25, ge=1, le=50),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    """Org-scoped, permission-aware global search (Phase 43).

    One authoritative search endpoint: bounded, deterministic, parameterized.
    Empty queries return an empty list; visibility rules (private knowledge
    spaces, user-owned notifications) are enforced server-side in
    `search_service.global_search`.
    """
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header missing")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "search.view")
    return global_search(db, org_id, current_user.id, q, limit=limit)
